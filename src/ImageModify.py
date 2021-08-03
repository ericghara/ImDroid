# This uses ImageMagick to convert HEIC files into jpegs via wand - Imagemagick binding
from os import listdir
from os.path import join, splitext, split
from wand.image import Image
from PyQt5 import QtCore
from time import perf_counter
from inspect import currentframe


def timer(func):
    def wrapper(*args):
        start = perf_counter()
        output = func(*args)
        run_time = perf_counter() - start
        print(f"Finished {func.__name__!r} in {run_time:.4f} secs\n")
        return output

    return wrapper


global rootKEY, extKEY, opKEY
rootKEY = "name"
extKEY = "extension"
opKEY = "out path"


class ImgFind:

    def __init__(self):
        global Boss
        super().__init__()
        Boss = ConvertBoss()
        self.IO_dict = {}
        self.env = {}

    def formatToExt(self, frmt):
        if frmt[0] != ".":  # allows for format as ext or .ext
            ext = "." + frmt.upper()
        else:
            ext = frmt.upper()
        return ext

    def convert(self, iPath, iFormat, oPath, oFormat, android=True):
        self.IO_dict[iPath] = {}
        imgDict = self.findImg(iPath, iFormat)
        for iFile in imgDict[iPath].keys():
            outDict = self.makeOutDict(oPath, oFormat, iFile, android)
            self.IO_dict[iPath][iFile] = outDict
        #environment
        for k, v in self.findImg(oPath, oFormat).items():
            self.env[k] = v
        Boss.addToQueue(self.IO_dict)
        self.IO_dict = {}
        if Boss.isIdle:
            Boss.assignThreads()
        #print("%d Pictures added to queue" % len(IO_list))

    @timer
    def findImg(self, dirPath, frmt):
        #returns {dirPath: {File0: {}, File1: {}...}
        if type(frmt) == list or type(frmt) == tuple:
            extList = [self.formatToExt(f) for f in frmt]
        elif type(frmt) == str:
            extList = [self.formatToExt(frmt)]
        else:
            print("Error %r: %r not a valid format" % (currentframe().f_code.co_name, frmt))
            return -1
        try:
            fileList = listdir(dirPath)
        except Exception:
            print("Error - Could not open directory: %s" % dirPath)
            return -1
        iFileDict = {}
        for iName in fileList:
            root, ext = splitext(iName)
            if ext.upper() in extList:
                iFileDict[iName] = {}
        imgDict = {dirPath: iFileDict}
        return imgDict

    @timer
    def makeOutDict(self, oPath, oFormat, iFile, android=False):
        fileDict = {}
        if android:
            fRoot = None
        else:
            fRoot, trash = splitext(iFile)  # returns (fRoot, ext) of iFile, only using fRoot
        fileDict[opKEY] = oPath
        fileDict[extKEY] = self.formatToExt(oFormat)
        fileDict[rootKEY] = fRoot
        return fileDict

