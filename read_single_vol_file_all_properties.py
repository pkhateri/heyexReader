import sys
import heyexReader

input_filename = sys.argv[1]
output_oct = input_filename[:-4]+'_oct'
output_slo = input_filename[:-4]+'_slo.png'
#print(output_slo)

vol = heyexReader.volFile(input_filename)
#vol.renderIRslo(output_slo, renderGrid = True)
#vol.renderOCTscans(output_oct, renderSeg = True)

scan_pos = vol.fileHeader['scanPos'].decode('ascii')
exam_time = vol.fileHeader['examTime']
scan_id = vol.fileHeader['ID'].decode('ascii')
is_edi = vol.oct.shape[0]==7
oct_fov_x = vol.fileHeader["octSizeX"]*vol.fileHeader["scaleX"]
oct_fov_z = vol.fileHeader["octSizeZ"]*vol.fileHeader["scaleZ"]
oct_fov_y = vol.fileHeader["numBscan"]*vol.fileHeader["distance"]

print("version", vol.fileHeader["version"])
print("octSizeX", vol.fileHeader["octSizeX"])
print("numBscan", vol.fileHeader["numBscan"])
print("octSizeZ", vol.fileHeader["octSizeZ"])
print("scaleX", vol.fileHeader["scaleX"])
print("distance", vol.fileHeader["distance"])
print("scaleZ", vol.fileHeader["scaleZ"])
print("sizeXSlo", vol.fileHeader["sizeXSlo"])
print("sizeYSlo", vol.fileHeader["sizeYSlo"])
print("scaleXSlo", vol.fileHeader["scaleXSlo"])
print("scaleYSlo", vol.fileHeader["scaleYSlo"])
print("fieldSizeSlo", vol.fileHeader["fieldSizeSlo"])
print("scanFocus", vol.fileHeader["scanFocus"])
print("scanPos", vol.fileHeader["scanPos"])
print("examTime", vol.fileHeader["examTime"])
print("scanPattern", vol.fileHeader["scanPattern"])
print("BscanHdrSize", vol.fileHeader["BscanHdrSize"])
print("ID", vol.fileHeader["ID"])
print("ReferenceID", vol.fileHeader["ReferenceID"])
print("PID", vol.fileHeader["PID"])
print("PatientID", vol.fileHeader["PatientID"])
print("unknown2", vol.fileHeader["unknown2"])
print("DOB", vol.fileHeader["DOB"])
print("VID", vol.fileHeader["VID"])
print("VisitID", vol.fileHeader["VisitID"])
print("VisitDate", vol.fileHeader["VisitDate"])
print("GridType", vol.fileHeader["GridType"])
print("GridOffset", vol.fileHeader["GridOffset"])
