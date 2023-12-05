import sys
import heyexReader

input_filename = sys.argv[1]
output_oct = input_filename[:-4]+'_oct'
output_slo = input_filename[:-4]+'_slo.png'
#print(output_slo)

vol = heyexReader.volFile(input_filename)
#vol.renderIRslo(output_slo, renderGrid = True)
#vol.renderOCTscans(output_oct, renderSeg = False, file_format="png")

scan_pos = vol.fileHeader['scanPos'].decode('ascii')
exam_time = vol.fileHeader['examTime']
scan_id = vol.fileHeader['ID'].decode('ascii')
is_edi = vol.oct.shape[0]==7
oct_fov_x = vol.fileHeader["octSizeX"]*vol.fileHeader["scaleX"]
oct_fov_z = vol.fileHeader["octSizeZ"]*vol.fileHeader["scaleZ"]
oct_fov_y = vol.fileHeader["numBscan"]*vol.fileHeader["distance"]

#is_slo =
print(is_edi)
print(exam_time)
print(scan_pos)
print(scan_id)
print(vol.oct.shape)
print(vol.irslo.shape)
print(vol.fileHeader)
print("oct_fov_x =", round(oct_fov_x,3), "mm")
print("oct_fov_z =", round(oct_fov_z,3), "mm")
print("oct_fov_y =", round(oct_fov_y,3), "mm")
