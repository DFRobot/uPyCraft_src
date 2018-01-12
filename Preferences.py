# -*- coding: utf-8 -*
import sys
import time
import serial
import serial.tools.list_ports

from PyQt4.QtCore import *
from PyQt4.QtGui import *

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
		
        #self.detailWidget.hide()
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
        self.locationComboBox.setCurrentIndex(1)

        self.detailWidget=QWidget()
        detailLayout=QGridLayout(self.detailWidget)
        #detailLayout.addWidget(serialPort,0,0)
        #detailLayout.addWidget(self.portComboBox,0,1)
        detailLayout.addWidget(languageLabel,0,0)
        detailLayout.addWidget(self.languageComBox,0,1)
        detailLayout.addWidget(locationLabel,1,0)
        detailLayout.addWidget(self.locationComboBox,1,1)
        #self.detailWidget.hide()
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
        self.widget=QWidget()
        layout=QGridLayout(self.widget)

        self.landlocation=LanLocWidget(self)
        self.configUpdate=updateConfig()
        
        tabWidget=QTabWidget()
        tabWidget.setTabPosition(QTabWidget.West);
        tabWidget.addTab(SerialWidget(self),"Serial")
        tabWidget.addTab(self.landlocation,"Languare Location")
        tabWidget.addTab(self.configUpdate,"config")
        layout.addWidget(tabWidget,1,0)
        self.setLayout(layout)
        self.resize(300,200)
        self.setWindowTitle("Preferences")
        self.setWindowIcon(QIcon(':/logo.png')) 