class ConvertBoss:
    def __init__(self):
        super().__init__()
        self.thrdPool = []  # List of worker threads
        self.workers = []  # list of worker objects
        self.queue = {}  # queue of files to convert
        self.MAXTHREADS = QtCore.QThread.idealThreadCount()

    def addToQueue(self, _dict):
        for dir, fDict in _dict.items():
            if dir not in [*self.queue.keys()]:
                self.queue[dir] = fDict
            else:
                for f, oDict in fDict.items():
                    if f in self.queue[dir].keys():
                        print("Error %r: %s/%s already in conversion queue" % (currentframe().f_code.co_name, dir,f))
                    else:
                        self.queue[dir][f] = oDict

    def isIdle(self):
        return len(self.workers) == 0

    def findIdleThreads(self):
        # Failure to add deadline leads to a deadlock/starvation of threads.
        # Without deadline, trd.wait() will indefinitely wait for threads to
        # finish, meanwhile blocking trd.quit() commands from the very threads
        # it's waiting on *facepalm*
        return [thrd for thrd in self.thrdPool if thrd.wait(1)]

    def queueEmpty(self):
        if len([*self.queue.keys()])>0:
            return False
        else:
            return True
    def queuePop(self):
        #always run queueEmpty before queuePop
        pathList = [*self.queue.keys()]
        iPath = pathList[0]
        fList = [*self.queue[iPath].keys()]
        if len(fList) > 0:
            iFile = fList.pop(-1)
            outDict = self.queue[iPath].pop(iFile)
        else: #we were given an empty dir by user
            self.queue.pop(iPath)
            return iPath, False
        if len(fList) == 0: # clear a depleted path from queue
            self.queue.pop(iPath)
        iImgPath = join(iPath,iFile)
        return iImgPath, outDict

    @QtCore.pyqtSlot()
    def assignThreads(self,trd=None):
        idleList = self.findIdleThreads()
        while self.queueEmpty() == False:
                if len(idleList) > 0:
                    trd = idleList.pop()
                elif len(self.thrdPool) < self.MAXTHREADS: # Next consider making new threads
                    trd = QtCore.QThread()
                    self.thrdPool.append(trd)
                else:
                    # Won't be able to clear queue with available threads
                    # Will be called by stop thread when next thread clears
                    break
                iImgPath, outDict = self.queuePop()
                if outDict is False: #ConvertBoss was probably given an empty dir
                    print("Warning %r: %s contains no image files" % (currentframe().f_code.co_name, iImgPath))
                    self.assignThreads()
                    break
                self.startThread(trd, iImgPath, outDict)

    @QtCore.pyqtSlot()
    def startThread(self, trd, iImgPath, outDict):
            wkr = ConvertWorker(iImgPath,outDict)
            wkr.moveToThread(trd)
            wkr.finished.connect(lambda: self.stopThread(trd, wkr))
            trd.started.connect(wkr.convertImg)
            trd.finished.connect(wkr.deleteLater)
            trd.start()
            self.workers.append(wkr)

    @QtCore.pyqtSlot()
    def stopThread(self, trd, wkr):
        wIdx = self.workers.index(wkr)
        del self.workers[wIdx]
        trd.quit()
        trd.wait(1500) # Waits for thread to become ready
        self.assignThreads()
        #print("Stopped thread #%d: %r" % (self.threads.index(trd),trd.wait(QtCore.QDeadlineTimer(50))))


class ConvertWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    def __init__(self, iImgPath, outDict):
        super().__init__()
        self.iImgPath = iImgPath
        self.oRoot = outDict[rootKEY]
        self.oPath = outDict[opKEY]
        self.oExt = outDict[extKEY]

    @QtCore.pyqtSlot()
    def convertImg(self):
        oFormat = self.oExt[1:] # remove period from ext
        try:
            iImg = Image(filename=self.iImgPath)
        except Exception:
            print("Error %r: %s could not be opened.  This file will be skipped." % (currentframe().f_code.co_name, self.iImgPath))
            self.finished.emit()
            return -1
        if self.oRoot is None:
            self.oRoot = self.toAndroidRoot(iImg.metadata.items())
            if self.oRoot == -1:
                print("Warning %r: %s could not find exif:DateTime. Preserving original filename." % (currentframe().f_code.co_name, self.iImgPath))
                self.oRoot = self.preserveRoot()
        oImgPath = self.makeImgPath(self.oPath, self.oExt, self.oRoot)
        print("Started Conversion of %s to %s" % (self.iImgPath, oImgPath))
        with iImg.convert(oFormat) as oImg:
            if oFormat.lower() == "pdf":
                oImg.transform_colorspace("srgb")
            oImg.save(filename=oImgPath)
            print("Successfully converted %s to %s" % (self.iImgPath, oImgPath))
        self.finished.emit()

    @QtCore.pyqtSlot()
    def preserveRoot(self):
        iFilename = split(self.iImgPath)[1]
        iRoot = splitext(iFilename)[0]
        return iRoot

    @QtCore.pyqtSlot()
    def toAndroidRoot(self, metadata):
        EXIFKEY = "exif:DateTime"
        mdDict = {k: v for k, v in metadata}
        if (EXIFKEY in mdDict.keys() and len(mdDict[EXIFKEY]) == 19):
            dateTime = mdDict[EXIFKEY]
            date, time = dateTime.split()
            YYYY, MM, DD = date.split(":")
            hh, mm, ss = time.split(":")
            return YYYY + MM + DD + "_" + hh + mm + ss
        else:
            print("Error: Couldn't find DateTime key in exif data")
            return -1

    @QtCore.pyqtSlot()
    def makeImgPath(self, path, ext, root):
        fileName = root+ext
        imgPath = join(path,fileName)
        return imgPath



