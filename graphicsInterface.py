# -*- coding: utf-8 -*
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import sys
import time
import serial
import serial.tools.list_ports

if sys.platform=="darwin":
    pass
else:
	QTextCodec.setCodecForTr(QTextCodec.codecForName("utf8"))

class findReplaceText(QDialog):
    def __init__(self,parent=None):
        super(findReplaceText,self).__init__(parent) 
        self.setWindowFlags(Qt.WindowCloseButtonHint)#HelpButtonHint?
        self.setWindowTitle("Find&Replace")
        self.setWindowIcon(QIcon(':/logo.png')) 
        self.setStyleSheet("""QDialog{background-color: rgb(236, 236, 236);color:black;}
                           QPushButton{background-color:rgb(253,97,72);color:white;}
                           QPushButton:hover{background-color:rgb(212,212,212);color:black;}
                           """)
        self.findedit=QLineEdit()
        self.findButton=QPushButton(self.tr("find"))
        self.replaceStartEdit=QLineEdit()
        self.replaceToEdit=QLineEdit()
        self.replaceButton=QPushButton(self.tr("replace"))
        self.msg=QLabel(self.tr("To"))

        self.layout=QGridLayout()
        self.layout.addWidget(self.findedit,0,0,1,3)
        self.layout.addWidget(self.findButton,0,3)
        self.layout.addWidget(self.replaceStartEdit,1,0)
        self.layout.addWidget(self.msg,1,1)
        self.layout.addWidget(self.replaceToEdit,1,2)
        self.layout.addWidget(self.replaceButton,1,3)

        self.setLayout(self.layout)

class saveUntitled(QDialog):
    def __init__(self,parent=None):
        super(saveUntitled,self).__init__(parent)
        self.setWindowFlags(Qt.WindowCloseButtonHint)#HelpButtonHint?
        self.setWindowTitle("save at your workSpace")
        self.resize(400,80)
        self.setWindowIcon(QIcon(':/logo.png')) 

        self.setStyleSheet("""QDialog{background-color: rgb(236, 236, 236);color:black;}
                           QPushButton{background-color:rgb(253,97,72);color:white;}
                           """)
                                
        self.saveFileLabel=QLabel(self.tr("Input file name"))
        self.saveFileTextedit=QLineEdit()
                                
        self.saveFileWidget=QWidget()
                                
        self.okButton=QPushButton(self.tr("ok"))
        self.cancelButton=QPushButton(self.tr("cancel"))
                                
        saveFileLayout=QGridLayout(self.saveFileWidget)
                                
        saveFileLayout.addWidget(self.saveFileLabel,0,0)
        saveFileLayout.addWidget(self.saveFileTextedit,0,1)
        saveFileLayout.addWidget(self.okButton,1,0)
        saveFileLayout.addWidget(self.cancelButton,1,1)
        self.saveFileWidget.hide()
        self.setLayout(saveFileLayout)
                                
        self.connect(self.okButton,SIGNAL("clicked()"),self.saveFileEditOk)
        self.connect(self.cancelButton,SIGNAL("clicked()"),self.saveFileEditCancle)
                        
    def saveFileEditOk(self):
        self.close()
                
    def saveFileEditCancle(self):
        self.close()

class treeRightClickRename(QDialog):
    def __init__(self,parent=None):
        super(treeRightClickRename,self).__init__(parent)
        self.setWindowFlags(Qt.WindowCloseButtonHint)#HelpButtonHint?
        self.setWindowTitle("Rename as")
        self.setWindowIcon(QIcon(':/logo.png'))
        self.setStyleSheet("""QDialog{background-color: rgb(236, 236, 236);color:black;}
                           QPushButton{background-color:rgb(253,97,72);color:white;}
                           """)

        self.nameLabel=QLabel(self.tr("new name:"))
        self.nameLineEdit=QLineEdit()

        self.okButton=QPushButton(self.tr("ok"))
        self.cancelButton=QPushButton(self.tr("cancel"))


        self.connect(self.okButton,SIGNAL("clicked()"),self.renameOk)
        self.connect(self.cancelButton,SIGNAL("clicked()"),self.renameCancel)

        layout=QGridLayout()
        layout.addWidget(self.nameLabel,0,0)
        layout.addWidget(self.nameLineEdit,0,1)
        layout.addWidget(self.okButton,1,0)
        layout.addWidget(self.cancelButton,1,1)
        self.setLayout(layout)


    def renameOk(self):
        self.close()
    def renameCancel(self):
        self.close()

class createBoardNewDirName(QDialog):
    def __init__(self,parent=None):
        super(createBoardNewDirName,self).__init__(parent)
        self.setWindowFlags(Qt.WindowCloseButtonHint)#HelpButtonHint?
        self.setWindowTitle("boardDirName")
        self.setWindowIcon(QIcon(':/logo.png'))
        self.setStyleSheet("""QDialog{background-color: rgb(236, 236, 236);color:black;}
                           QPushButton{background-color:rgb(253,97,72);color:white;}
                           """)
        self.resize(200,80)
        self.nameLabel=QLabel(self.tr("Input Dir Name"))
        self.nameLineEdit=QLineEdit()

        self.nameWidget=QWidget()
        self.okButton=QPushButton(self.tr("ok"))
        self.cancelButton=QPushButton(self.tr("cancel"))

        layout=QGridLayout(self.nameWidget)
        layout.addWidget(self.nameLabel,0,0)
        layout.addWidget(self.nameLineEdit,0,1)
        layout.addWidget(self.okButton,1,0)
        layout.addWidget(self.cancelButton,1,1)
        self.nameWidget.hide()
        self.setLayout(layout)

        self.connect(self.okButton,SIGNAL("clicked()"),self.nameEditOk)
        self.connect(self.cancelButton,SIGNAL("clicked()"),self.nameEditCancel)

    def nameEditOk(self):
        self.close()
    def nameEditCancel(self):
        self.close()


