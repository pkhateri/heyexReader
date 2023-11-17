#!/usr/bin/env python
#
# Parisa Khateri (IOB, Basel) 2023
#


import struct, array, datetime, codecs
import numpy as np
from collections import OrderedDict
import xml.etree.ElementTree as ET
import ntpath
from PIL import Image
import os
from skimage.util import img_as_float32


class xml2VolConvertor():
    def __init__(self, xml_filename, tiff_files_dir):
        """
        Parses Heyex Spectralis *.xml and *.tiff files.

        Args:
            xml_filename, tiff_files_dir (str): Pathes to *.xml and *.tiff files.

        Returns:
            Spectralis volFile

        """
        self.__parseXMLFile(xml_filename, tiff_files_dir)

    @property
    def oct(self):
        """
        Retrieve OCT volume as a 3D numpy array.

        Returns:
            3D numpy array with OCT intensities as 'uint8' array

        """
        return self.wholefile["cScan"]

    @property
    def irslo(self):
        """
        Retrieve IR SLO image as 2D numpy array

        Returns:
            2D numpy array with IR reflectance SLO image as 'uint8' array.

        """
        return self.wholefile["sloImage"]

    @property
    def grid(self):
        """
        Retrieve the IR SLO pixel coordinates for the B scan OCT slices

        Returns:
            2D numpy array with the number of b scan images in the first dimension
            and x_0, y_0, x_1, y_1 defining the line of the B scan on the pixel
            coordinates of the IR SLO image.

        """
        wf = self.wholefile
        grid = []
        for bi in range(len(wf["slice-headers"])):
            bscanHead = wf["slice-headers"][bi]
            x_0 = int(bscanHead["startX"] / wf["header"]["scaleXSlo"])
            x_1 = int(bscanHead["endX"] / wf["header"]["scaleXSlo"])
            y_0 = int(bscanHead["startY"] / wf["header"]["scaleYSlo"])
            y_1 = int(bscanHead["endY"] / wf["header"]["scaleYSlo"])
            grid.append([x_0, y_0, x_1, y_1])
        return grid

    def renderIRslo(self, filename, renderGrid=False):
        """
        Renders IR SLO image as a PNG file and optionally overlays grid of B scans

        Args:
            filename (str): filename to save IR SLO image
            renderGrid (bool): True will render red lines for the location of the B scans.

        Returns:
            None

        """
        from PIL import Image, ImageDraw
        wf = self.wholefile
        a = np.copy(wf["sloImage"])
        if renderGrid:
            a = np.stack((a,)*3, axis=-1)
            a = Image.fromarray(a)
            draw = ImageDraw.Draw(a)
            grid = self.grid
            for (x_0, y_0, x_1, y_1) in grid:
                draw.line((x_0,y_0, x_1, y_1), fill=(255,0,0), width=3)
            a.save(filename)
        else:
            Image.fromarray(a).save(filepre)

    def renderOCTscans(self, filepre = "oct", renderSeg=False):
        """
        Renders OCT images a PNG file and optionally overlays segmentation lines

        Args:
            filepre (str): filename prefix. OCT Images will be named as "<prefix>-001.png"
            renderSeg (bool): True will render colored lines for the segmentation of the RPE, ILM, and NFL on the B scans.

        Returns:
            None

        """
        from PIL import Image
        wf = self.wholefile
        for i in range(wf["cScan"].shape[0]):
            a = np.copy(wf["cScan"][i])

            if renderSeg:
                a = np.stack((a,)*3, axis=-1)
                for li in range(wf["segmentations"].shape[0]):
                    for x in range(wf["segmentations"].shape[2]):
                        a[int(wf["segmentations"][li,i,x]),x, li] = 255

            Image.fromarray(a).save("%s-%03d.png" % (filepre, i))

    def get_bscan_spacing(self, bscanheaders):
        # Check if all B-scans are parallel and have the same distance. They might be rotated though
        dist_func = lambda a, b: np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
        start_distances = [
            dist_func([bscanheaders[i]['startX'], bscanheaders[i]['startY']], [bscanheaders[i + 1]['startX'],bscanheaders[i + 1]['startY']] )
            for i in range(len(bscanheaders) - 1)
        ]
        end_distances = [
            dist_func([bscanheaders[i]['endX'], bscanheaders[i]['endY']], [bscanheaders[i + 1]['endX'],bscanheaders[i + 1]['endY']] )
            for i in range(len(bscanheaders) - 1)
        ]
        if not np.allclose(start_distances[0],
                           np.array(start_distances + end_distances),
                           rtol=4e-2):
            msg = 'B-scans are not equally spaced. Projections into the enface space are distorted.'
            logger.warning(msg)
        return np.mean(start_distances + end_distances)

    def writeToVolFile(self, vol_filename):
        wholefile = self.wholefile
        with open(vol_filename, "wb") as fout:
            """
            write header values
            """
            header = wholefile["header"]
            fout.write(struct.pack("12s", header["version"].ljust(12).encode('utf-8')))
            fout.write(struct.pack("I", header["octSizeX"])) # lateral resolution
            fout.write(struct.pack("I", header["numBscan"]))
            fout.write(struct.pack("I", header["octSizeZ"])) # OCT depth
            fout.write(struct.pack("d", header["scaleX"]))
            fout.write(struct.pack("d", header["distance"]))
            fout.write(struct.pack("d", header["scaleZ"]))
            fout.write(struct.pack("I", header["sizeXSlo"]))
            fout.write(struct.pack("I", header["sizeYSlo"]))
            fout.write(struct.pack("d", header["scaleXSlo"]))
            fout.write(struct.pack("d", header["scaleYSlo"]))
            fout.write(struct.pack("I", int(header["fieldSizeSlo"]))) # FOV in degrees
            fout.write(struct.pack("d", header["scanFocus"]))
            fout.write(struct.pack("4s", header["scanPos"].ljust(4).encode('utf-8')))
            fout.write(struct.pack("l", int(header["examTime"].timestamp() * 1e7)))
            fout.write(struct.pack("I", header["scanPattern"]))
            fout.write(struct.pack("I", header["BscanHdrSize"]))
            fout.write(struct.pack("16s", header["ID"].encode('utf-8')))
            fout.write(struct.pack("16s", header["ReferenceID"].ljust(16).encode('utf-8')))
            fout.write(struct.pack("I", int(header["PID"])))
            fout.write(struct.pack("21s", header["PatientID"].ljust(21).encode('utf-8')))
            fout.write(header["unknown2"])
            fout.write(struct.pack("d", header["DOB"].timestamp() / (24 * 60 * 60) + 25569))
            fout.write(struct.pack("I", int(header["VID"])))
            fout.write(struct.pack("24s", header["VisitID"].ljust(24).encode('utf-8')))
            fout.write(struct.pack("d", header["VisitDate"].timestamp() / (24 * 60 * 60) + 25569)) # To be checked
            fout.write(struct.pack("I", header["GridType"]))
            fout.write(struct.pack("I", header["GridOffset"]))
            fout.write(struct.pack("I", header["GridType1"]))
            fout.write(struct.pack("I", header["GridOffset1"]))
            fout.write(struct.pack("34s", header["ProgID"].ljust(34).encode('utf-8')))

            """
            so far 216 bytes out of 2048 bytes have been filled
            write empty bytes to fill 2048 bytes
            """
            fout.write(struct.pack("1790x"))


            """
            write slo image
            """
            U = wholefile["sloImage"] # an np.array of dtype=np.uint8
            U = U.flatten()
            fout.write(U.tobytes())

            """
            write oct image
            ascan: 1D, a line of scan
            bscan: 2D, a pack of cscans
            cscan: 3D, a pack of bscans
            """
            bscanheaders = wholefile["slice-headers"] # a list of headers for individual bscans
            bscans = wholefile["cScan"] # a list of bscans, each bscan is a list of ascans, each ascan is an array
            #segmentations = wholefile["segmentations"] # np.array

            for i in range(header["numBscan"]):
                """
                write bscan header
                """
                bscanHead = bscanheaders[i]
                fout.write(struct.pack("12s", bscanHead["version"].encode('utf-8')))
                fout.write(struct.pack("I", bscanHead["BscanHdrSize"]))
                fout.write(struct.pack("d", bscanHead["startX"]))
                fout.write(struct.pack("d", bscanHead["startY"]))
                fout.write(struct.pack("d", bscanHead["endX"]))
                fout.write(struct.pack("d", bscanHead["endY"]))
                fout.write(struct.pack("I", bscanHead["numSeg"]))
                fout.write(struct.pack("I", bscanHead["offSeg"]))
                fout.write(struct.pack("f", bscanHead["quality"]))
                fout.write(struct.pack("I", bscanHead["shift"]))
                fout.write(struct.pack("6f", 0.,0.,0.,0.,0.,0)) #IVTrafo float
                fout.write(struct.pack("168x")) # so far 88, 168 = 256 - 88

                """
                write empty space to fill bscanhdrsize
                """
                empty_space = str(bscanHead["BscanHdrSize"] - 256 - bscanHead["numSeg"]*4*header["octSizeX"])+'x'
                fout.write(struct.pack(empty_space))

                """
                write OCT segmentations data: skip for now
                """
                #segmentation = []
                #U = array.array('f', np.array(segmentation).flatten())
                #fout.write(U.tobytes())

                """
                write OCT bscan data
                """
                U = bscans[i] # an array of dtype=np.float32
                U = array.array('f', U.flatten())
                fout.write(U.tobytes())

    def __parseXMLFile(self, xml_filename, tiff_files_dir):
        """
        read header values from the xml file and store in a dictionary
        """
        wholefile = OrderedDict()
        header = OrderedDict()

        tree = ET.parse(os.path.join(xml_filename))
        root = tree.getroot()
        data = root.find('BODY/Patient/Study/Series')
        images = data.findall('Image')
        bscan_blocks = []
        for img in images:
            if img.find('ImageType/Type').text=='LOCALIZER':
                slo = img
            if img.find('ImageType/Type').text=='OCT':
                bscan_blocks.append(img)

        """
        extract header info
        """
        header["version"] = root.find('BODY/SWVersion/Version').text
        header["octSizeX"] = int(bscan_blocks[0].find('OphthalmicAcquisitionContext/Width').text)
        header["numBscan"] = int(data.find('NumImages').text) -1 # or len(bscans)
        header["octSizeZ"] = int(bscan_blocks[0].find('OphthalmicAcquisitionContext/Height').text)
        header["scaleX"] = float(bscan_blocks[0].find('OphthalmicAcquisitionContext/ScaleX').text)
        header["distance"] = 0.
        header["scaleZ"] = float(bscan_blocks[0].find('OphthalmicAcquisitionContext/ScaleY').text)
        header["sizeXSlo"] = int(slo.find('OphthalmicAcquisitionContext/Width').text)
        header["sizeYSlo"] = int(slo.find('OphthalmicAcquisitionContext/Height').text)
        header["scaleXSlo"] = float(slo.find('OphthalmicAcquisitionContext/ScaleX').text)
        header["scaleYSlo"] = float(slo.find('OphthalmicAcquisitionContext/ScaleY').text)
        header["fieldSizeSlo"] = float(slo.find('OphthalmicAcquisitionContext/Angle').text) # FOV in degrees
        header["scanFocus"] = float(slo.find('OphthalmicAcquisitionContext/Focus').text)
        if data.find('Laterality').text == "R":
            header["scanPos"] = 'OD'
        elif data.find('Laterality').text == "L":
            header["scanPos"] = 'OS'
        study_year = int(root.find('BODY/Patient/Study/StudyDate/Date/Year').text)
        study_month = int(root.find('BODY/Patient/Study/StudyDate/Date/Month').text)
        study_day = int(root.find('BODY/Patient/Study/StudyDate/Date/Day').text)
        study_date = datetime.date(study_year, study_month, study_day)
        header["examTime"] = datetime.datetime.combine(study_date, datetime.time.min)
        header["scanPattern"] = 0 # 0:unknown
        header["BscanHdrSize"] = 1024
        if not root.find('BODY/Patient/PatientID')== None:
            patient_id = root.find('BODY/Patient/PatientID').text
        else:
            patient_id = 'unknown'
        header["ID"] = patient_id
        header["ReferenceID"] = patient_id
        header["PID"] = root.find('BODY/Patient/ID').text
        header["PatientID"] = patient_id # this should be of length 21
        header["unknown2"] = b'\x01\x02\x03'
        dob_year = int(root.find('BODY/Patient/Birthdate/Date/Year').text)
        dob_month = int(root.find('BODY/Patient/Birthdate/Date/Month').text)
        dob_day = int(root.find('BODY/Patient/Birthdate/Date/Day').text)
        dob = datetime.date(dob_year, dob_month, dob_day)
        header["DOB"] = datetime.datetime.combine(dob, datetime.time.min)
        header["VID"] = root.find('BODY/Patient/ID').text
        header["VisitID"] = patient_id # this should be of length 24
        header["VisitDate"] = datetime.datetime.combine(study_date, datetime.time.min)
        header["GridType"] = 0 #int(root.findall('BODY/Patient/Study/Series/ThicknessGrid/Type')[0].text)
        header["GridOffset"] = 0 #int(root.findall('BODY/Patient/Study/Series/ThicknessGrid/CenterPos/Coord/X')[0].text)
        header["GridType1"] = 0 #int(root.findall('BODY/Patient/Study/Series/ThicknessGrid/Type')[1].text)
        header["GridOffset1"] = 0 #int(root.findall('BODY/Patient/Study/Series/ThicknessGrid/CenterPos/Coord/X')[1].text)
        header["ProgID"] = patient_id # this should be of length 34

        wholefile["header"] = header

        """
        extract slo data
        """
        slo_path = os.path.basename(slo.find('ImageData/ExamURL').text)
        _, slo_filename = ntpath.split(slo_path)
        r, _, _ = Image.open(os.path.join(tiff_files_dir, slo_filename)).convert("RGB").split()
        slo_data = np.array(r, dtype=np.uint8) #pixel values 0-255
        wholefile["sloImage"] = slo_data

        """
        extract OCT header, Bscan data and segmentation boundaries
        """
        bscanheaders = []
        bscans = []
        segmentations = []
        for b in bscan_blocks:
            bscanHead = OrderedDict()
            bscanHead["version"] = root.find('BODY/Patient/Study/Series/GeneralEquipment/AQMVersion/Version').text
            bscanHead["BscanHdrSize"] = header["BscanHdrSize"] # integer
            bscanHead["startX"] = float(b.find('OphthalmicAcquisitionContext/Start/Coord/X').text)
            bscanHead["startY"] = float(b.find('OphthalmicAcquisitionContext/Start/Coord/Y').text)
            bscanHead["endX"] = float(b.find('OphthalmicAcquisitionContext/End/Coord/X').text)
            bscanHead["endY"] = float(b.find('OphthalmicAcquisitionContext/End/Coord/Y').text)
            bscanHead["numSeg"] = 0
            bscanHead["offSeg"] = 0
            bscanHead["quality"] = float(b.find('OphthalmicAcquisitionContext/ImageQuality').text)
            bscanHead["shift"] = 0
            bscanHead["filename"] = os.path.basename(b.find('ImageData/ExamURL').text)
            bscanheaders.append(bscanHead)
            # till here the size of bscanHead should be 60 bytes

            # bscan data
            bscan_path = os.path.basename(b.find('ImageData/ExamURL').text)
            _, bscan_filename = ntpath.split(bscan_path)
            r, _, _ = Image.open(os.path.join(tiff_files_dir, bscan_filename)).convert("RGB").split()
            bscan_data = np.array(r, dtype=np.uint8) #pixel values 0-255, shape:height x width
            # the next 3 lines are taken from eyepy library
            bscan_data = img_as_float32(bscan_data)
            bscan_data = bscan_data*8.285 - 8.3
            bscan_data = np.exp(bscan_data) - 2.44e-04
            bscans.append(bscan_data)

            # segmentation data
            boundaries_dict = {'ILM':[], 'BM':[], 'RNFL':[], 'GCL':[],
                               'IPL':[], 'INL':[], 'OPL':[], 'ELM':[],
                               'CHO':[], 'PR1':[], 'PR2':[], 'RPE':[]}
            seg_data = b.find('Segmentation')
            if not seg_data==None:
                seg_lines = seg_data.findall('SegLine')
                for line in seg_lines:
                    for key in boundaries_dict.keys():
                        if line.find('Name').text == key:
                            line_list = line.find('Array').text.split(' ')
                            line_float = list(map(float, line_list)) # because it includes floats like '3e+038'
                            boundaries_dict[key] = [int(l) for l in line_float]
            segmentations.append(boundaries_dict)

        header["distance"] = self.get_bscan_spacing(bscanheaders)
        wholefile["slice-headers"] = bscanheaders
        wholefile["cScan"] = np.array(bscans)
        wholefile["segmentations"] = np.array(segmentations)
        self.wholefile = wholefile

    def exportSegToIowaXML(self, iowa_surfaces_filename):
        wholefile = self.wholefile
        segmentations = wholefile["segmentations"]
        header = wholefile["header"]

        labels_dict = { # a dictionary mapping heyex labels to iowa labels
                'ILM':['10','ILM (ILM)'],
                'OPL':['60','OPL-Henles fiber layer (OPL-HFL)'],
                'ELM':['100','Boundary of myoid and ellipsoid of inner segments (BMEIS)'],
                'PR1':['110','IS/OS junction (IS/OSJ)'],
                #'GCL':['120','Inner boundary of OPR (IB_OPR)'],
                #'RPE':['140','Inner boundary of RPE (IB_RPE)'],
                'BM':['150','Outer boundary of RPE (OB_RPE)'],
                #'CHO': ['170', 'Coroid outer'] # not existing for all bscans
                }

        surfaces = ET.Element('surfaces')
        version = ET.SubElement(surfaces, 'version')
        version.text = '4.0.0'
        scan_characteristics = ET.SubElement(surfaces, 'scan_characteristics')
        manufacturer = ET.SubElement(scan_characteristics, 'manufacturer')
        manufacturer.text = 'Heidelberg Engineering'
        size = ET.SubElement(scan_characteristics, 'size')
        unit = ET.SubElement(size, 'unit')
        x = ET.SubElement(size, 'x')
        y = ET.SubElement(size, 'y')
        z = ET.SubElement(size, 'z')
        unit.text = 'voxel'
        x.text = str(header["octSizeX"])
        y.text = str(header["octSizeZ"])
        z.text = str(header["numBscan"])
        voxel_size = ET.SubElement(scan_characteristics, 'voxel_size')
        unit = ET.SubElement(voxel_size, 'unit')
        x = ET.SubElement(voxel_size, 'x')
        y = ET.SubElement(voxel_size, 'y')
        z = ET.SubElement(voxel_size, 'z')
        unit.text = 'mm'
        x.text = str(header["scaleX"])
        y.text = str(header["scaleZ"])
        z.text = str(header["distance"])
        laterality = ET.SubElement(scan_characteristics, 'laterality')
        laterality.text = header["scanPos"]
        center_type = ET.SubElement(scan_characteristics, 'center_type')
        center_type.text = 'macula'
        unit = ET.SubElement(surfaces, 'unit')
        unit.text = 'voxel'
        surface_size  = ET.SubElement(surfaces, 'surface_size')
        x = ET.SubElement(surface_size, 'x')
        z = ET.SubElement(surface_size, 'z')
        x.text = str(header["octSizeX"])
        z.text = str(header["numBscan"])
        surface_num  = ET.SubElement(surfaces, 'surface_num')
        surface_num.text = str(len(labels_dict))

        for l in labels_dict:
            surface = ET.SubElement(surfaces, 'surface')
            label = ET.SubElement(surface, 'label')
            label.text = labels_dict[l][0]
            name = ET.SubElement(surface, 'name')
            name.text = labels_dict[l][1]
            instance = ET.SubElement(surface, 'instance')
            instance.text = 'NA'
            for b in reversed(range(header["numBscan"])):
                bscan = ET.SubElement(surface, 'bscan')
                if not segmentations[b][l] == []:
                    for i in range(header["octSizeX"]):
                        y = ET.SubElement(bscan, 'y')
                        y.text = str(segmentations[b][l][i])
                else:
                    print("layer %s does not exist for bscan %s" %(l,b))
        tree = ET.ElementTree(surfaces)
        tree.write(iowa_surfaces_filename, xml_declaration=True, encoding='utf-8')


    @property
    def fileHeader(self):
        """
        Retrieve vol header fields

        Returns:
            Dictionary with the following keys
                - version: version number of vol file definition
                - numBscan: number of B scan images in the volume
                - octSizeX: number of pixels in the width of the OCT B scan
                - octSizeZ: number of pixels in the height of the OCT B scan
                - distance: unknown
                - scaleX: resolution scaling factor of the width of the OCT B scan
                - scaleZ: resolution scaling factor of the height of the OCT B scan
                - sizeXSlo: number of pixels in the width of the IR SLO image
                - sizeYSlo: number of pixels in the height of the IR SLO image
                - scaleXSlo: resolution scaling factor of the width of the IR SLO image
                - scaleYSlo: resolution scaling factor of the height of the IR SLO image
                - fieldSizeSlo: field of view (FOV) of the retina in degrees
                - scanFocus: unknown
                - scanPos: Left or Right eye scanned
                - examTime: Datetime of the scan (needs to be checked)
                - scanPattern: unknown
                - BscanHdrSize: size of B scan header in bytes
                - ID: unknown
                - ReferenceID
                - PID: unknown
                - PatientID: Patient ID string
                - DOB: Date of birth
                - VID: unknown
                - VisitID: Visit ID string
                - VisitDate: Datetime of visit (needs to be checked)
                - GridType: unknown
                - GridOffset: unknown

        """
        return self.wholefile["header"]

    def bScanHeader(self, slicei):
        """
        Retrieve the B Scan header information per slice.

        Args:
            slicei (int): index of B scan

        Returns:
            Dictionary with the following keys
                - startX: x-coordinate for B scan on IR. (see getGrid)
                - startY: y-coordinate for B scan on IR. (see getGrid)
                - endX: x-coordinate for B scan on IR. (see getGrid)
                - endY: y-coordinate for B scan on IR. (see getGrid)
                - numSeg: 2 or 3 segmentation lines for the B scan
                - quality: OCT signal quality
                - shift: unknown

        """
        return self.wholefile["slice-headers"][slicei]

    def saveGrid(self, outfn):
        """
        Saves the grid coordinates mapping OCT Bscans to the IR SLO image to a text file. The text file
        will be a tab-delimited file with 5 columns: The bscan number, x_0, y_0, x_1, y_1 in pixel space
        scaled to the resolution of the IR SLO image.

        Args:
            outfn (str): location of where to output the file

        Returns:
            None

        """
        grid = self.grid
        with open(outfn, "w") as fout:
            fout.write("bscan\tx_0\ty_0\tx_1\ty_1\n")
            ri = 0
            for r in grid:
                r = [ri] + r
                fout.write("%s\n" % "\t".join(map(str, r)))
                ri += 1
