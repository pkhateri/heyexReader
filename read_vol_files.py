
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


dir = sys.argv[1]
print("patient_id exam_time scan_pos is_edi oct_shape oct_fov")
for f in glob.glob(dir+'*.vol'):
    patient_id = os.path.basename(f)[:-4]
    print(patient_id, end = ' ')
    vol = heyexReader.volFile(f)
    exam_time = vol.fileHeader['examTime'].replace(microsecond=0)
    scan_pos = vol.fileHeader['scanPos'].replace(b'\x00', b'') #remove null bytes from the end of bytes object then convert it to string
    scan_pos = scan_pos.decode('utf-8')
    is_edi = vol.oct.shape[0]==7
    oct_shape = vol.oct.shape
    oct_fov_x = round(vol.fileHeader["octSizeX"]*vol.fileHeader["scaleX"], 2)
    oct_fov_z = round(vol.fileHeader["octSizeZ"]*vol.fileHeader["scaleZ"], 2)
    oct_fov_y = round(vol.fileHeader["numBscan"]*vol.fileHeader["distance"], 2)
    scan_id = vol.fileHeader['ID'].decode('ascii')
    print(exam_time, scan_pos, is_edi, oct_shape[0], oct_shape[1], oct_shape[2], oct_fov_y, oct_fov_z, oct_fov_x)

'''
generate oct and slo files in png format
'''
#output_oct = input_filename[:-4]+'_oct'
#output_slo = input_filename[:-4]+'_slo.png'
#vol.renderIRslo(output_slo, renderGrid = True)
#vol.renderOCTscans(output_oct, renderSeg = True)
