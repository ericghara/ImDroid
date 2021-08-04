import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from pathlib import Path
from src import ImageModify, SecondaryWindows
from time import time #delete later

class AppWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        global Mod
        Mod = ImageModify.ImgFind()
        self.form = QtWidgets.QWidget()
        QtCore.QMetaObject.connectSlotsByName(self.form)
        self.setCentralWidget(self.form)
        self.layout = QtWidgets.QVBoxLayout(self.form)
        SecWins = SecondaryWindows.BrowseDialog()
        self.widgDict = {"input" : {},
                            "output" : {},
                            "lowerButts" : {}
                         }  #IO dict is where button widgets live
        self.HOMEDIR = str(Path.home())
        self.widgTextDict = {"input" : {
                                        "label" : "Source Directory",
                                        "lEdit" : self.HOMEDIR+"\desktop\\test",
                                        "browseButt" : "Browse",
                                       },
                            "output" : {
                                        "label": "Output Directory",
                                        "lEdit": self.HOMEDIR+"\\desktop\output",
                                        "browseButt": "Browse"
                                        },
                            "lowerButts" : {
                                            "convertButt" : "Convert!"
                                            }}  #This is where default widget text lives.  Key names need to be the same as widgDict
        for ky in self.widgDict.keys():  # This populates self.form with widgets and layouts
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
            for k, w in wDict.items():  # add widgets, layouts and stretch
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
        iExts = ["heic"]
        oExt = "jpg"
        ANDROID = True
        iPath = self.widgDict["input"]["lEdit"].text()
        oPath = self.widgDict["output"]["lEdit"].text()
        Mod.convert(iPath,iExts,oPath,oExt,ANDROID)

    def browseButtClick(self):
        SecWins = SecondaryWindows.BrowseDialog()
        name = self.sender().objectName()
        ky, trash = name.split("_",1)
        leWidg = self.widgDict[ky]["lEdit"]
        path = SecWins.dialog(leWidg.text())
        if "\\" in self.HOMEDIR:  # Dialog returns unix style / even in windows environment
            path = path.replace("/","\\")
        leWidg.setText(path)

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
    #WL.printIt() # For some reason this causes a crash on exit but it's only a diagnostic.  Completely unsure why, has something to do with items= line

