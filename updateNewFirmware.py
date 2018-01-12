# -*- coding: utf-8 -*
import sys
import serial
import serial.tools.list_ports
import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class updateNewFirmwareBar(QDialog):
    def __init__(self,windowname,isErase,isUPY,parent=None):
        super(updateNewFirmwareBar,self).__init__(parent)

        self.setWindowTitle(windowname)
        self.setWindowIcon(QIcon(':/logo.png'))

        self.updateLabel=QLabel(self.tr("Burn"))
        self.updateBar=QProgressBar(self)

        self.isUPY=isUPY
        if isUPY:
            self.downloadLabel=QLabel(self.tr("Download"))
            self.downloadBar=QProgressBar(self)

        self.erasePer=0

        detailLayout=QWidget()
        layout = QGridLayout(detailLayout)
        
        if isErase:
            self.eraseBar=QProgressBar(self)
            self.eraseLabel=QLabel(self.tr("EraseFlash"))
            if self.isUPY==True:
                layout.addWidget(self.downloadLabel,0,0)
                layout.addWidget(self.downloadBar,0,1)
                layout.addWidget(self.eraseLabel,1,0)
                layout.addWidget(self.eraseBar,1,1)
                layout.addWidget(self.updateLabel,2,0)
                layout.addWidget(self.updateBar,2,1)
            else:
                layout.addWidget(self.eraseLabel,0,0)
                layout.addWidget(self.eraseBar,0,1)
                layout.addWidget(self.updateLabel,1,0)
                layout.addWidget(self.updateBar,1,1)
            self.resize(600,150)
        else:
            if self.isUPY==True:
                layout.addWidget(self.downloadLabel,0,0)
                layout.addWidget(self.downloadBar,0,1)
                layout.addWidget(self.updateLabel,1,0)
                layout.addWidget(self.updateBar,1,1)
            else:
                layout.addWidget(self.updateLabel,0,0)
                layout.addWidget(self.updateBar,0,1)
            self.resize(600,100)
            
        self.setLayout(layout)


    def downloadEvent(self,per):
        if per>=100:
            per=100
            self.downloadBar.setValue(per)
            return
        self.downloadBar.setValue(per)

    def eraseEvent(self,per):
        if per>=100:
            per=100
            self.eraseBar.setValue(per)
            return
        self.eraseBar.setValue(per)

    def updateEvent(self,per):
        if per>=100:
            per=100
            self.updateBar.setValue(per)
            self.close()
            return
        self.updateBar.setValue(per)

class updateNewFirmware(QDialog):
    def __init__(self,windowname,isAuto=False,parent=None):
        super(updateNewFirmware,self).__init__(parent)
        self.setWindowTitle(windowname)
        self.setWindowIcon(QIcon(':/logo.png'))
        self.isAuto=isAuto
        if self.isAuto:
            Com_List=[]
            port_list = list(serial.tools.list_ports.comports())
            for port in port_list:
                Com_List.append(port[0])

            self.comLabel=QLabel(self.tr("com"))
            self.comChoose=QComboBox()
            self.comChoose.addItems(Com_List)
	
        self.okButton=QPushButton(self.tr("ok"))
        self.cancelButton=QPushButton(self.tr("cancel"))

        self.boardLabel=QLabel(self.tr("board"))
        self.boardComboBox=QComboBox()
        self.boardComboBox.addItems(["esp8266","esp32","microbit"])
        self.boardComboBox.setCurrentIndex(2)

        self.eraseflashLabel=QLabel(self.tr("erase_flash"))
        self.eraseComboBox=QComboBox()
        self.eraseComboBox.addItems(["yes","no"])
        self.eraseComboBox.setCurrentIndex(1)


        self.myGroupBox  = QGroupBox(self.tr("Firmware Choose"))         

        self.detailWidget=QWidget()
        layout = QGridLayout(self.detailWidget)
        #########
        self.myGroupBox  = QGroupBox(self.tr("Firmware Choose"))
        
        self.myGroupBoxLayout = QGridLayout()
        
        self.firmwareTip=QLabel(self.tr("Firmware Choose"))
        self.radioUPY=QRadioButton("uPyCraft")
        self.radioUser=QRadioButton("Users")
        self.firmwareName=QLineEdit()
        self.chooseFirmwareButton=QPushButton(self.tr("choose"))   

        self.myGroupBoxLayout.addWidget(self.radioUPY,0,0)
        self.myGroupBoxLayout.addWidget(self.radioUser,1,0)
        self.myGroupBoxLayout.addWidget(self.firmwareName,1,1)
        self.myGroupBoxLayout.addWidget(self.chooseFirmwareButton,1,2)

        self.myGroupBox.setLayout(self.myGroupBoxLayout)
        #########

        if isAuto:
            layout.addWidget(self.boardLabel,0,0)
            layout.addWidget(self.boardComboBox,0,2)

            layout.addWidget(self.eraseflashLabel,1,0)
            layout.addWidget(self.eraseComboBox,1,2)

            layout.addWidget(self.comLabel,2,0)
            layout.addWidget(self.comChoose,2,2)

            layout.addWidget(self.myGroupBox,3,0,2,3)

            layout.addWidget(self.okButton,6,0)
            layout.addWidget(self.cancelButton,6,2)
        else:
            layout.addWidget(self.boardLabel,0,0)
            layout.addWidget(self.boardComboBox,0,2)

            layout.addWidget(self.eraseflashLabel,1,0)
            layout.addWidget(self.eraseComboBox,1,2)

            layout.addWidget(self.myGroupBox,2,0,2,3)

            layout.addWidget(self.okButton,5,0)
            layout.addWidget(self.cancelButton,5,2)
            
        self.radioUPY.setChecked(True)
        self.firmwareName.setEnabled(False)
        self.chooseFirmwareButton.setVisible(False)

        if self.boardComboBox.currentText()=="microbit":
            self.eraseComboBox.setCurrentIndex(1)# for erase:0 yes,1 no
            self.eraseComboBox.setEnabled(False)
        else:
            self.eraseComboBox.setEnabled(True)
        self.resize(450,200)
        self.setLayout(layout)

        self.connect(self.okButton,SIGNAL("clicked()"),self.chooseOk)
        self.connect(self.cancelButton,SIGNAL("clicked()"),self.chooseCancel)
        self.connect(self.boardComboBox,SIGNAL("activated(int)"),self.boardChange)
        self.connect(self.radioUPY,SIGNAL("toggled(bool)"),self.radioUPYChanged)
        self.connect(self.radioUser,SIGNAL("toggled(bool)"),self.radioUserChanged)

    def radioUPYChanged(self,choosed):
        if choosed:
            self.firmwareName.clear()
            self.firmwareName.setEnabled(False)
            self.chooseFirmwareButton.setVisible(False)

    def radioUserChanged(self,choosed):
        if choosed:
            self.firmwareName.setEnabled(True)
            self.chooseFirmwareButton.setVisible(True)

        
    def boardChange(self,item):
        print(self.boardComboBox.currentText())
        if self.boardComboBox.currentText()=="microbit":
            self.eraseComboBox.setCurrentIndex(1)# for erase:0 yes,1 no
            self.eraseComboBox.setEnabled(False)
        else:
            self.eraseComboBox.setCurrentIndex(0)
            self.eraseComboBox.setEnabled(True)
            
    def chooseOk(self):
        self.close()

    def chooseCancel(self):
        self.close()


#app=QApplication(sys.argv)  
#main=updateNewFirmware("test")  
#main.show()  
#app.exec_() 
