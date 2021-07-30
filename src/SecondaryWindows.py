from PyQt5 import QtWidgets

class BrowseDialog(QtWidgets.QDialog):

    def __init__(self):
        super().__init__()

    def dialog(self, curPath):
        super().__init__()
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory", curPath)
        if not len(path): # If cancel selected returns empty string
            path = curPath
        return path