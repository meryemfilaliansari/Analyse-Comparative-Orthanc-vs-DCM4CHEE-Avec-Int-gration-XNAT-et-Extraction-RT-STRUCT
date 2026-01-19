#!/usr/bin/env python3
"""
Création d'un fichier DICOM strictement conforme pour dcm4chee 5.31.2
Inclut tous les attributs requis et recommandés
"""

import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid, CTImageStorage
from datetime import datetime
import numpy as np
import os

def create_compliant_dicom(output_filename="compliant_test.dcm"):
    """
    Crée un fichier DICOM avec tous les attributs requis par dcm4chee
    """
    
    print(f"Création d'un DICOM strictement conforme : {output_filename}")
    
    # Métadonnées du fichier
    file_meta = Dataset()
    file_meta.FileMetaInformationGroupLength = 200
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = CTImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()
    file_meta.ImplementationVersionName = "PYDICOM_TEST"
    
    # Dataset principal
    ds = FileDataset(
        output_filename,
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128
    )
    
    # ===== PATIENT MODULE (Requis) =====
    ds.PatientName = "TEST^DICOM^COMPLIANT"
    ds.PatientID = "TEST001"
    ds.PatientBirthDate = "19800101"
    ds.PatientSex = "M"
    
    # ===== STUDY MODULE (Requis) =====
    current_datetime = datetime.now()
    ds.StudyDate = current_datetime.strftime("%Y%m%d")
    ds.StudyTime = current_datetime.strftime("%H%M%S")
    ds.StudyInstanceUID = generate_uid()
    ds.StudyID = "1"
    ds.AccessionNumber = ""  # Peut être vide mais doit exister
    ds.ReferringPhysicianName = "DOC^REFERRING"
    ds.StudyDescription = "Test Study for dcm4chee"
    
    # ===== SERIES MODULE (Requis) =====
    ds.SeriesDate = current_datetime.strftime("%Y%m%d")
    ds.SeriesTime = current_datetime.strftime("%H%M%S")
    ds.Modality = "CT"
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesNumber = 1
    ds.SeriesDescription = "Test Series"
    
    # ===== EQUIPMENT MODULE =====
    ds.Manufacturer = "Test Manufacturer"
    ds.ManufacturerModelName = "Test Model"
    ds.StationName = "TEST_STATION"
    ds.InstitutionName = "Test Hospital"
    
    # ===== IMAGE MODULE (Requis) =====
    ds.InstanceNumber = 1
    ds.ImageType = ["ORIGINAL", "PRIMARY", "AXIAL"]
    ds.AcquisitionDate = current_datetime.strftime("%Y%m%d")
    ds.AcquisitionTime = current_datetime.strftime("%H%M%S")
    ds.ContentDate = current_datetime.strftime("%Y%m%d")
    ds.ContentTime = current_datetime.strftime("%H%M%S")
    
    # ===== SOP COMMON MODULE (Requis) =====
    ds.SOPClassUID = CTImageStorage
    ds.SOPInstanceUID = generate_uid()
    ds.InstanceCreationDate = current_datetime.strftime("%Y%m%d")
    ds.InstanceCreationTime = current_datetime.strftime("%H%M%S")
    
    # ===== CHARACTER SET (CRITIQUE pour dcm4chee) =====
    ds.SpecificCharacterSet = 'ISO_IR 100'  # Latin-1
    
    # ===== IMAGE PIXEL MODULE =====
    # Création d'une petite image de test
    rows, cols = 128, 128
    pixel_array = np.random.randint(0, 255, (rows, cols), dtype=np.uint8)
    
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PixelData = pixel_array.tobytes()
    
    # ===== CT IMAGE MODULE (spécifique CT) =====
    ds.ImagePositionPatient = [0.0, 0.0, 0.0]
    ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    ds.SliceThickness = "5.0"
    ds.SliceLocation = "0.0"
    ds.PixelSpacing = [1.0, 1.0]
    
    # Paramètres CT spécifiques
    ds.KVP = "120"
    ds.RescaleIntercept = "0"
    ds.RescaleSlope = "1"
    ds.RescaleType = "HU"
    
    # Sauvegarde
    ds.is_little_endian = True
    ds.is_implicit_VR = False
    
    print(f"\nAttributs configurés :")
    print(f"  - Patient: {ds.PatientName} ({ds.PatientID})")
    print(f"  - Study: {ds.StudyInstanceUID}")
    print(f"  - Series: {ds.SeriesInstanceUID}")
    print(f"  - SOP Instance: {ds.SOPInstanceUID}")
    print(f"  - Charset: {ds.SpecificCharacterSet}")
    print(f"  - Modality: {ds.Modality}")
    print(f"  - Date/Time: {ds.StudyDate} {ds.StudyTime}")
    
    ds.save_as(output_filename, write_like_original=False)
    print(f"\n✓ Fichier DICOM créé : {output_filename}")
    
    return output_filename

def verify_dicom(filename):
    """
    Vérifie que tous les attributs critiques sont présents
    """
    print(f"\n{'='*60}")
    print(f"VÉRIFICATION DU FICHIER : {filename}")
    print(f"{'='*60}")
    
    ds = pydicom.dcmread(filename)
    
    # Liste des attributs critiques pour dcm4chee
    critical_attributes = [
        ('PatientName', '0010,0010'),
        ('PatientID', '0010,0020'),
        ('StudyInstanceUID', '0020,000D'),
        ('SeriesInstanceUID', '0020,000E'),
        ('SOPInstanceUID', '0008,0018'),
        ('SOPClassUID', '0008,0016'),
        ('Modality', '0008,0060'),
        ('StudyDate', '0008,0020'),
        ('StudyTime', '0008,0030'),
        ('SeriesDate', '0008,0021'),
        ('SeriesTime', '0008,0031'),
        ('AccessionNumber', '0008,0050'),
        ('ReferringPhysicianName', '0008,0090'),
        ('SpecificCharacterSet', '0008,0005'),
    ]
    
    print("\nAttributs critiques :")
    all_present = True
    for attr_name, tag in critical_attributes:
        if hasattr(ds, attr_name):
            value = getattr(ds, attr_name)
            status = "✓"
            print(f"  {status} {attr_name:30} ({tag}): {value}")
        else:
            status = "✗ MANQUANT"
            print(f"  {status} {attr_name:30} ({tag})")
            all_present = False
    
    print(f"\n{'='*60}")
    if all_present:
        print("✓ Tous les attributs critiques sont présents")
    else:
        print("✗ Certains attributs critiques sont manquants")
    print(f"{'='*60}\n")
    
    return all_present

if __name__ == "__main__":
    # Création du fichier
    filename = create_compliant_dicom()
    
    # Vérification
    verify_dicom(filename)
    
    print("\nProchaine étape : Envoi vers dcm4chee")
    print(f"  python send_cstore_dcm4chee.py {filename}")
