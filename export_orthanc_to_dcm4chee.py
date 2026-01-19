import requests
import os
from pydicom import dcmread
from pynetdicom import AE, StoragePresentationContexts

ORTHANC_URL = 'http://localhost:8042'
ORTHANC_USERNAME = ''  # set if needed
ORTHANC_PASSWORD = ''  # set if needed
DCM4CHEE_AET = 'DCM4CHEE'
DCM4CHEE_HOST = 'localhost'
DCM4CHEE_PORT = 11112

# 1. Get all instance IDs from Orthanc
r = requests.get(f'{ORTHANC_URL}/instances', auth=(ORTHANC_USERNAME, ORTHANC_PASSWORD) if ORTHANC_USERNAME else None)
r.raise_for_status()
instance_ids = r.json()

# 2. Download all DICOM files from Orthanc
dicom_files = []
os.makedirs('orthanc_export', exist_ok=True)
for iid in instance_ids:
    out_path = os.path.join('orthanc_export', f'{iid}.dcm')
    url = f'{ORTHANC_URL}/instances/{iid}/file'
    resp = requests.get(url, auth=(ORTHANC_USERNAME, ORTHANC_PASSWORD) if ORTHANC_USERNAME else None)
    resp.raise_for_status()
    with open(out_path, 'wb') as f:
        f.write(resp.content)
    dicom_files.append(out_path)

# 3. Send all DICOM files to dcm4chee using pynetdicom
print(f'Sending {len(dicom_files)} DICOM files to {DCM4CHEE_AET}@{DCM4CHEE_HOST}:{DCM4CHEE_PORT}...')
ae = AE()
for context in StoragePresentationContexts:
    ae.add_requested_context(context.abstract_syntax)
assoc = ae.associate(DCM4CHEE_HOST, DCM4CHEE_PORT, ae_title=DCM4CHEE_AET)
if assoc.is_established:
    from pydicom.uid import ExplicitVRLittleEndian
    from pydicom.uid import generate_uid
    from pydicom.valuerep import PersonName
    for idx, dcm_path in enumerate(dicom_files):
        ds = dcmread(dcm_path)
        # Force essential DICOM compliance fields
        ds.PatientName = PersonName(f"TEST^PATIENT{idx+1}")
        ds.PatientID = f"P{idx+1:04d}"
        ds.SpecificCharacterSet = 'ISO_IR 6'
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = generate_uid()
        ds.StudyID = f"{1000+idx}"
        ds.SeriesNumber = "1"
        ds.InstanceNumber = "1"
        ds.Modality = ds.get('Modality', 'CT')
        # File Meta
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ds.file_meta.MediaStorageSOPClassUID = ds.SOPClassUID if 'SOPClassUID' in ds else ds.file_meta.get('MediaStorageSOPClassUID', None)
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
        ds.is_implicit_VR = False
        ds.is_little_endian = True
        # Save as temp file
        dcm_path_conv = dcm_path + '.conv.dcm'
        ds.save_as(dcm_path_conv)
        ds_to_send = dcmread(dcm_path_conv)
        status = assoc.send_c_store(ds_to_send)
        print(f'Sent {os.path.basename(dcm_path_conv)}: Status 0x{status.Status:04x}')
    assoc.release()
    print('All files sent.')
else:
    print('Association to dcm4chee failed.')
