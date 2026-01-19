#!/usr/bin/env python3
"""
Script d'envoi DICOM vers dcm4chee avec diagnostics détaillés
"""

import pydicom
from pynetdicom import AE, evt, debug_logger
from pynetdicom.sop_class import CTImageStorage, MRImageStorage, SecondaryCaptureImageStorage
import sys

debug_logger()

def handle_store(event):
    ds = event.dataset
    print(f"\n{'='*60}")
    print("CALLBACK STORE - Informations reçues du serveur")
    print(f"{'='*60}")
    print(f"SOP Class UID: {ds.SOPClassUID}")
    print(f"SOP Instance UID: {ds.SOPInstanceUID}")
    return 0x0000

def send_dicom_with_diagnostics(
    dcm_file,
    host="localhost",
    port=11112,
    called_aet="DCM4CHEE",
    calling_aet="PYNETDICOM"
):
    print(f"\n{'='*70}")
    print(f"ENVOI DICOM VERS DCM4CHEE - MODE DIAGNOSTIC COMPLET")
    print(f"{'='*70}")
    print(f"\n1. Lecture du fichier : {dcm_file}")
    try:
        ds = pydicom.dcmread(dcm_file)
        print(f"   ✓ Fichier DICOM lu avec succès")
        print(f"   - Patient: {ds.PatientName}")
        print(f"   - SOP Class: {ds.SOPClassUID}")
        print(f"   - SOP Instance: {ds.SOPInstanceUID}")
        print(f"   - Transfer Syntax: {ds.file_meta.TransferSyntaxUID}")
    except Exception as e:
        print(f"   ✗ Erreur de lecture : {e}")
        return False
    print(f"\n2. Configuration de l'Application Entity")
    ae = AE(ae_title=calling_aet)
    ae.add_requested_context(CTImageStorage)
    ae.add_requested_context(MRImageStorage)
    ae.add_requested_context(SecondaryCaptureImageStorage)
    # Ajout des syntaxes de transfert non compressées
    transfer_syntaxes = [
        pydicom.uid.ExplicitVRLittleEndian,
        pydicom.uid.ImplicitVRLittleEndian,
        pydicom.uid.ExplicitVRBigEndian
    ]
    for cx in ae.requested_contexts:
        cx.transfer_syntax = transfer_syntaxes
    print(f"   ✓ AE Title: {calling_aet}")
    print(f"   ✓ Contextes de présentation configurés : {len(ae.requested_contexts)}")
    print(f"\n3. Connexion au serveur")
    print(f"   - Hôte: {host}")
    print(f"   - Port: {port}")
    print(f"   - Called AET: {called_aet}")
    try:
        assoc = ae.associate(host, port, ae_title=called_aet)
        if assoc.is_established:
            print(f"   ✓ Association établie avec succès")
            print(f"   - Contextes acceptés: {len(assoc.accepted_contexts)}")
            print(f"\n4. Contextes de présentation acceptés par le serveur:")
            for cx in assoc.accepted_contexts:
                print(f"   ✓ {cx.abstract_syntax}")
                print(f"     Transfer Syntax: {cx.transfer_syntax[0]}")
            print(f"\n5. Envoi du fichier DICOM (C-STORE)")
            print(f"   Envoi en cours...")
            status = assoc.send_c_store(ds)
            print(f"\n{'='*70}")
            print(f"RÉSULTAT DE L'ENVOI")
            print(f"{'='*70}")
            if status:
                status_code = status.Status
                print(f"Status Code: 0x{status_code:04X}")
                if status_code == 0x0000:
                    print(f"✓✓✓ SUCCÈS ! Le fichier a été accepté et stocké par dcm4chee")
                    result = True
                elif status_code == 0x0110:
                    print(f"✗✗✗ ÉCHEC : Processing Failure (0x0110)")
                    print(f"\nCe code indique que dcm4chee a rejeté le fichier.")
                    print(f"Causes possibles :")
                    print(f"  - Attribut DICOM manquant ou invalide")
                    print(f"  - Contrainte de validation non respectée")
                    print(f"  - Problème d'encodage (charset)")
                    print(f"  - Configuration serveur restrictive")
                    result = False
                elif status_code == 0xB000:
                    print(f"⚠ WARNING : Coercion of Data Elements (0xB000)")
                    print(f"Le fichier a été accepté mais avec modifications")
                    result = True
                elif status_code == 0xB007:
                    print(f"⚠ WARNING : Data Set does not match SOP Class (0xB007)")
                    result = False
                elif status_code == 0xB006:
                    print(f"⚠ WARNING : Elements Discarded (0xB006)")
                    result = True
                elif status_code in [0xC000, 0xC001, 0xC002]:
                    print(f"✗ ERREUR : Cannot understand (0x{status_code:04X})")
                    result = False
                elif status_code == 0xA700:
                    print(f"✗ ERREUR : Out of Resources (0xA700)")
                    result = False
                elif status_code == 0xA900:
                    print(f"✗ ERREUR : Data Set does not match SOP Class (0xA900)")
                    result = False
                else:
                    print(f"? Status inconnu : 0x{status_code:04X}")
                    result = False
                if hasattr(status, 'ErrorComment'):
                    print(f"\nCommentaire d'erreur : {status.ErrorComment}")
                if hasattr(status, 'OffendingElement'):
                    print(f"Élément problématique : {status.OffendingElement}")
                if hasattr(status, 'ErrorID'):
                    print(f"Error ID : {status.ErrorID}")
            else:
                print(f"✗✗✗ ÉCHEC : Aucune réponse du serveur")
                result = False
            print(f"\n6. Fermeture de l'association")
            assoc.release()
            print(f"   ✓ Association libérée")
        else:
            print(f"   ✗✗✗ ÉCHEC : Impossible d'établir l'association")
            print(f"\nRaisons possibles :")
            print(f"  - AE Title '{called_aet}' non configuré sur dcm4chee")
            print(f"  - Port {port} incorrect ou service non démarré")
            print(f"  - Pare-feu bloquant la connexion")
            print(f"  - Contextes de présentation rejetés")
            if assoc.rejected:
                print(f"\nDétails du rejet :")
                print(f"  Raison : {assoc.rejected}")
            result = False
    except Exception as e:
        print(f"   ✗ Exception lors de la connexion : {e}")
        import traceback
        traceback.print_exc()
        result = False
    print(f"\n{'='*70}\n")
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_enhanced_dcm4chee.py <fichier.dcm> [host] [port] [called_aet]")
        print("\nExemple:")
        print("  python send_enhanced_dcm4chee.py compliant_test.dcm")
        print("  python send_enhanced_dcm4chee.py test.dcm localhost 11112 DCM4CHEE")
        sys.exit(1)
    dcm_file = sys.argv[1]
    host = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 11112
    called_aet = sys.argv[4] if len(sys.argv) > 4 else "DCM4CHEE"
    success = send_dicom_with_diagnostics(dcm_file, host, port, called_aet)
    sys.exit(0 if success else 1)
