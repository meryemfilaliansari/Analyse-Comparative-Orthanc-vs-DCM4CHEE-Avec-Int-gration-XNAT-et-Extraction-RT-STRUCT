from pynetdicom import AE
from pynetdicom.sop_class import (
    CTImageStorage,
    MRImageStorage,
    RTStructureSetStorage,
    RTDoseStorage,
    RTPlanStorage,
    SecondaryCaptureImageStorage
)
import os
import pydicom

DICOM_DIR = r"C:/Users/awati/Downloads/case4/case4"

ae = AE(ae_title="PYTHONSCU")

# Contextes acceptés
ae.add_requested_context(CTImageStorage)
ae.add_requested_context(MRImageStorage)
ae.add_requested_context(RTStructureSetStorage)
ae.add_requested_context(RTDoseStorage)
ae.add_requested_context(RTPlanStorage)
ae.add_requested_context(SecondaryCaptureImageStorage)

assoc = ae.associate("localhost", 11112, ae_title="DCM4CHEE")

if assoc.is_established:
    for root, _, files in os.walk(DICOM_DIR):
        for f in files:
            if f.lower().endswith(".dcm"):
                ds = pydicom.dcmread(os.path.join(root, f))
                status = assoc.send_c_store(ds)
    assoc.release()
    print("✅ DICOM envoyés avec succès à DCM4CHEE")
else:
    print("❌ Association refusée")
