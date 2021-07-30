# This uses ImageMagick to convert HEIC files into jpegs via wand - Imagemagick binding
from os import listdir
from os.path import join, splitext
from wand.image import Image
from PyQt5 import QtCore

#dirPath = input("Enter directory path to HEIC files: ")

def findIMG(dirPath, format):
    if format[0] != ".": # allows for format as ext or .ext
        targExt = "." + format.upper()
    else:
        targExt = format
    try:
        fileList = listdir(dirPath)
    except:
        print("Error - Could not open directory: %s" % dirPath)
        return -1
    iFileList = []
    for iName in fileList:
        root, ext = splitext(iName)
        if ext.upper() == targExt:
            iFileList.append(iName)
    if not len(iFileList):
        print("Error - No HEIC files found in %s" % dirPath)
        return -1
    else:
        iDict = {"input":{"path":dirPath,
                         "files":iFileList
                         }}
        return iDict

def makeOutPath(fileDict, ext, oPath=None, android=False):
    oFileList =[]
    if ext[0] != ".": # allows for ext as jpg or .jpg
        ext = "." + ext.lower()
    if oPath == None: # if oPath not specified, assumed same as input path
        oPath = fileDict["input"]["path"]
    for iFile in fileDict["input"]["files"]: # assembles only roots at this point
        if not android:
            root, trash = splitext(iFile) # returns (root, ext) of iFile, only using root
        elif android:
            iImgPath =join(fileDict["input"]["path"],iFile)
            with Image(filename=iImgPath) as iImg:
                root = toAndroidFilename(iImg.metadata.items())
        oFileList.append(root) # at this point root without ext
    if android: # we need to find and resolve duplicate roots as these will become duplicate filenames
        pntr = 0
        lenOList = len(oFileList)
        while pntr < lenOList:
            cnt = 0
            curRoot = oFileList[pntr]
            pntr += 1
            for i in range(pntr, lenOList):
                if oFileList[i] == curRoot:
                    oFileList[i] = oFileList[i]+"("+str(cnt)+")"
                    cnt += 1
    for i in range(lenOList):
        oFileList[i] = oFileList[i]+ext
    fileDict["output"] = {"path":oPath,
                       "files":oFileList}
    return fileDict

def bulkConvertImgs(fileDict):
    iPath = fileDict["input"]["path"]
    iFiles = fileDict["input"]["files"]
    oPath = fileDict["output"]["path"]
    oFiles = fileDict["output"]["files"]
    for iF, oF in zip(iFiles,oFiles):
        iImgPath = join(iPath,iF)
        oImgPath = join(oPath,oF)
        convertImg(iImgPath,oImgPath)

def genIOList(fileDict):
    IOList = []
    iPath = fileDict["input"]["path"]
    iFiles = fileDict["input"]["files"]
    oPath = fileDict["output"]["path"]
    oFiles = fileDict["output"]["files"]
    for iF, oF in zip(iFiles,oFiles):
        iImgPath = join(iPath,iF)
        oImgPath = join(oPath,oF)
        IOList.append((iImgPath, oImgPath))
    return IOList

def toAndroidFilename(metadata):
    EXIFKEY = "exif:DateTime"
    mdDict = {k:v for k, v in metadata}
    if (EXIFKEY in mdDict.keys() and len(mdDict[EXIFKEY]) == 19):
        dateTime = mdDict[EXIFKEY]
        date, time = dateTime.split()
        YYYY, MM, DD = date.split(":")
        hh, mm, ss = time.split(":")
        return YYYY + MM + DD + "_" + hh + mm + ss
    else:
        print("Error: Couldn't find DateTime key in exif data")
        return -1

def convertImg(iImgPath,oImgPath):
    oFormat = splitext(oImgPath)[1][1:] #spltext returns root, ext; we only care about ext
    iImg = Image(filename=iImgPath)
    with iImg.convert(oFormat) as oImg:
         if oFormat.lower() == "pdf":
            oImg.transform_colorspace("srgb")
         oImg.save(filename=oImgPath)
         print("Successfully converted %s to %s" % (iImgPath,oImgPath))

class ConvertWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    def __init__(self, iImgPath, oImgPath):
        super().__init__()
        self.iImgPath = iImgPath
        self.oImgPath = oImgPath

    @QtCore.pyqtSlot()
    def convertImg(self):
        oFormat = splitext(self.oImgPath)[1][1:]  # spltext returns root, ext; we only care about ext
        print("Started Conversion of %s to %s" % (self.iImgPath,self.oImgPath))
        iImg = Image(filename=self.iImgPath)
        with iImg.convert(oFormat) as oImg:
            if oFormat.lower() == "pdf":
                oImg.transform_colorspace("srgb")
            oImg.save(filename=self.oImgPath)
            print("Successfully converted %s to %s" % (self.iImgPath, self.oImgPath))
        self.finished.emit()


# inputFiles = findIMG(dirPath,"jpg")
# completeDict = makeOutPath(inputFiles,"gif", "C:\\Users\\TV\\Desktop\\output", True)
# bulkConvertImgs(completeDict)
