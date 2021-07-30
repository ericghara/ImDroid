import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from pathlib import Path
from src import ImageModify, SecondaryWindows
from time import time #delete later

class AppWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.thrdPool = [] # List of worker threads
        self.workers = [] # list of worker objects
        self.queue = [] # queue of files to convert
        self.MAXTHREADS = QtCore.QThread.idealThreadCount()-1
        self.form = QtWidgets.QWidget()
        self.setCentralWidget(self.form)
        self.layout = QtWidgets.QVBoxLayout(self.form)
        SecWins = SecondaryWindows.BrowseDialog()
        self.widgDict = {"input" : {},
                            "output" : {},
                            "lowerButts" : {}
                         } #IO dict is where button widgets live
        self.HOMEDIR = str(Path.home())
        self.widgTextDict = {"input" : {
                                        "label" : "Source Directory",
                                        "lEdit" : self.HOMEDIR+"\\Desktop\\Test",
                                        "browseButt" : "Browse"
                                       },
                            "output" : {
                                        "label": "Output Directory",
                                        "lEdit": self.HOMEDIR+"\\Desktop\\output",
                                        "browseButt": "Browse"
                                        },
                            "lowerButts" : {
                                            "convertButt" : "Convert!"
                                            }}  #This is where default widget text lives.  Key names need to be the same as widgDict
        for ky in self.widgDict.keys(): # This populates self.form with widgets and layouts
            wDict = {}
            wDict["layout"] = QtWidgets.QHBoxLayout()
            if (ky == "input" or ky == "output"): # create input and output widgets
                wDict["label"] = QtWidgets.QLabel(self.form)
                wDict["lEdit"] = QtWidgets.QLineEdit(self.form)
                wDict["lEdit"].setMinimumWidth(200)
                wDict["browseButt"] = QtWidgets.QPushButton(self.form, objectName=ky+"_browseButt")
                name = wDict["browseButt"].objectName()
                wDict["browseButt"].clicked.connect(lambda: self.browseButtClick())
            elif ky == "lowerButts": # create lower Butts widgets
                wDict["stretch0"] = 1
                wDict["convertButt"] = QtWidgets.QPushButton(self.form)
                wDict["convertButt"].clicked.connect(self.convertButtClick)
            for k, w in wDict.items(): # add widgets, layouts and stretch
                if k == "layout":
                    self.layout.addLayout(w)
                elif "stretch" in k.lower():  # stretch values are just ints.  This departs from everything else whose value is a widget
                    wDict["layout"].addStretch(w)
                else:
                    wDict["layout"].addWidget(w)
            for k,t in self.widgTextDict[ky].items(): # Set widget text
                wDict[k].setText(t)
            self.widgDict[ky] = wDict

    @QtCore.pyqtSlot()
    def convertButtClick(self):
        ANDROID = True
        Mod = ImageModify
        source = self.widgDict["input"]["lEdit"].text()
        dest = self.widgDict["output"]["lEdit"].text()
        inputFiles = Mod.findIMG(source, "jpg")
        IO_Dict = Mod.makeOutPath(inputFiles, "gif", dest, ANDROID)
        IO_list = Mod.genIOList(IO_Dict)
        self.queue[:0] = IO_list # prepend queue
        if len(self.workers)  == 0:
            self.assignThreads()
        print("%d Pictures added to queue" % len(IO_list))

    def browseButtClick(self):
        SecWins = SecondaryWindows.BrowseDialog()
        name = self.sender().objectName()
        ky, trash = name.split("_",1)
        leWidg = self.widgDict[ky]["lEdit"]
        path = SecWins.dialog(leWidg.text())
        if "\\" in self.HOMEDIR: # Dialog returns unix style / even in windows environment
            path = path.replace("/","\\")
        leWidg.setText(path)



    def findIdleThreads(self):
        # Failure to add deadline leads to a deadlock/starvation of threads.
        # Without deadline, trd.wait() will indefinitely wait for threads to
        # finish, meanwhile blocking trd.quit() commands from the very threads
        # it's waiting on *facepalm*
        return [thrd for thrd in self.thrdPool if thrd.wait(1)]

    @QtCore.pyqtSlot()
    def assignThreads(self,trd=None):
        idleList = self.findIdleThreads()
        WL.add(len(idleList), len(self.queue))
        while len(self.queue) > 0: # First use up existing idle threads
            # if len(idleList) > 0:
            #     self.startThread(idleList.pop())
            if len(idleList) > 0:
                trd = idleList.pop()
                self.startThread(trd)
            elif len(self.thrdPool) < self.MAXTHREADS: # Next consider making new threads
                trd = QtCore.QThread()
                self.thrdPool.append(trd)
                self.startThread(trd)
            else:
                # Won't be able to clear queue with available threads
                # Will be called by stop thread when next thread clears
                break

    @QtCore.pyqtSlot()
    def startThread(self, trd):
            i, o = self.queue.pop()
            wkr = ImageModify.ConvertWorker(i,o)
            wkr.moveToThread(trd)
            wkr.finished.connect(lambda: self.stop_thread(trd, wkr))
            trd.started.connect(wkr.convertImg)
            trd.finished.connect(wkr.deleteLater)
            trd.start()
            self.workers.append(wkr)

    @QtCore.pyqtSlot()
    def stop_thread(self, trd, wkr):
        wIdx = self.workers.index(wkr)
        del self.workers[wIdx]
        trd.quit()
        trd.wait(1500) # Waits for thread to become ready
        self.assignThreads()
        #print("Stopped thread #%d: %r" % (self.threads.index(trd),trd.wait(QtCore.QDeadlineTimer(50))))



class WaitList:
    def __init__(self):
        super().__init__()
        self.wList = {}
        self.cnt = 0
        self.epoch = None
        self.numFiles = None

    def add(self, numIdle, numQueued):
        if self.numFiles == None:
            self.numFiles = numQueued
            self.epoch = time()
        self.wList["Times called: "+ str(self.cnt)] ={
            "Processing Time: ": time()-self.epoch, "Number Idle: ":numIdle, "Pictures processed: ": self.numFiles - numQueued}
        self.cnt +=1

    def printIt(self):
        for k, dict in self.wList.items():
            items = str([l+str(v) for l,v in dict.items()]).replace("'","")
            print(k,items.strip("[]"))

if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    app = AppWindow()
    WL = WaitList()
    app.show()
    qapp.exec_()
    WL.printIt() # For some reason this causes a crash on exit but it's only a diagnostic.  Completely unsure why, has something to do with items= line
    print("Workers: %d" % len(app.workers))
    print("Threads: %d" % len(app.thrdPool))




