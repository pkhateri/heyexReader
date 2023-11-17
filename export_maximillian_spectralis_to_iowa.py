import os, sys, glob
import heyexReader

#xml_filename = sys.argv[1]
#tiff_files_dir = sys.argv[2]
vol_filename = 'test.vol'
iowa_surfaces_filename = 'iowa_surfaces.xml'

#xml2vol = heyexReader.xml2VolConvertor(xml_filename, tiff_files_dir)

#oct_fov_x = xml2vol.fileHeader["octSizeX"]*xml2vol.fileHeader["scaleX"]
#oct_fov_z = xml2vol.fileHeader["octSizeZ"]*xml2vol.fileHeader["scaleZ"]
#oct_fov_y = xml2vol.fileHeader["numBscan"]*xml2vol.fileHeader["distance"]

#xml2vol.writeToVolFile(vol_filename)
#xml2vol.exportSegToIowaXML(iowa_surfaces_filename)

data_dir = '/home/pkhateri/Documents/data/maximilian/OCT-Normal-Data/'
iowa_dir = '/home/pkhateri/Documents/data/maximilian/OCT-Normal-Data/iowa_format'
if not os.path.exists(iowa_dir):
    os.system('mkdir %s'%(iowa_dir))
for d in glob.glob(data_dir+'Kontrolle_50'):
    print('### processing...', d)
    name = d.split('/')[-1]
    xml_filename = glob.glob(d+'/*.xml')[0]
    tiff_files_dir = d
    out_dir = os.path.join(iowa_dir, name)
    if not os.path.exists(out_dir):
        os.system('mkdir %s'%(out_dir))
    vol_filename = os.path.join(out_dir, name+'_OCT_Iowa.vol')
    iowa_surfaces_filename = os.path.join(out_dir, name+'_Surfaces_Iowa.xml')

    xml2vol = heyexReader.xml2VolConvertor(xml_filename, tiff_files_dir)
    xml2vol.writeToVolFile(vol_filename)
    xml2vol.exportSegToIowaXML(iowa_surfaces_filename)
