import requests
import os

 # Chemin du dossier contenant les DICOMs à uploader
DICOM_PATH = r"C:\Users\awati\Desktop\pacs\dicom_samples\rt_test"

DCM4CHEE_URL = "http://localhost:8080/dcm4chee-arc/aets/DCM4CHEE/rs/studies"
AUTH = ("admin", "admin")

def upload_file(file_path):
    with open(file_path, "rb") as f:
        files = {'file': (os.path.basename(file_path), f, 'application/dicom')}
        response = requests.post(DCM4CHEE_URL, files=files, auth=AUTH)
    print(f"{file_path} => {response.status_code} {response.reason}")

if os.path.isfile(DICOM_PATH):
    upload_file(DICOM_PATH)
elif os.path.isdir(DICOM_PATH):
    for root, _, files in os.walk(DICOM_PATH):
        for name in files:
            if name.lower().endswith(".dcm"):
                upload_file(os.path.join(root, name))
else:
    print("Chemin non valide :", DICOM_PATH)
