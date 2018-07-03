#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import threading
import json

from PyQt4.QtCore import *
from PyQt4.QtGui import *

rootDirectoryPath  =os.path.expanduser("~")
rootDirectoryPath  =rootDirectoryPath.replace("\\","/")
currentTempPath="%s/AppData/Local/uPyCraft/temp/"%rootDirectoryPath

class ctrlAction(QThread):
    def __init__(self,readWriteUart,readWriteQueue,ctrltouiQueue,parent):
        super(ctrlAction,self).__init__(parent)
        self.readWriteUart=readWriteUart
        self.ui = parent
        self.currentBoard="esp32"
        self.connect(self.ui,SIGNAL("changeCurrentBoard"),self.changeCurrentBoard)
        self.ctrltouiQueue=ctrltouiQueue
        self.ctrltouartQueue=readWriteQueue
        self.rootDir=""
        self.connect(self.readWriteUart,SIGNAL("ctrlRecvUartMsg"),self.ctrlRecvUartMsg)
        self.clear()

        self.recvAllData=""
        self.dragDropModel=False
        self.connect(self.ui,SIGNAL("changeDragDropModel"),self.changeDragDropModel)

    def run(self):
        while True:
            msg=self.ctrltouiQueue.get()
            msg=msg.split(":::")

            if msg[0]=="treeModel":
                self.treeModel()
                
            elif msg[0]=="dropdownfile":
                self.dropDownFileName=msg[1]
                self.downloadFile(msg[2])
                pass
            elif msg[0]=="downloadfile":
                self.downloadFile(msg[1])
                pass
            elif msg[0]=="loadfile":
                self.loadFile(msg[1])
                pass
            elif msg[0]=="dragChangeDir":
                self.dragChangeDir(msg[1],msg[2])
                pass
            elif msg[0]=="goprogram":
                self.goProgram(msg[1])
                pass
            elif msg[0]=="intofunc":
                #self.intoFunc(msg[1])
                pass
            elif msg[0]=="deleteboardfile":
                self.deleteFile(msg[1])
                pass
            elif msg[0]=="setdefaultprogram":
                self.setDefaultProg(msg[1])
                pass
            elif msg[0]=="checkFirmware":
                self.checkFirmware()
                pass
            elif msg[0]=="createnewdir":
                self.createNewDir(msg[1],msg[2])
                pass
            elif msg[0]=="rename":
                self.rename(msg[1],msg[2])
                pass
            elif msg[0]=="getcwd":
                self.getcwd()
                pass
            elif msg[0]=="importOs":
                self.importUos()
                pass
            elif msg[0]=="close":
                break
            elif msg[0]=="clear":
                self.clear()
                pass

        self.exit()

    def changeDragDropModel(self,model):
        self.dragDropModel=model

    def changeCurrentBoard(self,board):
        self.currentBoard=board

    def clear(self):
        self.importUosMsg      = ""
        self.getcwdMsg         = ""
        self.reflushTreeMsg    = ""
        self.loadFileMsg       = ""
        self.deleteFileMsg     = ""
        self.downloadFileMsg   = ""
        self.dropDownFileMsg   = ""
        self.checkFirmwareMsg  = ""
        self.renameMsg         = ""
        self.createNewDirMsg   = ""
        self.setDefaultProgMsg = ""
        self.downFileFalseMsg  = ""
        self.intoFuncMsg       = ""

        self.importUosBool     = False
        self.getcwdBool        = False
        self.reflushTreeBool   = False
        self.loadFileBool      = False
        self.deleteFileBool    = False
        self.downloadFileBool  = False
        self.checkFirmwareBool = False
        self.renameBool        = False
        self.createNewDirBool  = False
        self.setDefaultProgBool= False
        self.downFileFalseBool = False
        self.intoFuncBool      = False

    def importUos(self):
        self.importUosBool = True
        self.importUosMsg = ""
        if self.currentBoard=="microbit":
            aline="import os\r"
            for i in aline:
                self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                time.sleep(0.001)
        else:
            self.ctrltouartQueue.put("ctrltouart:::import os\r\n")

        startTime=time.time()
        while True:
            if self.importUosMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>3:
                self.importUosBool=False
                self.importUosMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"import os timeout")
                return

        if self.importUosMsg.find("Traceback")>=0 or self.importUosMsg.find("... ")>=0:
            self.importUosBool=False
            returnData=self.importUosMsg
            self.importUosMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),"import os false")
            else:
                self.ctrltouartQueue.put("uitouart:::\x03")
                time.sleep(0.01)
            return

        self.importUosBool=False
        self.importUosMsg=""

    def getcwd(self):
        self.getcwdBool=True
        self.getcwdMsg=""
        self.ctrltouartQueue.put("ctrltouart:::os.getcwd()\r\n")

        startTime=time.time()
        while 1:
            if self.getcwdMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>3:
                self.getcwdBool=False
                self.getcwdMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"getcwd timeout")
                return
        if self.getcwdMsg.find("Traceback")>=0 or self.getcwdMsg.find("... ")>=0:
            self.getcwdBool=False
            returnData=self.getcwdMsg
            self.getcwdMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),"getcwd false")
            else:
                self.ctrltouartQueue.put("uitouart:::\x03")
                time.sleep(0.01)
            return
        
        rootDir=self.getcwdMsg.split("\r\n")
        self.emit(SIGNAL("uiRecvFromCtrl"),"rootDir:%s"%rootDir[1][1:-1])
        self.rootDir=rootDir[1][1:-1]
        self.getcwdBool=False
        self.getcwdMsg=""
                
        
    def dragChangeDir(self,dragfile,dropfile):
        #if str(dragfile).find(":")<0:#device Internal move
        if sys.platform=="linux" and str(dragfile).find(rootDirectoryPath)<0:
            dropfile=dropfile + "/" + dragfile.split("/")[-1]
            self.rename(dragfile,dropfile)
        elif sys.platform=="win32" and str(dragfile).find(":")<0:
            dropfile=dropfile + "/" + dragfile.split("/")[-1]
            self.rename(dragfile,dropfile)
        elif sys.platform=="darwin" and str(dragfile).find(rootDirectoryPath)<0:
            dropfile=dropfile + "/" + dragfile.split("/")[-1]
            self.rename(dragfile,dropfile)
        #if str(dragfile).find(rootDirectoryPath)<0:
        #    dropfile=dropfile + "/" + dragfile.split("/")[-1]
        #    self.rename(dragfile,dropfile)
        else:#device external drag and download
            dropfile=dropfile + "/" + dragfile.split("/")[-1]
            self.dropDownFileName=dropfile
            self.downloadFile(dragfile)

    def getMoreRenameDir(self,dirpath):
        self.renameMsg=""
        self.ctrltouartQueue.put("ctrltouart:::os.listdir(\'%s\')\r\n"%str(dirpath))
        startTime=time.time()
        while 1:
            if self.renameMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>1:
                return False

        if self.renameMsg.find("Traceback")>=0 or self.renameMsg.find("... ")>=0:
            returnData=self.renameMsg
            if returnData.find("Traceback")>=0:
                pass
            else:
                self.ctrltouartQueue.put("uitouart:::\x03")
                time.sleep(0.01)
            return False

        inDirFile = self.renameMsg[str(self.renameMsg).find("["):str(self.renameMsg).find("]")+1]

        inDirFile=str(inDirFile).split("'")
        for i in inDirFile:
            if i.find("[")>=0 or i.find("]")>=0 or i.find(",")>=0:
                pass
            else:
                if i.find(".")>0:
                    self.returnUIinDirFile.append(dirpath+"/"+i)
                else:
                    dirreturn = self.getMoreRenameDir(dirpath+"/"+i)
                    if dirreturn==False:
                        return False
        return True
        
    def getMoreRmDir(self,dirpath):
        self.deleteFileMsg=""
        self.ctrltouartQueue.put("ctrltouart:::os.listdir(\'%s\')\r\n"%str(dirpath))
        startTime=time.time()
        while 1:
            if self.deleteFileMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>2:
                return False

        if self.deleteFileMsg.find("Traceback")>=0 or self.deleteFileMsg.find("... ")>=0:
            returnData=self.deleteFileMsg
            if returnData.find("Traceback")>=0:
                pass
            else:
                self.ctrltouartQueue.put("uitouart:::\x03")
                time.sleep(0.01)
            return False

        inDirFile = self.deleteFileMsg[str(self.deleteFileMsg).find("["):str(self.deleteFileMsg).find("]")+1]
        inDirFile=str(inDirFile).split("'")
        for i in inDirFile:
            if i.find("[")>=0 or i.find("]")>=0 or i.find(",")>=0:
                pass
            else:
                if i.find(".")>0:
                    self.returnUIinDirFile.append(dirpath+"/"+i)
                else:
                    dirreturn = self.getMoreRmDir(dirpath+"/"+i)
                    if dirreturn==False:
                        return False

        return True

    def rename(self,oldname,newname):
        print("rename,oldname:%s,newname:%s\n"%(oldname,newname))
        self.renameBool=True

        if str(oldname)==self.rootDir:
            self.renameBool=False
            self.renameMsg=""
            return

        self.renameMsg=""
        self.ctrltouartQueue.put("ctrltouart:::os.stat(\'%s\')\r\n"%str(oldname))
        
        startTime=time.time()
        while 1:
            if self.renameMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>1:
                self.renameBool=False
                self.renameMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"rename timeout")
                return
        
        if self.renameMsg.find("Traceback")>=0 or self.renameMsg.find("... ")>=0:
            self.renameBool=False
            returnData=self.renameMsg
            self.renameMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"rename error")
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"rename error")
            return

        isdir=self.renameMsg.split("\r\n")
        for adir in isdir:
            if adir.find(", ")>=0:
                adir=adir[adir.find("(")+1:adir.find(")")]
                adir=adir.split(", ")
                break

        self.renameMsg=""
        if int(adir[0])==0o100000:
            self.ctrltouartQueue.put("ctrltouart:::os.rename(\'%s\',\'%s\')\r\n"%(str(oldname),str(newname)))
            startTime=time.time()
            while 1:
                if self.renameMsg=="":
                    time.sleep(0.005)
                else:
                    break
                endTime=time.time()
                if endTime-startTime>1:
                    self.renameBool=False
                    self.renameMsg=""
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename file false")
                    return
            if self.renameMsg.find("Traceback")>=0 or self.renameMsg.find("... ")>=0:
                self.renameBool=False
                returnData=self.renameMsg
                self.renameMsg=""
                if returnData.find("Traceback")>=0:
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename file false")
                else:
                    self.ctrltouartQueue.put("ctrltouart:::\x03")
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename file false")
                return
            
            self.emit(SIGNAL("uiRecvFromCtrl"),"rename ok")
        else:#dir
            self.ctrltouartQueue.put("ctrltouart:::os.listdir(\'%s\')\r\n"%str(oldname))
            startTime=time.time()
            while 1:
                if self.renameMsg=="":
                    time.sleep(0.005)
                else:
                    break
                endTime=time.time()
                if endTime-startTime>1:
                    self.renameBool=False
                    self.renameMsg=""
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename dir false1")
                    return

            if self.renameMsg.find("Traceback")>=0 or self.renameMsg.find("... ")>=0:
                self.renameBool=False
                returnData=self.renameMsg
                self.renameMsg=""
                if returnData.find("Traceback")>=0:
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename dir false2")
                else:
                    self.ctrltouartQueue.put("ctrltouart:::\x03")
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename dir false3")
                return
            
            inDirFile = self.renameMsg[str(self.renameMsg).find("["):str(self.renameMsg).find("]")+1]
            print(inDirFile)
            self.returnUIinDirFile=[]
            inDirFile=str(inDirFile).split("'")
            for i in inDirFile:
                if i.find("[")>=0 or i.find("]")>=0 or i.find(",")>=0:
                    pass
                else:
                    if i.find(".")>0:
                        self.returnUIinDirFile.append(oldname+"/"+i)
                    else:
                        dirreturn = self.getMoreRenameDir(oldname+"/"+i)
                        if dirreturn==False:
                            self.renameBool=False
                            self.renameMsg=""
                            self.emit(SIGNAL("uiRecvFromCtrl"),"rename false")
                            return

            print(self.returnUIinDirFile)

            self.emit(SIGNAL("renameDirDeleteDirTab"),self.returnUIinDirFile)

            self.renameMsg=""
            self.ctrltouartQueue.put("ctrltouart:::os.rename(\'%s\',\'%s\')\r\n"%(str(oldname),str(newname)))
            startTime=time.time()
            while 1:
                if self.renameMsg=="":
                    time.sleep(0.005)
                else:
                    break
                endTime=time.time()
                if endTime-startTime>1:
                    self.renameBool=False
                    self.renameMsg=""
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename false1")
                    return
            if self.renameMsg.find("Traceback")>=0 or self.renameMsg.find("... ")>=0:
                self.renameBool=False
                returnData=self.renameMsg
                self.renameMsg=""
                if returnData.find("Traceback")>=0:
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename false2")
                else:
                    self.ctrltouartQueue.put("ctrltouart:::\x03")
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rename false3")
                return
            
            self.emit(SIGNAL("uiRecvFromCtrl"),"rename ok")
          
        self.renameBool=False
        self.renameMsg=""

    def createNewDir(self,path,name):
        self.createNewDirBool=True
        self.createNewDirMsg=""
        print("in createNewDir dirpath:%s,dirname:%s"%(path,name))
        dirname=path+"/"+name
        self.ctrltouartQueue.put("ctrltouart:::os.mkdir('%s')\r\n"%str(dirname))
        startTime=time.time()
        while 1:
            if self.createNewDirMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>1:
                self.createNewDirBool=False
                self.createNewDirMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"dir false:time out")
                return
        if self.createNewDirMsg.find("Traceback")>=0 or self.createNewDirMsg.find("... ")>=0:
            self.createNewDirBool=False
            returnData=self.createNewDirMsg
            self.createNewDirMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"dir false:cmd not full")
            return

        self.emit(SIGNAL("uiRecvFromCtrl"),"newdir ok")
        self.createNewDirBool=False
        self.createNewDirMsg=""

    def checkFirmware(self):
        self.checkFirmwareBool=True

        self.ctrltouartQueue.put("ctrltouart:::os.uname()\r\n")
        startTime=time.time()
        while 1:
            if self.checkFirmwareMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>2:
                self.checkFirmwareBool=False
                self.checkFirmwareMsg=""
                self.emit(SIGNAL("checkFiremware"),"false")
                return
        if self.checkFirmwareMsg.find("Traceback")>=0 or self.checkFirmwareMsg.find("... ")>=0:
            self.checkFirmwareBool=False
            returnData=self.checkFirmwareMsg
            self.checkFirmwareMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("checkFiremware"),"false")
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("checkFiremware"),"false")
            return
        else:
            self.emit(SIGNAL("checkFiremware"),self.checkFirmwareMsg)
            self.checkFirmwareMsg=""
            self.checkFirmwareBool=False
            return

    def setDefaultProg(self,filename):
        print("setDefaultProg:%s"%filename)
        self.setDefaultProgBool=True
        self.setDefaultProgMsg=""
        if self.currentBoard=="microbit":
            aline="myfile=open('main.py','w')\r"
            for i in aline:
                self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                time.sleep(0.001)
        else:
            self.ctrltouartQueue.put("ctrltouart:::myfile=open(\'main.py\',\'w\')\r\n")
        startTime=time.time()
        while 1:
            if self.setDefaultProgMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>1:
                self.setDefaultProgBool=False
                self.setDefaultProgMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program open file timeout")
                return
        if self.setDefaultProgMsg.find("Traceback")>=0 or self.setDefaultProgMsg.find("... ")>=0:
            self.setDefaultProgBool=False
            returnData=self.setDefaultProgMsg
            self.setDefaultProgMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program false")
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program false")
            return

        self.setDefaultProgMsg=""
        if self.currentBoard=="microbit":
            aline="myfile.write(\"exec(open('%s').read(),globals())\")\r"%str(filename[2:])
            for i in aline:
                self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                time.sleep(0.001)
        else:
            #if str(filename).find("/flash")>=0:
            #    filenameLast = filename.replace("/flash",".")
            #    readwriteQueue.put("ctrltouart:::myfile.write(\"try:\\r  exec(open(\'%s\').read(),globals())\\rexcept:\\r  exec(open(\'%s\').read(),globals())\")\r\n"%(str(filename),str(filenameLast)))
            #else:
            self.ctrltouartQueue.put("ctrltouart:::myfile.write(\"exec(open(\'%s\').read(),globals())\")\r\n"%str(filename))
       
        startTime=time.time()
        while 1:
            if self.setDefaultProgMsg=="":
                time.sleep(0.005)
            else:
                print(self.setDefaultProgMsg)
                break
            endTime=time.time()
            if endTime-startTime>3:
                self.setDefaultProgBool=False
                self.setDefaultProgMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program false")
                return
        if self.setDefaultProgMsg.find("Traceback")>=0 or self.setDefaultProgMsg.find("... ")>=0:
            self.setDefaultProgBool=False
            returnData=self.setDefaultProgMsg
            self.setDefaultProgMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program false")
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program false")
            return

        self.setDefaultProgMsg=""
        if self.currentBoard=="microbit":
            aline="myfile.close()\r"
            for i in aline:
                self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                time.sleep(0.001)
        else:
            self.ctrltouartQueue.put("ctrltouart:::myfile.close()\r\n")
        startTime=time.time()
        while 1:
            if self.setDefaultProgMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>1:
                self.setDefaultProgBool=False
                self.setDefaultProgMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program false")
                return
        if self.setDefaultProgMsg.find("Traceback")>=0 or self.setDefaultProgMsg.find("... ")>=0:
            self.setDefaultProgBool=False
            returnData=self.setDefaultProgMsg
            self.setDefaultProgMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program false")
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"set Default Program false")
            return

        self.emit(SIGNAL("uiRecvFromCtrl"),"set Default ok")
        self.setDefaultProgBool=False
        self.setDefaultProgMsg=""

    def downFileFalseDeal(self,filename):
        pass

    def deleteMicroBit(self,filename):
        print("in deletemicrobit file")
        aline="os.remove('%s')\r"%str(filename[2:])
        for i in aline:
            self.ctrltouartQueue.put("ctrltouart:::%s"%i)
            time.sleep(0.001)
        startTime=time.time()
        while 1:
            if self.deleteFileMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>3:
                self.deleteFileBool=False
                self.deleteFileMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"rm file false1")
                return

        if self.deleteFileMsg.find("Traceback")>=0 or self.deleteFileMsg.find("... ")>=0:
            self.deleteFileBool=False
            returnData=self.deleteFileMsg
            self.deleteFileMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"rm file false2")
            else:
                self.ctrltouartQueue.put("uitouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"rm file false3")
            return
                
        self.emit(SIGNAL("deleteBoardFileSig"),filename)
        self.deleteFileBool=False
        self.deleteFileMsg=""

    def deleteFile(self,filename):
        self.deleteFileBool=True
        self.deleteFileMsg=""

        if str(filename)==self.rootDir:
            self.deleteFileBool=False
            self.deleteFileMsg=""
            return

        if self.currentBoard=="microbit":
            self.deleteMicroBit(filename)
            return

        self.ctrltouartQueue.put("ctrltouart:::os.stat(\'%s\')\r\n"%str(filename))
        startTime=time.time()
        while 1:
            if self.deleteFileMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>1:
                self.deleteFileBool=False
                self.deleteFileMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"delete error stat timeout")
                return

        if self.deleteFileMsg.find("Traceback")>=0 or self.deleteFileMsg.find("... ")>=0:
            self.deleteFileBool=False
            returnData=self.deleteFileMsg
            self.deleteFileMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"delete error")
            else:
                self.ctrltouartQueue.put("uitouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"delete error")
            return


        isdir=self.deleteFileMsg.split("\r\n")
        for adir in isdir:
            if adir.find(", ")>=0:
                adir=adir[adir.find("(")+1:adir.find(")")]
                adir=adir.split(", ")
                break

        if int(adir[0])==0o100000:
            self.deleteFileMsg=""
            self.ctrltouartQueue.put("ctrltouart:::os.remove(\'%s\')\r\n"%str(filename))
            startTime=time.time()
            while 1:
                if self.deleteFileMsg=="":
                    time.sleep(0.005)
                else:
                    break
                endTime=time.time()
                if endTime-startTime>2:
                    self.deleteFileBool=False
                    self.deleteFileMsg=""
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm file false1")
                    return

            if self.deleteFileMsg.find("Traceback")>=0 or self.deleteFileMsg.find("... ")>=0:
                self.deleteFileBool=False
                returnData=self.deleteFileMsg
                self.deleteFileMsg=""
                if returnData.find("Traceback")>=0:
                    self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                    time.sleep(0.01)
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm file false2")
                else:
                    self.ctrltouartQueue.put("uitouart:::\x03")
                    time.sleep(0.01)
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm file false3")
                return
                
            self.emit(SIGNAL("deleteBoardFileSig"),filename)
        else:#rmdir
            self.deleteFileMsg=""
            self.ctrltouartQueue.put("ctrltouart:::os.listdir(\'%s\')\r\n"%str(filename))
            startTime=time.time()
            while 1:
                if self.deleteFileMsg=="":
                    time.sleep(0.005)
                else:
                    break
                endTime=time.time()
                if endTime-startTime>1:
                    self.deleteFileBool=False
                    self.deleteFileMsg=""
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm dir false")
                    return
            
            if self.deleteFileMsg.find("Traceback")>=0 or self.deleteFileMsg.find("... ")>=0:
                self.deleteFileBool=False
                returnData=self.deleteFileMsg
                self.deleteFileMsg=""
                if returnData.find("Traceback")>=0:
                    self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                    time.sleep(0.01)
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm dir false")
                else:
                    self.ctrltouartQueue.put("uitouart:::\x03")
                    time.sleep(0.01)
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm dir false")
                return

            inDirFile = ""
            inDirFile = self.deleteFileMsg[str(self.deleteFileMsg).find("["):str(self.deleteFileMsg).find("]")+1]
            self.returnUIinDirFile=[]
            inDirFile=str(inDirFile).split("'")
            for i in inDirFile:
                if i.find("[")>=0 or i.find("]")>=0 or i.find(",")>=0:
                    pass
                else:
                    if i.find(".")>0:
                        self.returnUIinDirFile.append(filename+"/"+i)
                    else:
                        dirreturn = self.getMoreRmDir(filename+"/"+i)
                        if dirreturn==False:
                            self.deleteFileBool=False
                            self.deleteFileMsg=""
                            self.emit(SIGNAL("uiRecvFromCtrl"),"rm dir false")
                            return

            self.emit(SIGNAL("renameDirDeleteDirTab"),self.returnUIinDirFile)

            self.deleteFileMsg=""

            self.ctrltouartQueue.put("ctrltouart:::os.rmdir(\'%s\')\r\n"%str(filename))
            startTime=time.time()
            while 1:
                if self.deleteFileMsg=="":
                    time.sleep(0.005)
                else:
                    break
                endTime=time.time()
                if endTime-startTime>1:
                    self.deleteFileBool=False
                    self.deleteFileMsg=""
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm dir false")
                    return

            if self.deleteFileMsg.find("Traceback")>=0 or self.deleteFileMsg.find("... ")>=0:
                self.deleteFileBool=False
                returnData=self.deleteFileMsg
                self.deleteFileMsg=""
                if returnData.find("Traceback")>=0:
                    self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                    time.sleep(0.01)
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm dir false")
                else:
                    self.ctrltouartQueue.put("uitouart:::\x03")
                    time.sleep(0.01)
                    self.emit(SIGNAL("uiRecvFromCtrl"),"rm dir false")
                return

            self.emit(SIGNAL("uiRecvFromCtrl"),"rmdir ok")
            
        self.deleteFileBool=False
        self.deleteFileMsg=""

    def intoFunc(self,data):
        pass

    def goProgram(self,filename):
        if str(filename).find("/")<0:
            pass
        else:
            #if str(filename).find(":")>=0:
            if (sys.platform=="linux" and str(filename).find(rootDirectoryPath)>=0) or (sys.platform=="win32" and str(filename).find(":")>=0) or (sys.platform=="darwin" and str(filename).find(rootDirectoryPath)>=0):
            #if str(filename).find(rootDirectoryPath)>=0:
                filelist=str(filename).split('/')
                for afile in filelist:
                    if afile.find(".py")>=0:
                        filename=afile
                        break
            else:
                pass
            
        if self.currentBoard=="microbit":
            if str(filename).find("./")>=0:
                aline="exec(open('%s').read(),globals())"%str(filename[2:])
            else:
                aline="exec(open('%s').read(),globals())"%str(filename)
            for i in aline:
                self.ctrltouartQueue.put("uitouart:::%s"%i)
                time.sleep(0.001)
            self.ctrltouartQueue.put("exec_:::\r")
        else:
            self.ctrltouartQueue.put("exec_:::exec(open(\'%s\').read(),globals())\r\n"%str(filename))

    def loadFile(self,filename):
        print("ctrl loadfile")
        self.loadFileBool=True
        self.loadFileMsg=""
        if self.currentBoard=="microbit":
            aline="print(open('%s','r').read())\r"%str(filename[2:])
            for i in aline:
                self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                time.sleep(0.001)
        else:
            self.ctrltouartQueue.put("ctrltouart:::print(open(\'%s\',\'rU\').read())\r\n"%str(filename))

        startTime=time.time()
        while 1:
            if self.loadFileMsg == "" or self.loadFileMsg==None:
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>3:
                self.loadFileBool=False
                self.loadFileMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"open board file timeout")
                return

        if self.loadFileMsg.find("Traceback")>=0 or self.loadFileMsg.find("... ")>=0:
            self.loadFileBool=False
            returnData=self.loadFileMsg
            self.loadFileMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"open board file false")
            else:
                readwriteQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"open board file false")
            return

        self.loadfileMsg=self.loadFileMsg.replace("\r\n","\r")
        self.loadfileMsg=self.loadFileMsg.replace("\n","\r")
        
        myList=self.loadFileMsg.split('\r')

        appendMsg=''
        lenth=0     
        while lenth<=len(myList):
            if lenth==0:        #lenth=0,list err
                pass
            elif lenth==1:      #lenth=1,mylenth[0],it is not be used
                pass
            elif lenth==len(myList):   #delete endless '>>>'
                pass
            else:
                appendMsg+=str(myList[lenth-1])+"\r\n"    #use [lenth-1],len=3,list have [0][1][2]
            lenth+=1

        filenameB=filename.split("/")
        connectdir=""
        for afile in filenameB:
            if afile == "" or afile==".":
                pass
            elif afile.find(".py")>=0 or afile.find(".txt")>=0 or afile.find(".json")>=0 or afile.find(".ini")>=0:
                connectdir+=afile
                break
            else:
                connectdir=connectdir+afile+"/"
                if os.path.exists(currentTempPath+connectdir)==False:
                    os.mkdir(currentTempPath+connectdir)
                    
        myfile=open(currentTempPath+connectdir,'w',encoding='UTF-8')
        if type(appendMsg) is bytes:
            appendMsg=appendMsg.decode('utf-8')
        myfile.write(appendMsg)
        myfile.close()

        self.emit(SIGNAL("loadFileSig"),filename,appendMsg)
        self.loadFileMsg=""
        self.loadFileBool=False

    def downloadFile(self,filename):
        filename = filename.replace("\\","/")
        print("downloadFile===============================%s\n"%filename)
        if str(filename).find(".py")>=0:
            if self.dragDropModel==True:
                afile=self.dropDownFileName
            #elif str(filename).find(":")<0:
            #elif str(filename).find(rootDirectoryPath)<0:
            #    afile=str(filename)
            elif sys.platform=="linux" and str(filename).find(rootDirectoryPath)<0:
                afile=str(filename)
            elif sys.platform=="win32" and str(filename).find(":")<0:
                afile=str(filename)
            elif sys.platform=="darwin" and str(filename).find(rootDirectoryPath)<0:
                afile=str(filename)
            else:
                if str(filename).find("/")>=0:
                    afile=str(filename).split("/")
                else:
                    afile=str(filename).split("\\")
                afile=afile[-1]           
        else:
            afile=str(filename).split("/")[-1]
        
        self.downloadFileBool=True

        if self.dragDropModel == True:
            try:
                fileHandle=open(filename,'rbU')
            except Exception:
                self.downloadFileBool=False
                self.emit(SIGNAL("uiRecvFromCtrl"),"no suport for download dir")
                return
            afile=self.dropDownFileName
        #elif filename.find(":")<0:
        elif sys.platform=="linux" and filename.find(rootDirectoryPath)<0:
            fileHandle=open(currentTempPath+filename,'rbU')
        elif sys.platform=="win32" and filename.find(":")<0:
            fileHandle=open(currentTempPath+filename,'rbU')
        elif sys.platform=="darwin" and filename.find(rootDirectoryPath)<0:
            fileHandle=open(currentTempPath+filename,'rbU')
        #elif filename.find(rootDirectoryPath)<0:
        #    fileHandle=open(currentTempPath+filename,'rbU')
        else:
            myfile=open(currentTempPath+"/"+str(filename.split("/")[-1]),"w",encoding='UTF-8')
            filemsg=""
            filemsg=self.ui.tabWidget.currentWidget().text()

            if type(filemsg) is bytes:
                filemsg=filemsg.decode('utf-8')
        
            myfile.write(filemsg)
            myfile.close()
            fileHandle=open(currentTempPath+"/"+str(filename.split("/")[-1]),'rbU')

        self.downloadFileMsg=""
        self.ctrltouartQueue.put("ctrltouart:::\x03")
        startTime=time.time()
        while 1:
            if self.downloadFileMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>2:
                fileHandle.close()
                self.downloadFileBool=False
                self.downloadFileMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"runningFileBreakFalse")
                return

        self.emit(SIGNAL("uiRecvFromCtrl"),self.downloadFileMsg)
        self.emit(SIGNAL("uiRecvFromCtrl"),"Ready to download this file,please wait!")

        ##################
        #open(filename,'w')
        ##################
        self.downloadFileMsg=""
        #the following shows:if create false,the file handle is None,do not deal)
        if self.currentBoard=="microbit":
            aline="myfile=open(%s,'w')\r"%repr(afile.split("/")[-1])
            for i in aline:
                self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                time.sleep(0.001)
        else:
            self.ctrltouartQueue.put("ctrltouart:::myfile=open(\'%s\',\'w\')\r\n"%str(afile))
        
        startTime=time.time()
        while 1:
            if self.downloadFileMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>3:
                fileHandle.close()
                self.downloadFileBool=False
                self.downloadFileMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"download false")
                return
        if self.downloadFileMsg.find("Traceback")>=0 or self.downloadFileMsg.find("... ")>=0:
            fileHandle.close()
            self.downloadFileBool=False
            returnData=self.downloadFileMsg
            self.downloadFileMsg=""
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"download false")
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"download false")
            return

        ##################
        #write(msg)
        ##################
        done=0
        while not done:
            if self.currentBoard == "microbit":
                aline = fileHandle.read(64)
            else:
                aline = fileHandle.read(128)

            if(str(aline)!="b''"):
                if self.currentBoard=="microbit":
                    self.emit(SIGNAL("uiRecvFromCtrl"),".")
                    self.downloadFileMsg=""
                    try:
                        aline=aline.decode()
                        #if aline.find("\r\n")<0 and aline.find("\n")>=0:
                        #    aline=aline.replace("\n","\r")
                        #elif aline.find("\r\n")>=0:
                        #    aline=aline.replace("\n","")
                        aline=aline.replace("\r\n","\r")
                        aline=aline.replace("\n","\r")
                        aline="myfile.write(%s)\r"%repr(aline)
                    except:
                        aline="myfile.write(%s)\r"%repr(aline)
                    for i in aline:
                        self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                        time.sleep(0.001)
                else:
                    try:
                        aline=aline.decode()
                        
                        #if aline.find("\r\n")<0 and aline.find("\\n")>=0:
                        #    aline=aline.replace("\n","\r")
                        #elif aline.find("\r\n")>=0:
                        #    aline=aline.replace("\n","")
                        aline=aline.replace("\r\n","\r")
                        aline=aline.replace("\n","\r")
                        aline=aline.encode('utf-8')
                        self.emit(SIGNAL("uiRecvFromCtrl"),".")
                        self.downloadFileMsg=""
                        self.ctrltouartQueue.put("ctrltouart:::myfile.write(%s)\r\n"%aline)
                    except:
                        self.emit(SIGNAL("uiRecvFromCtrl"),".")
                        self.downloadFileMsg=""
                        self.ctrltouartQueue.put("ctrltouart:::myfile.write(%s)\r\n"%aline)
                
                startTime=time.time()
                while 1:#if this place is false锛宼hink about that Whether join err deal with self.downFileFalseDeal(afile)
                    if self.downloadFileMsg=="":
                        time.sleep(0.005)
                    else:
                        break
                    endTime=time.time()
                    if endTime-startTime>15:
                        fileHandle.close()
                        self.downloadFileBool=False
                        self.downloadFileMsg=""
                        self.emit(SIGNAL("uiRecvFromCtrl"),"download false4")
                        return
                if self.downloadFileMsg.find("Traceback")>=0 or self.downloadFileMsg.find("... ")>=0:
                    fileHandle.close()
                    self.downloadFileBool=False
                    returnData=self.downloadFileMsg
                    self.downloadFileMsg=""

                    self.downFileFalseDeal(afile)
                    if returnData.find("Traceback")>=0:
                        self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                        time.sleep(0.01)
                        self.emit(SIGNAL("uiRecvFromCtrl"),"download false5")
                    else:
                        self.ctrltouartQueue.put("ctrltouart:::\x03")
                        time.sleep(0.01)
                        self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                        self.emit(SIGNAL("uiRecvFromCtrl"),"download false6")
                    return      
            else:
                done=1

        ##################
        #myfile.close()
        ##################
        fileHandle.close()

        self.downloadFileMsg=""
        if self.currentBoard=="microbit":
            aline="myfile.close()\r"
            for i in aline:
                self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                time.sleep(0.001)
        else:
            self.ctrltouartQueue.put("ctrltouart:::myfile.close()\r\n")
        startTime=time.time()
        while 1:
            if self.downloadFileMsg=="":
                time.sleep(0.005)
            else:
                break
            endTime=time.time()
            if endTime-startTime>3:
                self.downloadFileBool=False
                self.downloadFileMsg=""
                self.emit(SIGNAL("uiRecvFromCtrl"),"download false7")
                return
        if self.downloadFileMsg.find("Traceback")>=0 or self.downloadFileMsg.find("... ")>=0:
            self.downloadFileBool=False
            returnData=self.downloadFileMsg
            self.downloadFileMsg=""

            self.downFileFalseDeal(afile)
            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"download false")
            else:
                #self.readuart.serial.ser.write("\x03")
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"download false")
            return
        
        self.downloadFileBool=False
        self.downloadFileMsg=""
        self.emit(SIGNAL("uiRecvFromCtrl"),"download ok")
        return

    def treeWaitUart(self):
        startTime=time.time()
        while 1:
            if self.reflushTreeMsg=="":
                time.sleep(0.005)
            else:
                return "ok"
            endTime=time.time()
            if endTime-startTime>3:
                self.reflushTreeBool=False
                self.reflushTreeMsg=""
                self.emit(SIGNAL("reflushTree"),"err")
                return "err"

    def getFileTree(self,dir):
        self.reflushTreeMsg=""
        self.ctrltouartQueue.put("ctrltouart:::os.listdir(\'%s\')\r\n"%dir)
        result=self.treeWaitUart()
        if result=="err":
            return result
        #print(self.reflushTreeMsg)

        if self.reflushTreeMsg.find("Traceback")>=0 or self.reflushTreeMsg.find("... ")>=0:
            self.reflushTreeBool=False
            returnData=self.reflushTreeMsg
            self.reflushTreeMsg=""

            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"reflush tree false")
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"reflush tree false")
            return "err"

        filemsg=self.reflushTreeMsg[self.reflushTreeMsg.find("["):self.reflushTreeMsg.find("]")+1]

        ret=json.loads("{}")
        ret[dir]=[]
        if filemsg=="[]":
            return ret
        filelist=[]
        filemsg=filemsg.split("'")
        
        for i in filemsg:
            if i.find("[")>=0 or i.find(",")>=0 or i.find("]")>=0:
                pass
            else:
                filelist.append(i)
        
        for i in filelist:
            self.reflushTreeMsg=""
            self.ctrltouartQueue.put("ctrltouart:::os.stat(\'%s\')\r\n"%(dir+"/"+i))
            result=self.treeWaitUart()
            if result=="err":
                return result
            if self.reflushTreeMsg.find("Traceback")>=0 or self.reflushTreeMsg.find("... ")>=0:
                self.reflushTreeBool=False
                returnData=self.reflushTreeMsg
                self.reflushTreeMsg=""

                if returnData.find("Traceback")>=0:
                    self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                    time.sleep(0.01)
                    self.emit(SIGNAL("uiRecvFromCtrl"),"reflush tree false")
                else:
                    self.ctrltouartQueue.put("ctrltouart:::\x03")
                    time.sleep(0.01)
                    self.emit(SIGNAL("uiRecvFromCtrl"),"reflush tree false")
                return "err"

            isdir=self.reflushTreeMsg.split("\r\n")

            for adir in isdir:
                if adir.find(", ")>=0:
                    adir=adir[adir.find("(")+1:adir.find(")")]
                    adir=adir.split(", ")
                    break
            try:
                if int(adir[0])==0o40000:
                    if self.currentBoard=="pyboard" and i=="System Volume Information":
                        pass
                    else:
                        ret[dir].append(self.getFileTree(dir+"/"+i))
                else:
                    ret[dir].append(i)
            except:
                self.emit(SIGNAL("uiRecvFromCtrl"),"reflush tree false")
                return "err"

        return ret

    def getFileTreeBit(self,dir):
        self.reflushTreeMsg=""

        aline="os.listdir()\r"
        for i in aline:
            self.ctrltouartQueue.put("ctrltouart:::%s"%i)
            time.sleep(0.001)
        
        result=self.treeWaitUart()
        if result=="err":
            return result
        
        if self.reflushTreeMsg.find("Traceback")>=0 or self.reflushTreeMsg.find("... ")>=0:
            self.reflushTreeBool=False
            returnData=self.reflushTreeMsg
            self.reflushTreeMsg=""

            if returnData.find("Traceback")>=0:
                self.emit(SIGNAL("uiRecvFromCtrl"),returnData)
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"reflush tree false")
            else:
                self.ctrltouartQueue.put("ctrltouart:::\x03")
                time.sleep(0.01)
                self.emit(SIGNAL("uiRecvFromCtrl"),"reflush tree false")
            return "err"

        filemsg=self.reflushTreeMsg[self.reflushTreeMsg.find("["):self.reflushTreeMsg.find("]")+1]

        ret=json.loads("{}")
        ret[dir]=[]
        if filemsg=="[]":
            return ret
        filelist=[]
        filemsg=filemsg.split("'")
        
        for i in filemsg:
            if i.find("[")>=0 or i.find(",")>=0 or i.find("]")>=0:
                pass
            else:
                filelist.append(i)
                ret[dir].append(i)

        return ret

    def treeModel(self):
        self.reflushTreeBool=True
        self.reflushTreeMsg=""

        res=json.loads("{}")

        if self.currentBoard=="microbit":
            res=self.getFileTreeBit(".")
        else:
            res=self.getFileTree(".")
        if res=="err":
            self.reflushTreeBool=False
            self.reflushTreeMsg=""
            return

        if str(res).find("main.py")>=0:
            self.reflushTreeMsg=""

            if self.currentBoard=="microbit":
                aline="print(open('main.py','r').read())\r"
                for i in aline:
                    self.ctrltouartQueue.put("ctrltouart:::%s"%i)
                    time.sleep(0.001)
                
            else:
                self.ctrltouartQueue.put("ctrltouart:::print (open(\'main.py\',\'r\').read())\r\n")

            result=self.treeWaitUart()
            if result=="err":
                self.reflushTreeBool=False
                self.reflushTreeMsg=""
                return
            print(self.reflushTreeMsg)
            self.reflushTreeMsg=self.reflushTreeMsg.split("\n")[1]
            self.ui.myDefaultProgram=self.reflushTreeMsg[str(self.reflushTreeMsg).find("('")+2:str(self.reflushTreeMsg).find("')")]
        else:
            self.ui.myDefaultProgram=""
            pass
                    
        self.emit(SIGNAL("reflushTree"),res)
        self.reflushTreeMsg=""
        self.reflushTreeBool=False

    def ctrlRecvUartMsg(self,data):
        if data=="" or data==None:
            return
        elif self.reflushTreeBool==True:
            print("reflushTreeBool is true")
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.reflushTreeMsg=self.recvAllData
                self.recvAllData=""
            return     
        elif self.loadFileBool==True:
            print("loadfileMsg is true")
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.loadFileMsg=self.recvAllData
                self.recvAllData=""
            return        
        elif self.intoFuncBool==True:
            print("intoFuncMsg is true")
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.intoFuncMsg=self.recvAllData
                self.recvAllData=""
            return 
        elif self.deleteFileBool==True:
            print("deleteFileMsg is true")
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.deleteFileMsg=self.recvAllData
                self.recvAllData=""
            return      
        elif self.downloadFileBool==True:
            print("downBigFileMsg is true")
            self.recvAllData+=data
            print("recvAllData=%s"%self.recvAllData)

            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.downloadFileMsg=self.recvAllData
                self.recvAllData=""
            return        
        elif self.downFileFalseBool==True:
            print("downFileFalse is true")
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.downFileFalseMsg=self.recvAllData
                self.recvAllData=""
            return
        elif self.setDefaultProgBool==True:
            print("setDefaultProgMsg is true")
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.setDefaultProgMsg=self.recvAllData
                self.recvAllData=""
            return
        elif self.checkFirmwareBool==True:
            print("checkFirmwareSig is true")
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.checkFirmwareMsg=self.recvAllData
                self.recvAllData=""
            return
        elif self.createNewDirBool==True:
            print("createNewDirMsg is true")
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.createNewDirMsg=self.recvAllData
                self.recvAllData=""
            return
        elif self.renameBool==True:
            print("renamesig is true")
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.renameMsg=self.recvAllData
                self.recvAllData=""
            return
        elif self.getcwdBool==True:
            self.recvAllData+=data
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.getcwdMsg=self.recvAllData
                self.recvAllData=""
            return
        elif self.importUosBool==True:
            self.recvAllData+=data
            print("***2017***%s"%data)
            if self.recvAllData.find(">>> ")>=0 or self.recvAllData.find("... ")>=0:
                self.importUosMsg=self.recvAllData
                self.recvAllData=""
            return
        else:
            self.emit(SIGNAL("uiRecvFromCtrl"),data)




