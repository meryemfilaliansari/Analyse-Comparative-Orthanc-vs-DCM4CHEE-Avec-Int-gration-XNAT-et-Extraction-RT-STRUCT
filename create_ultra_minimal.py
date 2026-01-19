import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid, CTImageStorage
import numpy as np

ds = FileDataset("ultra_minimal.dcm", {}, preamble=b"\0"*128)
ds.file_meta = Dataset()
ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
ds.file_meta.MediaStorageSOPClassUID = CTImageStorage
ds.file_meta.MediaStorageSOPInstanceUID = generate_uid()

# Noms ultra-simples (ASCII pur, type PN)
from pydicom.valuerep import PersonName
ds.PatientName = PersonName("TEST^PATIENT")  # ASCII only
ds.PatientName.encode('iso8859')  # Force encoding
ds.OtherPatientNames = "TESTPATIENTASCII"
ds.PatientNameUnicode = u"TEST^PATIENT"
ds.add_new((0x0010, 0x1001), 'PN', "TEST^PATIENT")  # Other Patient Names
ds.add_new((0x0010, 0x0011), 'LO', "TESTID001")  # Alternate Patient ID
ds.PatientID = "1"
ds.add_new((0x0010, 0x0020), 'LO', "1")  # Patient ID (again)
ds.SpecificCharacterSet = 'ISO_IR 6'  # ASCII charset
ds.PatientBirthDate = "19700101"
ds.PatientSex = "M"
ds.AccessionNumber = "000001"
ds.StudyDate = "20251231"
ds.StudyTime = "120000"
ds.ReferringPhysicianName = "REF^DOC"
ds.StudyID = "1001"
ds.SeriesNumber = "1"
ds.InstanceNumber = "1"
ds.StudyInstanceUID = generate_uid()
ds.SeriesInstanceUID = generate_uid()
ds.SOPInstanceUID = generate_uid()
ds.SOPClassUID = CTImageStorage
ds.Modality = "CT"

# Image minimale
ds.Rows = 64
ds.Columns = 64
ds.BitsAllocated = 8
ds.BitsStored = 8
ds.HighBit = 7
ds.PixelRepresentation = 0
ds.SamplesPerPixel = 1
ds.PhotometricInterpretation = "MONOCHROME2"
ds.PixelData = np.zeros((64, 64), dtype=np.uint8).tobytes()

ds.save_as("ultra_minimal.dcm")

# Vérification PatientName après génération
ds_check = pydicom.dcmread("ultra_minimal.dcm")
print("PatientName:", ds_check.PatientName)
