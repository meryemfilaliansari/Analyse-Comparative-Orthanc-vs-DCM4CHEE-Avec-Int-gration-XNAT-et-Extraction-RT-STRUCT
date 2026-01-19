import asyncio
import httpx
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time
from database import SessionLocal
from models import Patient, Study, Comparison, SyncLog
from uuid import uuid4

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, dcm4chee_url: str, orthanc_url: str, xnat_url: str, sync_interval: int = 60):
        self.dcm4chee_url = dcm4chee_url
        self.orthanc_url = orthanc_url
        self.xnat_url = xnat_url
        self.sync_interval = sync_interval
        self.client = None
    
    async def start_sync_loop(self):
        """Boucle de synchronisation continue"""
        logger.info("Démarrage de la boucle de synchronisation")
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                await self.sync_patients()
                await self.generate_comparisons()
                logger.info("Synchronisation complétée avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la synchronisation: {e}")
    
    async def sync_patients(self) -> int:
        """Synchroniser les patients entre les PACS"""
        db = SessionLocal()
        synced_count = 0
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Récupérer les patients de DCM4CHEE
                dcm4chee_patients = await self._fetch_dcm4chee_patients(client)
                logger.info(f"Trouvé {len(dcm4chee_patients)} patients dans DCM4CHEE")
                
                # Récupérer les patients d'Orthanc
                orthanc_patients = await self._fetch_orthanc_patients(client)
                logger.info(f"Trouvé {len(orthanc_patients)} patients dans Orthanc")
                
                # Fusionner et synchroniser
                for patient_data in dcm4chee_patients:
                    existing_patient = db.query(Patient).filter(
                        Patient.patient_id == patient_data.get('patient_id')
                    ).first()
                    
                    if not existing_patient:
                        patient = Patient(
                            id=str(uuid4()),
                            name=patient_data.get('name'),
                            birth_date=patient_data.get('birth_date'),
                            sex=patient_data.get('sex'),
                            patient_id=patient_data.get('patient_id'),
                            dcm4chee_id=patient_data.get('id'),
                            synchronized=False
                        )
                        db.add(patient)
                        synced_count += 1
                    else:
                        existing_patient.dcm4chee_id = patient_data.get('id')
                        existing_patient.updated_at = datetime.utcnow()
                
                # Vérifier correspondance Orthanc
                for patient_data in orthanc_patients:
                    existing_patient = db.query(Patient).filter(
                        Patient.patient_id == patient_data.get('patient_id')
                    ).first()
                    
                    if existing_patient:
                        existing_patient.orthanc_id = patient_data.get('id')
                        existing_patient.synchronized = True
                
                db.commit()
                
                # Log de synchronisation
                db_log = SyncLog(
                    service='patients',
                    action='sync',
                    status='success',
                    message=f'Synced {synced_count} patients',
                    details={
                        'dcm4chee_count': len(dcm4chee_patients),
                        'orthanc_count': len(orthanc_patients)
                    }
                )
                db.add(db_log)
                db.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des patients: {e}")
            db_log = SyncLog(
                service='patients',
                action='sync',
                status='error',
                message=str(e)
            )
            db.add(db_log)
            db.commit()
        finally:
            db.close()
        
        return synced_count
    
    async def generate_comparisons(self) -> int:
        """Générer les comparaisons entre les PACS"""
        db = SessionLocal()
        comparison_count = 0
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                studies = db.query(Study).all()
                
                for study in studies:
                    # Vérifier si une comparaison existe déjà
                    existing = db.query(Comparison).filter(Comparison.study_id == study.id).first()
                    
                    if not existing or existing.sync_status == "pending":
                        comparison_data = await self._compare_study(client, study)
                        
                        if not existing:
                            comparison = Comparison(
                                id=str(uuid4()),
                                study_id=study.id,
                                **comparison_data
                            )
                            db.add(comparison)
                        else:
                            for key, value in comparison_data.items():
                                setattr(existing, key, value)
                        
                        comparison_count += 1
                
                db.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération des comparaisons: {e}")
        finally:
            db.close()
        
        return comparison_count
    
    async def anonymize_study(self, study_id: str) -> str:
        """Router une étude vers XNAT pour anonymisation"""
        db = SessionLocal()
        
        try:
            study = db.query(Study).filter(Study.id == study_id).first()
            if not study:
                raise ValueError(f"Study {study_id} not found")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Récupérer l'étude depuis DCM4CHEE
                study_data = await self._fetch_study_from_dcm4chee(client, study.dcm4chee_id)
                
                # Envoyer vers XNAT pour anonymisation
                response = await client.post(
                    f"{self.xnat_url}/xapi/import",
                    json=study_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code not in [200, 201]:
                    raise ValueError(f"XNAT import failed: {response.text}")
                
                anonymized_id = response.json().get('id')
                
                # Log
                db_log = SyncLog(
                    service='xnat',
                    action='anonymize',
                    status='success',
                    message=f'Study {study_id} anonymized as {anonymized_id}'
                )
                db.add(db_log)
                db.commit()
                
                return anonymized_id
        
        except Exception as e:
            logger.error(f"Erreur lors de l'anonymisation: {e}")
            db_log = SyncLog(
                service='xnat',
                action='anonymize',
                status='error',
                message=str(e)
            )
            db.add(db_log)
            db.commit()
            raise
        finally:
            db.close()
    
    # Méthodes privées
    
    async def _fetch_dcm4chee_patients(self, client: httpx.AsyncClient) -> List[Dict]:
        """Récupérer les patients de DCM4CHEE"""
        try:
            response = await client.get(f"{self.dcm4chee_url}/dcm4chee-arc/aets/DCM4CHEE/rs/patients")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Erreur DCM4CHEE patients: {e}")
            return []
    
    async def _fetch_orthanc_patients(self, client: httpx.AsyncClient) -> List[Dict]:
        """Récupérer les patients d'Orthanc"""
        try:
            response = await client.get(f"{self.orthanc_url}/patients")
            if response.status_code == 200:
                patients = response.json()
                # Formater les réponses Orthanc
                formatted = []
                for patient_id in patients:
                    patient_data = await client.get(f"{self.orthanc_url}/patients/{patient_id}")
                    if patient_data.status_code == 200:
                        formatted.append({
                            'id': patient_id,
                            'patient_id': patient_data.json().get('PatientID'),
                            'name': patient_data.json().get('PatientName'),
                            'birth_date': patient_data.json().get('PatientBirthDate'),
                            'sex': patient_data.json().get('PatientSex')
                        })
                return formatted
            return []
        except Exception as e:
            logger.error(f"Erreur Orthanc patients: {e}")
            return []
    
    async def _compare_study(self, client: httpx.AsyncClient, study: Study) -> Dict:
        """Comparer une étude entre les deux PACS"""
        comparison_data = {
            'dcm4chee_images': 0,
            'orthanc_images': 0,
            'dcm4chee_response_time': 0.0,
            'orthanc_response_time': 0.0,
            'dcm4chee_success': False,
            'orthanc_success': False,
            'differences': {}
        }
        
        try:
            # Interroger DCM4CHEE
            if study.dcm4chee_id:
                start = time.time()
                response = await client.get(
                    f"{self.dcm4chee_url}/dcm4chee-arc/aets/DCM4CHEE/rs/studies/{study.study_uid}/series"
                )
                response_time = time.time() - start
                if response.status_code == 200:
                    series_list = response.json()
                    image_count = sum(len(s.get('Instances', [])) for s in series_list)
                    comparison_data['dcm4chee_images'] = image_count
                    comparison_data['dcm4chee_response_time'] = response_time
                    comparison_data['dcm4chee_success'] = True
                    # RTSTRUCT support (dcm4chee)
                    rtstruct_dcm4chee = any(s.get('Modality') == 'RTSTRUCT' for s in series_list)
                else:
                    rtstruct_dcm4chee = False
            else:
                rtstruct_dcm4chee = False

            # Interroger Orthanc
            if study.orthanc_id:
                start = time.time()
                response = await client.get(
                    f"{self.orthanc_url}/studies/{study.orthanc_id}/series"
                )
                response_time = time.time() - start
                if response.status_code == 200:
                    series_list = response.json()
                    image_count = 0
                    rtstruct_orthanc = False
                    for series_id in series_list:
                        series_data = await client.get(f"{self.orthanc_url}/series/{series_id}")
                        if series_data.status_code == 200:
                            series_json = series_data.json()
                            image_count += len(series_json.get('Instances', []))
                            if series_json.get('MainDicomTags', {}).get('Modality') == 'RTSTRUCT':
                                rtstruct_orthanc = True
                    comparison_data['orthanc_images'] = image_count
                    comparison_data['orthanc_response_time'] = response_time
                    comparison_data['orthanc_success'] = True
                else:
                    rtstruct_orthanc = False
            else:
                rtstruct_orthanc = False

            # Plugins installés (Orthanc)
            orthanc_plugins = []
            try:
                resp = await client.get(f"{self.orthanc_url}/plugins")
                if resp.status_code == 200:
                    orthanc_plugins = resp.json()
            except Exception:
                pass

            # Plugins installés (dcm4chee) - statique ou à améliorer
            dcm4chee_plugins = ['dcm4chee-arc', 'dcm4chee-webui']

            # Support anonymisation (présumé True pour les deux)
            anonymization = {'dcm4chee': True, 'orthanc': True}

            # Sécurité (présumé True si auth activée)
            security = {'dcm4chee': True, 'orthanc': True}

            # Compression (statique, à améliorer si besoin)
            compression = {'dcm4chee': 'JPEG Lossless', 'orthanc': 'JPEG Lossless'}

            # Identifier les différences
            if comparison_data['dcm4chee_images'] != comparison_data['orthanc_images']:
                comparison_data['differences']['image_count_diff'] = (
                    comparison_data['dcm4chee_images'] - comparison_data['orthanc_images']
                )

            # Ajout des nouveaux critères
            comparison_data['differences']['anonymization'] = anonymization
            comparison_data['differences']['plugins'] = {
                'dcm4chee': dcm4chee_plugins,
                'orthanc': orthanc_plugins
            }
            comparison_data['differences']['rtstruct'] = {
                'dcm4chee': rtstruct_dcm4chee,
                'orthanc': rtstruct_orthanc
            }
            comparison_data['differences']['security'] = security
            comparison_data['differences']['compression'] = compression

            comparison_data['sync_status'] = 'completed'

        except Exception as e:
            logger.error(f"Erreur lors de la comparaison: {e}")
            comparison_data['sync_status'] = 'error'

        return comparison_data
    
    async def _fetch_study_from_dcm4chee(self, client: httpx.AsyncClient, study_id: str) -> Dict:
        """Récupérer les données d'une étude de DCM4CHEE"""
        response = await client.get(f"{self.dcm4chee_url}/dcm4chee-arc/aets/DCM4CHEE/rs/studies/{study_id}")
        if response.status_code == 200:
            return response.json()
        return {}
