#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import threading

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class readWriteUart(QThread):
    def __init__(self,queue,parent):
        super(readWriteUart,self).__init__(parent)
        self.ui=parent
        self.model=""
        self.writemsg=""
        self.lastmodel=""
        self.queue=queue
        self.maybeCN=b""
        self.currentBoard="esp32"
        self.connect(self.ui,SIGNAL("changeCurrentBoard"),self.changeCurrentBoard)
        
    def run(self):
        readNum=0
        sendData=""
        execSendData=""
        self.maybeCN=b""
        while True:
            if self.ui.myserial.ser.isOpen():
                if not self.queue.empty():
                    cmd=self.queue.get()
                    print("cmd=%s"%cmd)
                    if cmd.find(":::")>=0:
                        cmd=cmd.split(":::")
                        self.model=cmd[0]
                        if type(cmd[1]) is bytes:
                            self.writemsg=cmd[1]
                        elif type(cmd[1]) is str:
                            self.writemsg=cmd[1].encode('utf-8')
                    else:
                        self.model=cmd
                        self.writemsg=""

                    if self.model=="close":
                        self.lastmodel=""
                        self.model=""
                        break
                    elif self.model=="uitouart":
                        if self.writemsg.decode()=="\x03":
                            self.lastmodel=""
                        elif self.lastmodel=="exec_":
                            self.emit(SIGNAL("uiRecvFromUart"),"program is running,do anything with stop it!1\n")
                            continue
                        try:
                            self.ui.myserial.ser.write(self.writemsg)
                            if self.currentBoard != "microbit":
                                self.ui.myserial.ser.flush()
                        except Exception:
                            self.lastmodel=""
                            self.model=""
                            break
                    elif self.model=="ctrltouart":
                        if self.lastmodel=="exec_":
                            self.emit(SIGNAL("uiRecvFromUart"),"program is running,do anything with stop it!2\n")
                            self.model="uitouart"
                            continue
                        try:
                            self.ui.myserial.ser.write(self.writemsg)
                            if self.currentBoard != "microbit":
                                self.ui.myserial.ser.flush()
                        except Exception:
                            self.lastmodel=""
                            self.model=""
                            break
                    elif self.model=="exec_":
                        if self.lastmodel=="exec_":
                            self.emit(SIGNAL("uiRecvFromUart"),"program is running,do anything with stop it!3\n")
                            self.model="uitouart"
                            continue
                        self.lastmodel="exec_"
                        try:
                            self.ui.myserial.ser.write(self.writemsg)
                            if self.currentBoard != "microbit":
                                self.ui.myserial.ser.flush()
                        except Exception:
                            self.lastmodel=""
                            self.model=""
                            break
                
                if self.model=="" or self.model=="uitouart":
                    #self.emit(SIGNAL("uiRecvFromUart"),"1")
                    #time.sleep(0.1)
                    #continue
                    try:
                        data=self.ui.myserial.ser.read(1)
                    except Exception as e:
                        break
                    if data==b'':
                        continue
                    if ord(data)>127:
                        pass
                    else:
                        data=data.decode()

                    if self.lastmodel=="exec_":
                        execSendData+=str(data)
                        if execSendData.find(">")<0:
                            execSendData=""
                        elif execSendData.find(">>> ")>=0:
                            execSendData=""
                            self.lastmodel=""
                    
                    self.emit(SIGNAL("uiRecvFromUart"),data)
                    if self.ui.myserial.ser.inWaiting()>=128:
                        self.ui.myserial.ser.flushInput()
                elif self.model=="exec_":
                    try:
                        data=self.ui.myserial.ser.read(1)
                    except Exception:
                        break
                    try:
                        data=data.decode()
                    except Exception as e:
                        print(e)
                    execSendData+=str(data)
                    if execSendData.find(">")<0:
                        execSendData=""
                    elif execSendData.find(">>> ")>=0:
                        execSendData=""
                        self.lastmodel=""
                    self.emit(SIGNAL("uiRecvFromUart"),data)
                    if self.ui.myserial.ser.inWaiting()>=128:
                        self.ui.myserial.ser.flushInput()
                elif self.model=="ctrltouart":
                    try:
                        data=self.ui.myserial.ser.read(10)
                    except Exception:
                        break

                    if len(data)>2:
                        if str(data[-2:-1]).find("b'\\xe")>=0:
                            time.sleep(0.001)
                            recv=self.ui.myserial.ser.read(1)
                            if recv==b'':
                                data=data[0:-2]
                            else:
                                data+=recv
                        elif str(data[-1:]).find("b'\\xe")>=0:
                            time.sleep(0.001)
                            recv=self.ui.myserial.ser.read(2)
                            if recv==b'' or len(recv)!=2:
                                data=data[0:-1]
                            else:
                                data+=recv
                        else:
                            pass
                    elif len(data)==2:
                        if str(data[0:1]).find("b'\\xe")>=0:
                            time.sleep(0.001)
                            recv=self.ui.myserial.ser.read(1)
                            if recv==b'':
                                data=data[0:-2]
                            else:
                                data+=recv
                        elif str(data[1:]).find("b'\\xe")>=0:
                            time.sleep(0.001)
                            recv=self.ui.myserial.ser.read(2)
                            if recv==b'' or len(recv)!=2:
                                data=data[0:-1]
                            else:
                                data+=recv
                    else:
                        if data==b'':
                            pass
                        else:
                            if str(data).find("b'\\xe")>=0:
                                time.sleep(0.001)
                                recv=self.ui.myserial.ser.read(2)
                                if recv==b'' or len(recv)!=2:
                                    data=data[0:-1]
                                else:
                                    data+=recv

                    
                    if self.maybeCN!=b'':
                        data=self.maybeCN+data
                    try:
                        data=data.decode()
                        self.maybeCN=b''
                    except Exception as e:
                        #print("data:%s"%data)
                        if len(self.maybeCN)>=3:
                            self.maybeCN=b''
                            continue
                        self.maybeCN=data
                        continue
                    self.maybeCN=b''
                    

                    if data=="" or data==None:
                        readNum+=1
                        if readNum==6:
                            self.emit(SIGNAL("ctrlRecvUartMsg"),sendData)
                            sendData=""
                            readNum=0
                    else:
                        sendData+=data
                        readNum=0
                else:
                    self.emit(SIGNAL("uiRecvFromUart"),"error read model")

            else:
                time.sleep(0.01)

        print("class read out")
        self.lastmodel=""
        self.model=""
        self.exit()

    def changeCurrentBoard(self,board):
        self.currentBoard=board














                        
                    
