import os
from pydicom import dcmread
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import CTImageStorage, MRImageStorage, RTStructureSetStorage

debug_logger()  # Logs détaillés

# Paramètres DICOM C-STORE
dcm4chee_ae_title = 'DCM4CHEE'
dcm4chee_ip = 'localhost'
dcm4chee_port = 11112
calling_ae_title = 'DCM4CHEE'

# Chemin du fichier ou dossier à envoyer
# Test avec un vrai CT DICOM corrigé (PatientName présent)
DICOM_PATH = r"C:\Users\awati\Desktop\pacs\rt_complete_sample\CT_001_fixed.dcm"
# Pour envoyer tout un dossier, mets le chemin du dossier ci-dessous
# DICOM_PATH = r"C:\Users\awati\Desktop\mon_dossier_dicom"

# Fonction d'envoi C-STORE
def send_dicom(file_path):
    ds = dcmread(file_path)
    ae = AE(ae_title=calling_ae_title)
    # Ajoute les SOP Classes courantes
    ae.add_requested_context(CTImageStorage)
    ae.add_requested_context(MRImageStorage)
    ae.add_requested_context(RTStructureSetStorage)
    assoc = ae.associate(dcm4chee_ip, dcm4chee_port, ae_title=dcm4chee_ae_title)
    if assoc.is_established:
        status = assoc.send_c_store(ds)
        print(f"{file_path} => Status: 0x{status.Status:04x}")
        assoc.release()
    else:
        print(f"Association failed for {file_path}")

if os.path.isfile(DICOM_PATH):
    send_dicom(DICOM_PATH)
elif os.path.isdir(DICOM_PATH):
    for root, _, files in os.walk(DICOM_PATH):
        for name in files:
            if name.lower().endswith('.dcm'):
                send_dicom(os.path.join(root, name))
else:
    print("Chemin non valide :", DICOM_PATH)
