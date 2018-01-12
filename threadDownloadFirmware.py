#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import threading
import Esp
import urllib
from urllib import request
import socket
import shutil
import codecs

#from PyQt4 import QtGui, QtCore 
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class threadUserFirmware(QThread):
    def __init__(self, board, savepath, com, iserase, size, parent):
        super(threadUserFirmware,self).__init__(parent)

        self.board=board
        self.savepath=savepath
        self.com=com
        self.iserase=iserase
        self.size=size
        self.erasePer=0
        self.erasestart=False
        self.erasetimer=None

    def run(self):
        esptool=Esp.ESPTool()
        self.connect(esptool,SIGNAL("percentchange"),self.updateFirmwarePer)
        self.connect(esptool,SIGNAL("eraseStart"),self.eraseStart)

        if self.iserase=="yes":
            self.erasetimer=threading.Timer(0.1,self.eraseTimer)
            self.erasetimer.start()
            try:
                Esp.Burn(esptool,str(self.board),self.savepath,self.com,True)
                time.sleep(1)
                self.erasePer=100
                self.emit(SIGNAL("firmwareAnyErase"),self.erasePer)
                self.erasetimer.cancel()
            except:
                time.sleep(1)
                self.erasePer=-1
                self.emit(SIGNAL("firmwareAnyErase"),self.erasePer)
                self.erasetimer.cancel()
                self.erasestart=False
                self.exit()
                return
                
        if self.iserase=="yes":
            self.emit(SIGNAL("firmwareAnyErase"),100)
        try:
            writeFlashAddr=0
            if self.board=="esp32" or self.board=="esp8266":
                if self.board=="esp32":
                    file = codecs.open(self.savepath,'rb')
                    readline=2000
                    while 1:
                        msg=file.readline()
                        if str(msg).find("v1.9.2-445-g84035f0f")>=0:
                            writeFlashAddr = 0x1000
                            break
                        readline=readline-1
                        if readline==0:
                            break
                    file.close()
                Esp.Burn(esptool,str(self.board),self.savepath,self.com,False,writeFlashAddr)
            else:#microbit
                print("In threaddownloadfirmware:savepath=%s"%self.savepath)
                self.emit(SIGNAL("firmwareAnyUpdate"),-2)
                time.sleep(0.5)
                self.emit(SIGNAL("goMicrobitUpdate")) 
        except:
            self.emit(SIGNAL("firmwareAnyUpdate"),-1)
            self.exit()
            return
        if self.board=="esp8266":
            Esp.downOkReset()

        self.exit()

    def cbdownFramware(self,blocknum,blocksize,totalsize):
        print(blocknum)
        print(blocksize)
        print(totalsize)
        
        per=100.0*blocknum*blocksize/self.size
        if per>=100:
            per=100
            self.emit(SIGNAL("firmwareAnyDown"),per)
            return
  
        self.emit(SIGNAL("firmwareAnyDown"),per)

    def updateFirmwarePer(self,per):
        print("updateFirmwarePer:%d"%per)
        self.emit(SIGNAL("firmwareAnyUpdate"),per)

    def eraseStart(self):
        self.erasestart=True

    def eraseTimer(self):
        if self.erasestart==True:
            self.erasePer+=0.5
        
        if self.erasePer>=99:
            self.erasePer=99
            self.emit(SIGNAL("firmwareAnyErase"),self.erasePer)
            self.erasestart=False
            return
        self.emit(SIGNAL("firmwareAnyErase"),self.erasePer)
        
        self.erasetimer=threading.Timer(0.1,self.eraseTimer)
        self.erasetimer.start()

class threadDownloadFirmware(QThread):
    def __init__(self, url, board, savepath, com, iserase, size, parent):
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



    def run(self):

        self.reDownload()                
        if self.downloadOk==True:

            esptool=Esp.ESPTool()
            self.connect(esptool,SIGNAL("percentchange"),self.updateFirmwarePer)
            self.connect(esptool,SIGNAL("eraseStart"),self.eraseStart)
            
            if self.iserase=="yes":
                self.erasetimer=threading.Timer(0.1,self.eraseTimer)
                self.erasetimer.start()
                try:
                    Esp.Burn(esptool,str(self.board),self.savepath,self.com,True)
                    time.sleep(1)
                    self.erasePer=100
                    self.emit(SIGNAL("firmwareAnyErase"),self.erasePer)
                    self.erasetimer.cancel()
                except:
                    time.sleep(1)
                    self.erasePer=-1
                    self.emit(SIGNAL("firmwareAnyErase"),self.erasePer)
                    self.erasetimer.cancel()
                    self.erasestart=False
                    self.exit()
                    return
                
            if self.iserase=="yes":
                self.emit(SIGNAL("firmwareAnyErase"),100)
            try:
                writeFlashAddr=0
                if self.board=="esp32" or self.board=="esp8266":
                    if self.board=="esp32":
                        file = codecs.open(self.savepath,'rb')
                        readline=2000
                        while 1:
                            msg=file.readline()
                            if str(msg).find("v1.9.2-445-g84035f0f")>=0:
                                writeFlashAddr=0x1000
                                break
                            readline=readline-1
                            if readline==0:
                                break
                        file.close()
                    Esp.Burn(esptool,str(self.board),self.savepath,self.com,False,writeFlashAddr)
                else:#microbit
                    print("In threaddownloadfirmware:savepath=%s"%self.savepath)
                    self.emit(SIGNAL("firmwareAnyUpdate"),-2)
                    time.sleep(0.5)
                    self.emit(SIGNAL("goMicrobitUpdate")) 
            except:
                self.emit(SIGNAL("firmwareAnyUpdate"),-1)
                self.exit()
                return
            if self.board=="esp8266":
                Esp.downOkReset()

        self.exit()

    def reDownload(self):
        if self.reDownloadNum==3:
            self.downloadOk=False
            self.emit(SIGNAL("firmwareAnyDown"),-1)
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
            self.emit(SIGNAL("firmwareAnyDown"),per)
            return
  
        self.emit(SIGNAL("firmwareAnyDown"),per)

    def updateFirmwarePer(self,per):
        print("updateFirmwarePer:%d"%per)
        self.emit(SIGNAL("firmwareAnyUpdate"),per)

    def eraseStart(self):
        self.erasestart=True

    def eraseTimer(self):
        if self.erasestart==True:
            self.erasePer+=0.5
        
        if self.erasePer>=99:
            self.erasePer=99
            self.emit(SIGNAL("firmwareAnyErase"),self.erasePer)
            self.erasestart=False
            return
        self.emit(SIGNAL("firmwareAnyErase"),self.erasePer)
        
        self.erasetimer=threading.Timer(0.1,self.eraseTimer)
        self.erasetimer.start()
