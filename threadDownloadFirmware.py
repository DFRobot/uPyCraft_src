#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import threading
import uPyCraft_src.Esp
import urllib
from urllib import request
import socket
import shutil
import codecs
from PyQt5.QtCore import *
from uPyCraft_src.Esp import ESPTool, Burn, downOkReset


class threadUserFirmware(QThread):
    firmwareAnyDown = pyqtSignal(int)
    firmwareAnyUpdate = pyqtSignal(int)
    firmwareAnyErase = pyqtSignal(int)
    goMicrobitUpdate = pyqtSignal()

    def __init__(self, board, savepath, com, iserase, size, addr, parent):
        super(threadUserFirmware,self).__init__(parent)

        self.board=board
        self.savepath=savepath
        self.com=com
        self.iserase=iserase
        self.size=size
        self.erasePer=0
        self.erasestart=False
        self.erasetimer=None
        self.burnaddr=0
        if addr=="0x0":
            self.burnaddr=0
        else:
            self.burnaddr=0x1000

        print("burnaddr=====%d"%self.burnaddr)

    def run(self):
        esptool=ESPTool()
        esptool.percentchange.connect(self.updateFirmwarePer)

        esptool.eraseStartSig.connect(self.eraseStart)

        if self.iserase=="yes":
            self.erasetimer=threading.Timer(0.1,self.eraseTimer)
            self.erasetimer.start()
            try:
                Burn(esptool,str(self.board),self.savepath,self.com,True)
                time.sleep(1)
                self.erasePer=100
                self.firmwareAnyErase.emit(self.erasePer)
                self.erasetimer.cancel()
            except:
                time.sleep(1)
                self.erasePer=-1
                self.firmwareAnyErase.emit(self.erasePer)
                self.erasetimer.cancel()
                self.erasestart=False
                self.exit()
                return
                
        if self.iserase=="yes":
            self.firmwareAnyErase.emit(100)
        try:
            if self.board=="esp32" or self.board=="esp8266" or self.board=="TPYBoardV202":
                Burn(esptool,str(self.board),self.savepath,self.com,False,self.burnaddr)
            else:#microbit
                print("In threaddownloadfirmware:savepath=%s"%self.savepath)
                self.firmwareAnyErase.emit(-2)
                time.sleep(0.5)
                self.goMicrobitUpdate.emit()

        except:
            self.firmwareAnyUpdate.emit(-1)
            self.exit()
            return
        if self.board=="esp8266":
            downOkReset()

        self.exit()

    def cbdownFramware(self,blocknum,blocksize,totalsize):
        print(blocknum)
        print(blocksize)
        print(totalsize)
        
        per=100.0*blocknum*blocksize/self.size
        if per>=100:
            per=100
            self.firmwareAnyDown.emit(per)
            return
  
        self.firmwareAnyDown.emit(per)

    def updateFirmwarePer(self,per):
        print("updateFirmwarePer:%d"%per)
        self.firmwareAnyUpdate.emit(per)

    def eraseStart(self):
        self.erasestart=True

    def eraseTimer(self):
        if self.erasestart==True:
            self.erasePer+=0.5
        
        if self.erasePer>=99:
            self.erasePer=99
            self.firmwareAnyErase.emit(self.erasePer)
            self.erasestart=False
            return
        self.firmwareAnyErase.emit(self.erasePer)
        
        self.erasetimer=threading.Timer(0.1,self.eraseTimer)
        self.erasetimer.start()

class threadDownloadFirmware(QThread):
    firmwareAnyDown = pyqtSignal(int)
    firmwareAnyUpdate = pyqtSignal(int)
    firmwareAnyErase = pyqtSignal(int)
    goMicrobitUpdate = pyqtSignal()

    def __init__(self, url, board, savepath, com, iserase, size, addr, parent):
        super(threadDownloadFirmware,self).__init__(parent)
        self.url=url
        self.board=board
        self.savepath=savepath
        self.com=com
        self.iserase=iserase
        self.size=size
        self.erasePer=0
        self.reDownloadNum=0
        self.downloadOk=False
        self.erasestart=False

        self.erasetimer=None
        
        self.burnaddr=0
        if addr=="0x0":
            self.burnaddr=0
        else:
            self.burnaddr=0x1000

        print("burnaddr2=====%d"%self.burnaddr)


    def run(self):
        self.reDownload()                
        if self.downloadOk==True:

            esptool=ESPTool()
            esptool.percentchange.connect(self.updateFirmwarePer)
            esptool.eraseStartSig.connect(self.eraseStart)
            
            if self.iserase=="yes":
                self.erasetimer=threading.Timer(0.1,self.eraseTimer)
                self.erasetimer.start()
                try:
                    Burn(esptool,str(self.board),self.savepath,self.com,True)
                    time.sleep(1)
                    self.erasePer=100
                    self.firmwareAnyErase.emit(self.erasePer)
                    self.erasetimer.cancel()
                except:
                    time.sleep(1)
                    self.erasePer=-1
                    self.firmwareAnyErase.emit(self.erasePer)
                    self.erasetimer.cancel()
                    self.erasestart=False
                    self.exit()
                    return
                
            if self.iserase=="yes":
                self.firmwareAnyErase.emit(100)
            try:
                if self.board=="esp32" or self.board=="esp8266" or self.board=="TPYBoardV202":
                    Burn(esptool,str(self.board),self.savepath,self.com,False,self.burnaddr)
                else:#microbit
                    print("In threaddownloadfirmware:savepath=%s"%self.savepath)
                    self.firmwareAnyUpdate.emit(-2)
                    time.sleep(0.5)
                    self.goMicrobitUpdate.emit()
            except:
                self.firmwareAnyUpdate.emit(-1)
                self.exit()
                return
            if self.board=="esp8266" or self.board=="TPYBoardV202":
                downOkReset()

        self.exit()

    def reDownload(self):
        if self.reDownloadNum==3:
            self.downloadOk=False
            self.firmwareAnyDown.emit(-1)
            return
        try:
            socket.setdefaulttimeout(5)
            request.urlretrieve(self.url,self.savepath,self.cbdownFramware)
            self.downloadOk=True
            return
        except:
            print("urllib err :%s"%self.url)
            self.reDownloadNum+=1
            self.reDownload()



    def cbdownFramware(self,blocknum,blocksize,totalsize):
        print(blocknum)
        print(blocksize)
        print(totalsize)
        
        per=100.0*blocknum*blocksize/self.size
        if per>=100:
            per=100
            self.firmwareAnyDown.emit(per)
            return
  
        self.firmwareAnyDown.emit(per)

    def updateFirmwarePer(self,per):
        print("updateFirmwarePer:%d"%per)
        self.firmwareAnyUpdate.emit(per)

    def eraseStart(self):
        self.erasestart=True

    def eraseTimer(self):
        if self.erasestart==True:
            self.erasePer+=0.5
        
        if self.erasePer>=99:
            self.erasePer=99
            self.firmwareAnyErase.emit(self.erasePer)
            self.erasestart=False
            return
        self.firmwareAnyErase.emit(self.erasePer)
        
        self.erasetimer=threading.Timer(0.1,self.eraseTimer)
        self.erasetimer.start()
