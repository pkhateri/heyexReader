'''
1) read quality values in the header of bscans measured by heyex
2) print these in a csv file:
    patient_id quality_of_bscan_0 quality_of_bscan_1 ... quality_of_bscan_48
'''
#todo: fix the bug when no slash after dirname is given
import sys
import os
import glob
import heyexReader

if len(sys.argv)==2:
    dir = sys.argv[1]
else:
    print("usage: python get_bscan_qualities.py path_to_the_vol_files")
    sys.exit()
logfile = open("get_bscan_qualities.log", "w")
bscan_qualities = open(os.path.join(dir,"bscan_qualities.csv"), "w")

for f in glob.glob(dir+'*.vol'):
    patient_id = os.path.basename(f)[:-4]
    print("processing...", patient_id, file=logfile)
    print(patient_id, end = ' ', file=bscan_qualities)
    vol = heyexReader.volFile(f)
    for i in range(0,vol.fileHeader["numBscan"]): 
        print(round(vol.bScanHeader(i)["quality"],2), end = ' ', file=bscan_qualities)
    print("", file=bscan_qualities)
