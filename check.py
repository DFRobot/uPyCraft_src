# -*- coding: utf-8 -*
import sys
import threading
import time
import os
import json
from urllib import request
import platform
import socket
import zipfile


from PyQt4.QtCore import *
from PyQt4.QtGui import *

nowIDEVersion      ="0.30"
nowExamplesVersion="v0.0"
rootDirectoryPath  =os.path.expanduser("~")
rootDirectoryPath  =rootDirectoryPath.replace("\\","/")

class checkVersionExampleFire(QThread):
    def __init__(self,parent):
        super(checkVersionExampleFire,self).__init__(parent)
        self.ui=parent
        
        self.updateSize=0

        self.per=0
        self.runStep=""
        self.url=""
        self.downpath=""
        self.isDownload=False
        self.nowDownload=""
        self.reDownloadNum=0
        self.downloadOk=False
        self.status=404

        self.connect(self.ui,SIGNAL("exitCheckThread"),self.exitCheckThread)
        
    def run(self):
        global nowExamplesVersion
        
        if os.path.exists("%s/AppData/Local/uPyCraft/examples/info.json"%rootDirectoryPath)==True:
            myfile=open("%s/AppData/Local/uPyCraft/examples/info.json"%rootDirectoryPath,"r")
            jsonMsg=myfile.read()
            myfile.close()
            jsonMsg=json.loads(jsonMsg)
            nowExamplesVersion=jsonMsg["version"]

        checkUpdateUrl=""
        if os.path.exists("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath)==True:
            myfile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
            jsonMsg=myfile.read()
            myfile.close()
            jsonDict=eval(jsonMsg)

            checkUpdateUrl=jsonDict['updateURL']

        page=""
        if checkUpdateUrl=="":
            self.exit()
            return

        try:
            self.status=request.urlopen(checkUpdateUrl).code
        except:
            self.status=404
        print(self.status)
        if self.status==404:
            self.exit()
            return
        else:
            res=request.urlopen(checkUpdateUrl)
            page=res.read().decode()
            print(page)
            myfile = open("%s/AppData/Local/uPyCraft/update.json"%rootDirectoryPath,"w")
            myfile.write(page)
            myfile.close()

            self.emit(SIGNAL("changeIsCheckFirmware"),True)
                
            self.system = platform.system()#system check
            
            print(self.system)
            print(nowIDEVersion)
            print(nowExamplesVersion)

            if page=="":
                self.exit()
                return
            jsonmsg=json.loads(page)

            self.ideList = jsonmsg['IDE']
            self.firmwareList = jsonmsg['firmware']
            self.examplesList = jsonmsg['examples']

            self.emit(SIGNAL("changeUpdateFirmwareList"),self.firmwareList)

            self.connect(self.ui,SIGNAL("confirmUpdata"),self.confirmUpdata)
            
            #IDE
            if self.ideList[0]["version"]>nowIDEVersion:
                print("ide has new version")
                self.isDownload=True
                self.emit(SIGNAL("updateThing"),"update uPyCraft IDE","There is a new version available for uPyCraft, would you like to upgrade now?")
            else:
                #examples
                if self.examplesList[0]["version"]>nowExamplesVersion:
                    print("examples has new version")
                    self.isDownload=True
                    self.emit(SIGNAL("updateThing"),"update uPyCraft Examples","There is a new version available for EXAMPLES, would you like to upgrade now?")
        while 1:
            if self.isDownload==True:
                if self.nowDownload=="":
                    time.sleep(0.1)
                elif self.nowDownload == "IDE":
                    self.nowDownload=""
                    self.reDownloadNum=0
                    self.reDownload()
                    if self.downloadOk==False:
                        self.isDownload=False
                        break
                    #print("111111111222222222")
                    #QMessageBox.information(self.ui,self.tr("attention"),self.tr("Please delete the old edition and use the updated one."),QMessageBox.Ok)
                    #print("222222222222223333")
                    if self.examplesList[0]["version"]>nowExamplesVersion:
                        print("examples has new version")
                        self.emit(SIGNAL("updateThing"),"update uPyCraft Examples","There is a new version available for EXAMPLES, would you like to upgrade now?")
                    else:
                        self.isDownload=False
                elif self.nowDownload == "Examples":
                    self.nowDownload=""
                    self.reDownloadNum=0
                    self.reDownload()
                    if self.downloadOk==False:
                        self.isDownload=False
                        break
                    if self.per==100:
                        f=zipfile.ZipFile(self.downpath,"r")
                        for afile in f.namelist():
                            f.extract(afile,"%s/AppData/Local/uPyCraft"%rootDirectoryPath)
                        f.close()
                        self.emit(SIGNAL("reflushExamples"))
                    self.isDownload=False     
            else:
                break
        self.exit()

    def exitCheckThread(self):
        self.exit()

    def reDownload(self):
        if self.reDownloadNum==3:
            self.downloadOk=False
            self.emit(SIGNAL("updatePer"),-1)
            return 
        try:
            socket.setdefaulttimeout(3)
            request.urlretrieve(self.url,self.downpath,self.cbkUpdate)
            self.downloadOk=True 
            return
        except:
            print("urllib err :%s"%self.url)
            self.reDownloadNum+=1
            self.reDownload()
        

    def confirmUpdata(self,gotoUpdata):
        if gotoUpdata=="IDE":
            self.idenameList = str(self.ideList[0][self.system]["url"]).split("/")
            self.updateSize=self.ideList[0][self.system]["size"]
            self.url=self.ideList[0][self.system]["url"]
            self.downpath=self.idenameList[-1]
            self.nowDownload="IDE"
        elif gotoUpdata=="IDEcancel":
            if self.examplesList[0]["version"]>nowExamplesVersion:
                print("examples has new version")
                self.emit(SIGNAL("updateThing"),"update uPyCraft Examples","There is a new version available for EXAMPLES, would you like to upgrade now?")
            else:
                self.isDownload=False
        elif gotoUpdata=="Examples":
            self.url = self.examplesList[0]["url"]
            examplesNameList = str(self.url).split("/")
            self.updateSize=self.examplesList[0]["size"]
            self.downpath="%s/AppData/Local/uPyCraft/download/%s"%(rootDirectoryPath,examplesNameList[-1])
            self.nowDownload="Examples"
        elif gotoUpdata=="Examplescancel":
            self.isDownload=False


    def cbkUpdate(self,blocknum,blocksize,totalsize):
        self.per=100.0*blocknum*blocksize/self.updateSize
        if self.per>=100:
            self.per=100
            self.emit(SIGNAL("updatePer"),self.per)
            return
            
        self.emit(SIGNAL("updatePer"),self.per)

class attentionUpdata(QDialog):
    def __init__(self,title,labelmsg,parent=None):
        super(attentionUpdata,self).__init__(parent)
        self.setWindowTitle(title)
        
        self.setWindowIcon(QIcon(':/logo.png'))

        self.okButton=QPushButton(self.tr("ok"))
        self.cancelButton=QPushButton(self.tr("cancel"))

        self.label=QLabel(self.tr(labelmsg))
        #self.label.setFixedSize(400, 80)
        self.label.setWordWrap(True)
        self.label.adjustSize()

        self.detailWidget=QWidget()
        layout = QGridLayout(self.detailWidget)
        layout.addWidget(self.label,0,0,1,3)
        layout.addWidget(self.okButton,1,0)
        layout.addWidget(self.cancelButton,1,3)

        self.setLayout(layout)
        self.setFixedSize(500, 100)
        self.connect(self.okButton,SIGNAL("clicked()"),self.chooseOk)
        self.connect(self.cancelButton,SIGNAL("clicked()"),self.chooseCancel)
        
    def chooseOk(self):
        self.close()

    def chooseCancel(self):
        self.close()


class ProgressIDEorExampleBar(QDialog):
    def __init__(self, windowname,parent=None):
        super(ProgressIDEorExampleBar,self).__init__(parent)
        self.pbar = QProgressBar(self)
        detailLayout=QGridLayout()
        detailLayout.addWidget(self.pbar)
        self.setLayout(detailLayout)
        self.setWindowTitle(windowname)
        self.setWindowIcon(QIcon(':/logo.png'))
        self.resize(300,150)
        
    def timerEvent(self, per):
        if per >= 100:
            return
        self.pbar.setValue(per)










        
