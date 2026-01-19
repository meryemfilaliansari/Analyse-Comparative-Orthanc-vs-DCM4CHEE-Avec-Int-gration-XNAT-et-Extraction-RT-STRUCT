from pynetdicom import AE
from pynetdicom.sop_class import CTImageStorage, MRImageStorage, RTStructStorage
import os

# Chemin du fichier ou dossier à envoyer
DICOM_PATH = r"C:\Users\awati\Desktop\manifest-1684259732535\Prostate-Anatomical-Edge-Cases\Prostate-AEC-001\11-17-1992-NA-RX SIMULATION-82988\2.000000-Pelvis-13578\1-001.dcm"
# Pour envoyer tout un dossier, mets le chemin du dossier ci-dessous
# DICOM_PATH = r"C:\Users\awati\Desktop\mon_dossier_dicom"

# Paramètres dcm4chee
DCM4CHEE_AET = "DCM4CHEE"
DCM4CHEE_HOST = "localhost"
DCM4CHEE_PORT = 11112

# AE local
LOCAL_AET = "PYNETDICOM"

# Liste des SOP Classes courantes
SOP_CLASSES = [CTImageStorage, MRImageStorage, RTStructStorage]

def send_file(file_path):
    ae = AE(ae_title=LOCAL_AET)
    for sop in SOP_CLASSES:
        ae.add_requested_context(sop)
    assoc = ae.associate(DCM4CHEE_HOST, DCM4CHEE_PORT, ae_title=DCM4CHEE_AET)
    if assoc.is_established:
        with open(file_path, 'rb') as f:
            data = f.read()
        status = assoc.send_c_store(data)
        print(f"{file_path} => Status: {status.Status:#04x}")
        assoc.release()
    else:
        print(f"Association failed for {file_path}")

if os.path.isfile(DICOM_PATH):
    send_file(DICOM_PATH)
elif os.path.isdir(DICOM_PATH):
    for root, _, files in os.walk(DICOM_PATH):
        for name in files:
            if name.lower().endswith(".dcm"):
                send_file(os.path.join(root, name))
else:
    print("Chemin non valide :", DICOM_PATH)
