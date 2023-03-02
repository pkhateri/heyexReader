
'''
usage: python read_vol_files.py path_to_the_vol_files
1) read vol files
2) print these in a csv file:
    patient_id, exam_time, scan_pos, is_edi, oct_shape, oct_fov
3) rename the files based on their scan_pos ans exam_time
'''

import sys
import os
import glob
import heyexReader

if len(sys.argv)==2:
    dir = sys.argv[1]
else:
    print("usage: python read_vol_files.py path_to_the_vol_files")
    sys.exit()

oct_properties = open(os.path.join(dir, "oct_properties.csv"), "w")

print("patient_id exam_time scan_pos is_edi oct_shape_y oct_shape_z oct_shape_x oct_fov_y oct_fov_z oct_fov_x bscan_spacing", file=oct_properties)
for f in glob.glob(dir+'*.vol'):
    patient_id = os.path.basename(f)[:-4]
    print(patient_id, end = ' ', file=oct_properties)
    vol = heyexReader.volFile(f)
    exam_time = vol.fileHeader['examTime'].replace(microsecond=0)
    scan_pos = vol.fileHeader['scanPos'].replace(b'\x00', b'') #remove null bytes from the end of bytes object then convert it to string
    scan_pos = scan_pos.decode('utf-8')
    is_edi = vol.oct.shape[0]==7
    oct_shape = vol.oct.shape
    oct_fov_x = round(vol.fileHeader["octSizeX"]*vol.fileHeader["scaleX"], 2)
    oct_fov_z = round(vol.fileHeader["octSizeZ"]*vol.fileHeader["scaleZ"], 2)
    oct_fov_y = round(vol.fileHeader["numBscan"]*vol.fileHeader["distance"], 2)
    bscan_spacing = round(vol.fileHeader["distance"], 2)
    scan_id = vol.fileHeader['ID'].decode('ascii')
    print(exam_time, scan_pos, is_edi, oct_shape[0], oct_shape[1], oct_shape[2], oct_fov_y, oct_fov_z, oct_fov_x, bscan_spacing, file=oct_properties)