class SerialWidget(QWidget):
    def __init__(self,parent=None):
        super(SerialWidget,self).__init__(parent)  
        
        serialBaund=QLabel("baud")
        self.baundComboBox=QComboBox()
        self.baundComboBox.addItems(['100','300','600','1200','2400','4800','9600','14400','19200','38400','56000','57600','115200','128000','256000'])
        self.baundComboBox.setCurrentIndex(12)

        serialBytesize=QLabel("bytesize")
        self.bytesizeComboBox=QComboBox()
        self.bytesizeComboBox.addItems(['5','6','7','8'])
        self.bytesizeComboBox.setCurrentIndex(3)
		
        serialParity=QLabel("parity")
        self.parityComboBox=QComboBox()
        self.parityComboBox.addItems(['NONE','EVEN','ODD','MARK','SPACE'])
        self.parityComboBox.setCurrentIndex(0)
        
        #serialTimeout

        serialStopbits=QLabel("stopbits")
        self.stopbitsComboBox=QComboBox()
        self.stopbitsComboBox.addItems(['1','1.5','2'])
        self.stopbitsComboBox.setCurrentIndex(0)

        self.okButton=QPushButton(self.tr("ok"))
        self.cancelButton=QPushButton(self.tr("cancel"))
		
        self.detailWidget=QWidget()
        detailLayout=QGridLayout(self.detailWidget)
        detailLayout.addWidget(serialBaund,0,0)
        detailLayout.addWidget(self.baundComboBox,0,1)
        detailLayout.addWidget(serialBytesize,1,0)
        detailLayout.addWidget(self.bytesizeComboBox,1,1)

        detailLayout.addWidget(serialStopbits,2,0)
        detailLayout.addWidget(self.stopbitsComboBox,2,1)

        detailLayout.addWidget(serialParity,3,0)
        detailLayout.addWidget(self.parityComboBox,3,1)
		
        detailLayout.addItem(QSpacerItem(200,200),4,0)
        self.setLayout(detailLayout)
        
        self.ser=serial.Serial()
    def Port_List(self):
        Com_List=[]
        port_list = list(serial.tools.list_ports.comports())
        for port in port_list:
            Com_List.append(port[0])
        return Com_List
    def comChooseOk(self,com):
        self.ser.port=com
        self.ser.baudrate = self.baundComboBox.currentText()
        self.ser.bytesize = int(self.bytesizeComboBox.currentText())
      
        ParityValue = self.parityComboBox.currentText()
        self.ser.parity = ParityValue[0]
        self.ser.stopbits = int(self.stopbitsComboBox.currentText())
        self.ser.timeout=0.001
        self.ser.flow="N"
        self.ser.open()

class LanLocWidget(QWidget):
    def __init__(self,parent=None):
        super(LanLocWidget,self).__init__(parent)  
               
        languageLabel=QLabel(self.tr("Language"))
        self.languageComBox=QComboBox()
        self.languageComBox.addItems(['English'])
        self.languageComBox.setCurrentIndex(0)
    
        locationLabel=QLabel(self.tr("Location"))
        self.locationComboBox=QComboBox()
        self.locationComboBox.addItems(['China Mainland','Others'])
        self.locationComboBox.setCurrentIndex(0)

        self.detailWidget=QWidget()
        detailLayout=QGridLayout(self.detailWidget)
        detailLayout.addWidget(languageLabel,0,0)
        detailLayout.addWidget(self.languageComBox,0,1)
        detailLayout.addWidget(locationLabel,1,0)
        detailLayout.addWidget(self.locationComboBox,1,1)
        detailLayout.addItem(QSpacerItem(200,200),2,0)
        self.setLayout(detailLayout)

class updateConfig(QWidget):
    def __init__(self,parent=None):
        super(updateConfig,self).__init__(parent)

        checkFirmware=QLabel(self.tr("CheckFirmware"))
        self.checkBinComBox=QComboBox()
        self.checkBinComBox.addItems(['check update','no check'])
        self.checkBinComBox.setCurrentIndex(0)

        self.detailWidget=QWidget()
        detailLayout=QGridLayout(self.detailWidget)
        detailLayout.addWidget(checkFirmware,0,0)
        detailLayout.addWidget(self.checkBinComBox,0,1)

        detailLayout.addItem(QSpacerItem(200,200),1,0)
        self.setLayout(detailLayout)
  
class Preferences(QDialog):
    def __init__(self,parent=None):
        super(Preferences,self).__init__(parent)
        self.setWindowFlags(Qt.WindowCloseButtonHint)#HelpButtonHint?
        self.setStyleSheet("""QDialog{background-color: rgb(236, 236, 236);color:black;}
                           """)
        self.widget=QWidget()
        layout=QGridLayout(self.widget)

        self.landlocation=LanLocWidget(self)
        self.configUpdate=updateConfig()
        
        tabWidget=QTabWidget()
        tabWidget.setTabPosition(QTabWidget.North);
        tabWidget.addTab(self.configUpdate,"config")
        tabWidget.addTab(self.landlocation,"Languare Location")
        tabWidget.addTab(SerialWidget(self),"Serial")
        
        layout.addWidget(tabWidget,1,0)
        self.setLayout(layout)
        self.resize(300,200)
        self.setWindowTitle("Preferences")
        self.setWindowIcon(QIcon(':/logo.png'))
