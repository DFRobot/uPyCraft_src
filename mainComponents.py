import sys
import os
import shutil
import time

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerPython
from PyQt5.QtWidgets import *



rootDirectoryPath  =os.path.expanduser("~")
rootDirectoryPath  =rootDirectoryPath.replace("\\","/")
currentExamplesPath="%s/AppData/Local/uPyCraft/examples"%rootDirectoryPath

class myTerminal(QTextEdit):
    customContextMenuRequestedSig = pyqtSignal(QPoint)
    def __init__(self,queue,parent):        
        super(myTerminal,self).__init__(parent)
        self.eventFilterEnable=False
        self.setStyleSheet("""QTextEdit{background-color: qlineargradient(x1: 0, x2: 1, stop: 0 #262D34, stop: 1 #222529);
                           border-style:none;
                           color:white;}
                           QScrollBar:vertical{background-color:rgb(94,98,102);
                               border:0px;
                               width: 15px;
                               margin:0px 0px 0px 0px;
                           }
                           QScrollBar::add-page:vertical{background-color:rgb(61,62,64);
                               width: 15px;
                               margin:0px 0px 0px 0px;
                           }
                           QScrollBar::sub-page:vertical{background-color:rgb(61,62,64);
                               width: 15px;
                               margin:0px 0px 0px 0px;
                           }
                           """)
        #self.setReadOnly(False)
        self.installEventFilter(self)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

        p=QPalette()
        p.setColor(QPalette.Inactive,QPalette.Highlight,QColor(102,184,255))
        self.setPalette(p)
        
        self.setAcceptDrops(False)
        
        self.terminalRightMenu=None
        self.createTerminalRightMenu()

        self.ui=parent
        self.queue=queue
        self.currentBoard="esp32"
        self.ui.changeCurrentBoard.connect(self.changeBoard)
        self.ui.initRecvdata.connect(self.initRecvdata)
        self.ui.initMessycode.connect(self.initMessycode)

        self.keyPressMsg=""
        self.recvdata=""
        self.messycode=b''
        self.isChinese=0
        
        self.cursor=None
        self.startPosition=0
        
        self.terminalSelect=False
        
    def createTerminalRightMenu(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequestedSig.connect(self.slotTerminalRightClickMenu)
        self.terminalRightMenu=QMenu(self)
        self.terminalRightMenu.setStyleSheet(
                """QMenu{background-color:rgb(67,67,67);
                        color:white;}
                QMenu::item{padding:4px 16px;}
                QMenu::item::selected{background-color:rgb(124,124,124);}"""
            )

        terminalCopy=QAction(QIcon(":/copy.png"),self.tr("copy"),self)
        terminalCopy.triggered.connect(self.slotCopy)
        
        terminalPaste=QAction(QIcon(":/copy.png"),self.tr("paste"),self)
        terminalPaste.triggered.connect(self.slotPaste)

        self.terminalRightMenu.addAction(terminalCopy)
        self.terminalRightMenu.addAction(terminalPaste)
    def slotTerminalRightClickMenu(self,point):
        self.terminalRightMenu.exec_(self.mapToGlobal(point))

    def slotCopy(self):
        self.copy()
        self.ui.cutCopyPasteMsg = QApplication.clipboard().setText(QApplication.clipboard().text())
        self.terminalSelect=False

    def slotPaste(self):
        if not self.ui.myserial.ser.isOpen():
            return
        self.keyPressMsg=""
        for i in str(QApplication.clipboard().text()):
            if i=="\x0a":
                i="\x0d\x0a"
            self.ui.readwriteQueue.put("uitouart:::%s"%i)
        

    def setEventFilterEnable(self,enable):
        self.eventFilterEnable=enable

    def eventFilter(self,watch,event):
        if not self.eventFilterEnable:
            return QMainWindow.eventFilter(self,watch,event)
        if event.type()==QEvent.KeyPress:
            #print ("event.text:%s"%(event.text()))
            #print ("evevt.type:%d"%event.type())
            #print (event.key())
            self.keyPress(event)
            return True
        elif event.type()==QEvent.InputMethod:
            print ("event.text0")
            e=QInputMethodEvent(event)
            print(e.commitString())
            self.queue.put("uitouart:::%s"%e.commitString())
            return True
        else:
            return QMainWindow.eventFilter(self,watch,event)

    def changeBoard(self,board):
        #print("changeBoard")
        self.currentBoard=board

    def initRecvdata(self):
        print("initRecvdata")
        self.recvdata=""
    def initMessycode(self):
        print("initMessycode")
        self.messycode=b""

    def keyPress(self,event):
        print("keypress")
        if self.terminalSelect:
            self.terminalSelect=False
            self.setTextCursor(self.ui.cursor)
        
        self.messycode=b''
        if event.key()==Qt.Key_Backspace:
            self.keyPressMsg="\x08"
            self.queue.put("uitouart:::%s"%self.keyPressMsg)
        elif event.key()==Qt.Key_Left:
            self.keyPressMsg='\x1b\x5b\x44'
            self.queue.put("uitouart:::%s"%self.keyPressMsg)
        elif event.key()==Qt.Key_Right:
            self.keyPressMsg='\x1b\x5b\x43'
            self.queue.put("uitouart:::%s"%self.keyPressMsg)
        elif event.key()==Qt.Key_Delete:
            self.keyPressMsg="\x1b\x5b\x33\x7e"
            self.queue.put("uitouart:::%s"%self.keyPressMsg)
        elif event.key()==Qt.Key_Up:
            self.keyPressMsg="\x1b\x5b\x41"
            self.queue.put("uitouart:::%s"%self.keyPressMsg)
        elif event.key()==Qt.Key_Down:
            self.keyPressMsg="\x1b\x5b\x42"
            self.queue.put("uitouart:::%s"%self.keyPressMsg)
        elif event.key()==Qt.Key_Tab:
            self.keyPressMsg="\x09"
            self.queue.put("uitouart:::%s"%self.keyPressMsg)
        elif event.text()=="":
            self.keyPressMsg="else"
            return
        else:
            self.keyPressMsg="else"
            if event.key()==Qt.Key_Return or event.key()==Qt.Key_Enter:
                self.ui.cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                self.moveCursor(QTextCursor.End)
            self.queue.put("uitouart:::%s"%str(event.text()))

    def uiRecvFromUart(self,data):
        if data=="" or data==b'':
            return

        if (type(data) is bytes) and (str(data).find("b'\\xe")>=0):
            self.keyPressMsg="else"
            self.messycode=b''
            self.isChinese=1
        if self.isChinese==1:
            if type(data) is bytes:
                try:
                    self.messycode+=data
                except:
                    self.messycode+=data.decode("utf-8")

                if len(self.messycode)<3:
                    return
                else:
                    try:
                        self.insertPlainText(self.messycode.decode("utf-8"))
                    except Exception as e:
                        print(e)
                    self.isChinese=0
                    return
            else:
                self.isChinese=0
                self.messycode=b''
        
        if self.keyPressMsg=="\x08" and self.ui.cursor.atEnd()==True:#Backspace
            mycursor=self.textCursor()
            self.recvdata+=data
            if self.currentBoard=="microbit":
                if self.recvdata=="\x08\x20\x08":
                    mycursor.deletePreviousChar()
                    self.recvdata=""
                elif self.recvdata=="\x08\x08\x08\x08\x20\x20\x20\x20\x08\x08\x08\x08":
                    for i in range(0,4):
                        mycursor.deletePreviousChar()
                    self.recvdata=""
            else:
                if self.recvdata.find("\x08\x1b\x5b\x4b")==0:
                    mycursor.deletePreviousChar()
                    self.recvdata=""
                elif self.recvdata.find("\x08\x1b\x5b\x4b")>0:
                    for i in range(self.recvdata.find("\x08\x1b\x5b\x4b")+1):
                        if self.recvdata[i]=="\x08":
                            mycursor.deletePreviousChar()
                    self.recvdata=""
        elif self.keyPressMsg=="\x08" and not self.ui.cursor.atEnd():#Backspace
            mycursor=self.textCursor()
            self.recvdata+=data
            if self.currentBoard=="microbit":
                if len(self.recvdata)>5:
                    if self.recvdata[-2:]=="\x08\x08":
                        pass
                    elif self.recvdata[-1]=="\x08" and self.recvdata[-2]!="\x20":
                        for i in range(self.recvdata.find("\x20")):
                            mycursor.deletePreviousChar()
                        self.recvdata=""
                        self.keyPressMsg="else"
                    else:
                        pass
                else:
                    pass
            else:
                if self.recvdata.find("\x1b\x5b")>0 and self.recvdata[-1]=="\x08":
                    for i in range(self.recvdata.find("\x1b\x5b")):
                        if self.recvdata[i]=="\x08":
                            mycursor.deletePreviousChar()
                    self.recvdata="" 
                    self.keyPressMsg="else"
                elif self.recvdata.count("\x1b\x5b")==2 and self.recvdata[-1]=="\x44":
                    for i in range(self.recvdata.find("\x1b\x5b")):
                        if self.recvdata[i]=="\x08":
                            mycursor.deletePreviousChar()
                    self.recvdata=""
                #else:
                #    print("9999")
        elif self.keyPressMsg=="\x09" and not self.ui.cursor.atEnd():#debug
            self.recvdata+=data
            if self.recvdata=="\x08":
                lastLineCursorNum=self.ui.cursor.columnNumber()
                allMsg=self.toPlainText()
                showMsg=""
                movecursorNum=0
                allMsg=allMsg.split("\n")
                for i in allMsg:
                    if i==allMsg[-1]:
                        showMsg+=i[0:-1]
                        movecursorNum=len(i[lastLineCursorNum:])
                    else:
                        showMsg+=i+"\n"
                self.setPlainText(showMsg)
                
                self.ui.cursorLeftOrRight-=movecursorNum
                self.ui.cursor=self.textCursor()
                self.moveCursor(QTextCursor.Left,QTextCursor.MoveAnchor)
                self.recvdata=""
            elif self.recvdata[0]=="\x1b":
                if self.recvdata[-1]=="\x44":
                    movecursorNum=int(self.recvdata[self.recvdata.find("\x1b")+2:-1])
                    lastLineCursorNum=self.ui.cursor.columnNumber()
                    allMsg=self.toPlainText()
                    showMsg=""
                    allMsg=allMsg.split("\n")
                    for i in allMsg:
                        if i==allMsg[-1]:
                            showMsg+=i[0:lastLineCursorNum]
                        else:
                            showMsg+=i+"\n"
                    self.setPlainText(showMsg)
                    self.keyPressMsg="else"
                    self.recvdata=""

                    self.ui.cursorLeftOrRight-=movecursorNum
                    self.ui.cursor=self.textCursor()
                    self.moveCursor(QTextCursor.Left,QTextCursor.MoveAnchor)
            else:
                self.ui.cursor.insertText(self.recvdata)
                self.recvdata=""
        elif self.keyPressMsg=="\x1b\x5b\x33\x7e" and not self.ui.cursor.atEnd():#Delete
            self.recvdata+=data
            allMsg=self.toPlainText()
            allMsg=allMsg.split("\n")
            showMsg=""
            lastLineCursorNum=self.ui.cursor.columnNumber()

            if self.currentBoard=="microbit":
                if (len(allMsg[-1])-lastLineCursorNum==1) and self.recvdata=="\x20\x08":
                    self.ui.cursor.deleteChar()
                    self.keyPressMsg="else"
                    self.recvdata=""
                else:
                    if self.recvdata[-2:]=="\x08\x08":
                        pass
                    elif self.recvdata[-1]=="\x08" and self.recvdata[-2]!="\x20":
                        self.ui.cursor.deleteChar()
                        self.keyPressMsg="else"
                        self.recvdata=""
                    else:
                        pass
            else:
                if self.recvdata=="\x1b\x5b\x4b" and (len(allMsg[-1])-lastLineCursorNum==1):
                    self.ui.cursor.deleteChar()
                    self.keyPressMsg="else"
                    self.recvdata=""
                elif len(self.recvdata)>3 and self.recvdata[-1]=="\x08":#这里，不应该让keypressmsg=else
                    self.ui.cursor.deleteChar()
                    self.keyPressMsg="else"
                    self.recvdata=""
                elif len(self.recvdata)>3 and self.recvdata[3:].find("\x1b\x5b")>0 and self.recvdata[-1]=="\x44":
                    self.ui.cursor.deleteChar()
                    self.keyPressMsg="else"
                    self.recvdata=""
                elif self.recvdata=="\x08":
                    self.recvdata=""
                else:
                    pass
        elif self.keyPressMsg=="\x1b\x5b\x44":#Key_Left
            if data=="\x08":
                self.ui.cursorLeftOrRight-=1
                self.ui.cursor=self.textCursor()
                self.moveCursor(QTextCursor.Left,QTextCursor.MoveAnchor)
        elif self.keyPressMsg=="\x1b\x5b\x43":#Key_Right
            self.ui.cursorLeftOrRight+=1
            self.ui.cursor=self.textCursor()
            self.moveCursor(QTextCursor.Right, QTextCursor.MoveAnchor)
        elif self.keyPressMsg=="\x1b\x5b\x41":#Key_Up
            if data == "\x08":
                myBottomMsg=self.toPlainText()
                msgNum=self.document().lineCount()
                plainMsg=""
                mySplite=myBottomMsg.split("\n")
                for mysplite in mySplite:
                    msgNum-=1
                    if msgNum != 0:
                        plainMsg+=mysplite+"\n"
                plainMsg+=">>> "
                self.setPlainText(plainMsg)
            elif data == "\x1b" or self.recvdata.find("\x1b")>=0:
                self.recvdata+=data
                if self.recvdata.find("[K")>=0:
                    self.recvdata=""
                    myBottomMsg=self.toPlainText()
                    msgNum=self.document().lineCount()
                    plainMsg=""
                    mySplite=myBottomMsg.split("\n")
                    for mysplite in mySplite:
                        msgNum-=1
                        if msgNum != 0:
                            plainMsg+=mysplite+"\n"
                    plainMsg+=">>> "
                    self.setPlainText(plainMsg)
                elif self.recvdata.find("D")>=0:
                    self.recvdata=""
                    myBottomMsg=self.toPlainText()
                    msgNum=self.document().lineCount()
                    plainMsg=""
                    mySplite=myBottomMsg.split("\n")
                    for mysplite in mySplite:
                        msgNum-=1
                        if msgNum != 0:
                            plainMsg+=mysplite+"\n"
                    plainMsg+=">>> "
                    self.setPlainText(plainMsg)
            else:
                self.ui.cursor.insertText(data)
        elif self.keyPressMsg=="\x1b\x5b\x42":#Key_Down
            if data == "\x08":
                myBottomMsg=self.toPlainText()
                msgNum=self.document().lineCount()
                plainMsg=""
                mySplite=myBottomMsg.split("\n")
                for mysplite in mySplite:
                    msgNum-=1
                    if msgNum != 0:
                        plainMsg+=mysplite+"\n"
                plainMsg+=">>> "
                self.setPlainText(plainMsg)
            elif data == "\x1b" or self.recvdata.find("\x1b")>=0:
                self.recvdata+=data
                if self.recvdata.find("D")>=0:
                    self.recvdata=""
                    myBottomMsg=self.toPlainText()
                    msgNum=self.document().lineCount()
                    plainMsg=""
                    mySplite=myBottomMsg.split("\n")
                    for mysplite in mySplite:
                        msgNum-=1
                        if msgNum != 0:
                            plainMsg+=mysplite+"\n"
                    plainMsg+=">>> "
                    self.setPlainText(plainMsg)
                elif self.recvdata.find("[K")>=0:
                    self.recvdata=""
                    myBottomMsg=self.toPlainText()
                    msgNum=self.document().lineCount()
                    plainMsg=""
                    mySplite=myBottomMsg.split("\n")
                    for mysplite in mySplite:
                        msgNum-=1
                        if msgNum != 0:
                            plainMsg+=mysplite+"\n"
                    plainMsg+=">>> "
                    self.setPlainText(plainMsg)
            else:
                self.ui.cursor.insertText(data) 
        else:
            if not self.ui.cursor.atEnd():
                self.recvdata+=data
                if self.recvdata.find("\x08")>=0 and len(self.recvdata)>1 and self.recvdata[1:].find("\x08")>=0:
                    if self.messycode!=b'':
                        self.recvdata=''
                        self.messycode=b''
                        return
                    self.recvdata=self.recvdata[0]
                    self.ui.cursor.insertText(self.recvdata)
                    self.recvdata=""
                elif self.recvdata=="\x08":
                    self.recvdata=""
                elif self.recvdata.find("[")>0 and self.recvdata[-1]=="\x44":
                    if self.messycode!=b'':
                        self.recvdata=''
                        self.messycode=b''
                        return
                    self.recvdata=self.recvdata[0]
                    self.ui.cursor.insertText(self.recvdata)
                    self.recvdata=""
                elif self.recvdata=="\x1b\x5b\x4b":
                    self.keyPressMsg="\x1b\x5b\x33\x7e"
            else:
                if data=="\n":
                    data=""
                try:
                    self.insertPlainText(data)
                except:
                    print('recv unexpected word.')
    
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:
            self.startCursorPosition =event.pos()
            self.cursor = self.cursorForPosition(self.startCursorPosition)
            self.startPosition = self.cursor.position()
            self.setCursor.emit()
            
    def mouseMoveEvent(self,event):
        if event.button()==Qt.NoButton:
            self.terminalSelect=True
            self.endCursorPosition = event.pos()
            self.cursor = self.cursorForPosition(self.endCursorPosition)
            position = self.cursor.position()
            self.cursor.setPosition(self.startPosition)
            self.cursor.setPosition(position, QTextCursor.KeepAnchor)
            self.setTextCursor(self.cursor)
            self.cursor.select(QTextCursor.WordUnderCursor)

    def mouseReleaseEvent(self,event):
        if event.button()==Qt.LeftButton:
            pass
    
        
    
class myTreeView(QTreeView):
    customContextMenuRequestedSig = pyqtSignal(QPoint)
    def __init__(self,parent):
        super(myTreeView,self).__init__(parent)
        self.ui=parent
        
        self.setHeaderHidden(True)
        self.setStyleSheet("""
            QTreeView{
                background-color: qlineargradient(y1: 0, y2: 1,stop: 0 #0D0B0B, stop: 1 #5D5C5C);
                border-width:1px;
                border-color:#888888;
                border-style:solid;
                color:white;
            }

            QTreeView::branch:closed:has-children {
                border-image: none;
                image: url(':/treeBranchOpen.png');
            }

            QTreeView::branch:open:has-children {
                border-image: none;
                image: url(':/treeBranchClose.png');
            }""")

        
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)

        self.filename=""
        self.dragFrom=""
        self.dropDir=""
        #self.connect(self,SIGNAL("clicked(QModelIndex)"),self.chooseFile)

        # self.connect(self,SIGNAL("pressed(QModelIndex)"),self.treepressed)
        self.pressed.connect(self.treepressed)

    def setmodel(self,model):
        self.setModel(model)

    #def mousePressEvent(self,event):
    #    if event.button()==Qt.LeftButton:
    #        print("left")
	#    elif event.button()==Qt.RightButton:
    #        print("right")
    #    else:
    #        print("else")
	#   return QMainWindow.eventFilter(self,event)
    def createRightMenu(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.runFile=QAction(self.tr("Run"),self)
        self.runFile.triggered.connect(self.rightMenuRunFile)

        self.openFile=QAction(self.tr("Open"),self) 
        self.openFile.triggered.connect(self.rightMenuOpenFile)

        self.closeFile=QAction(self.tr("Close"),self)
        self.closeFile.triggered.connect(self.rightMenuCloseFile)

        self.deleteFile=QAction(self.tr("Delete"),self)
        self.deleteFile.triggered.connect(self.rightMenuDeleteFile)

        self.defaultProgram=QAction(self.tr("Default Run"),self)
        self.defaultProgram.triggered.connect(self.rightMenuDefaultProgram)

        self.rename=QAction(self.tr("Rename"),self)
        self.rename.triggered.connect(self.rightMenuRename)

        self.newDir=QAction(self.tr("New Dir"),self)
        self.newDir.triggered.connect(self.rightMenuNewDir)

        self.rightClickMenu=QMenu(self)
        self.rightClickMenu.setStyleSheet(
                """QMenu{background-color:rgb(67,67,67);
                        color:white;}
                QMenu::item{padding:4px 16px;}
                QMenu::item::selected{background-color:rgb(127,127,127);}"""
            )
        self.rightClickMenu.addAction(self.runFile)
        self.rightClickMenu.addAction(self.openFile)
        self.rightClickMenu.addAction(self.closeFile)
        self.rightClickMenu.addAction(self.deleteFile)
        self.rightClickMenu.addAction(self.defaultProgram)
        self.rightClickMenu.addAction(self.rename)
        self.rightClickMenu.addAction(self.newDir)

        self.customContextMenuRequestedSig.connect(self.slotRightClickMenu)

    def slotRightClickMenu(self,point):
        self.rightClickMenu.clear()
        if (self.ui.fileName=="." or self.ui.fileName=="/flash") and self.ui.myserial.ser.isOpen():
            self.rightClickMenu.addAction(self.newDir)
        elif (self.ui.fileName=="." or self.ui.fileName=="/flash") and not self.ui.myserial.ser.isOpen():
            pass
        elif self.ui.fileName=="/sd" or \
             (((sys.platform=="linux" and self.ui.fileName.find(rootDirectoryPath)>=0) or (sys.platform=="win32" and self.ui.fileName.find(":")>=0) or (sys.platform=="darwin" and self.ui.fileName.find(rootDirectoryPath)>=0)) and self.ui.fileName.split("/")[-1]=="uPy_lib"):
            pass
        elif ((sys.platform=="linux" and self.ui.fileName.find(rootDirectoryPath)>=0) or (sys.platform=="win32" and self.ui.fileName.find(":")>=0) or (sys.platform=="darwin" and self.ui.fileName.find(rootDirectoryPath)>=0)) and self.ui.fileName.find("uPy_lib")>0:
            self.rightClickMenu.addAction(self.openFile)
            self.rightClickMenu.addAction(self.closeFile)
        elif ((sys.platform=="linux" and self.ui.fileName.find(rootDirectoryPath)>=0) or (sys.platform=="win32" and self.ui.fileName.find(":")>=0) or (sys.platform=="darwin" and self.ui.fileName.find(rootDirectoryPath)>=0)) and self.ui.fileName.split("/")[-1]=="workSpace":
            self.rightClickMenu.addAction(self.openFile)
        elif ((sys.platform=="linux" and self.ui.fileName.find(rootDirectoryPath)>=0) or (sys.platform=="win32" and self.ui.fileName.find(":")>=0) or (sys.platform=="darwin" and self.ui.fileName.find(rootDirectoryPath)>=0)) and self.ui.fileName.find("workSpace")>0:
            self.rightClickMenu.addAction(self.openFile)
            self.rightClickMenu.addAction(self.closeFile)
            self.rightClickMenu.addAction(self.deleteFile)
        else:
            self.rightClickMenu.addAction(self.runFile)
            self.rightClickMenu.addAction(self.openFile)
            self.rightClickMenu.addAction(self.closeFile)
            self.rightClickMenu.addAction(self.deleteFile)
            self.rightClickMenu.addAction(self.defaultProgram)
            self.rightClickMenu.addAction(self.rename)
            self.rightClickMenu.addAction(self.newDir)

        self.rightClickMenu.exec_(self.mapToGlobal(point))

    def rightMenuRunFile(self):
        self.ui.treeRightMenuRunFile()

    def rightMenuOpenFile(self):
        self.ui.treeRightMenuOpenFile()
        
    def rightMenuCloseFile(self):
        self.ui.treeRightMenuCloseFile()
        
    def rightMenuDeleteFile(self):
        self.ui.treeRightMenuDeleteFile()
            
    def rightMenuDefaultProgram(self):
        self.ui.treeRightMenuDefaultProgram()
        
    def rightMenuRename(self):
        self.ui.treeRightMenuRename()
        
    def rightMenuNewDir(self):
        self.ui.treeRightMenuNewDir()
    

    def getQmodelIndexParent(self,index):
        if index.data() != None:
            self.ui.fileName="/"+str(index.data())+self.ui.fileName
            self.getQmodelIndexParent(index.parent())
        else:
            return

    def chooseFile(self,index):
        self.ui.fileName=""
        self.getQmodelIndexParent(index)
        print("--4--%s"%self.ui.fileName)
        dirList=self.ui.fileName.split("/")

        if dirList[1]=="device":
            self.ui.fileName=self.ui.fileName[7:]
            self.ui.fileName=self.ui.rootDir+self.ui.fileName
        elif dirList[1]=="sd":
            pass
        elif dirList[1]=="uPy_lib":
            self.ui.fileName="%s/AppData/Local/uPyCraft/examples"%rootDirectoryPath+self.ui.fileName
        elif dirList[1]=="workSpace":
            if self.ui.createWorkSpacePath():
                self.ui.fileName=self.ui.workspacePath[0:-10]+self.ui.fileName
                self.ui.fileName=self.ui.fileName.replace("\\","/")
                self.ui.fileName=self.ui.fileName.replace("//","/")
            else:
                self.ui.fileName=""
        else:
            pass

        print("--5--%s"%self.ui.fileName)

    def treepressed(self,index):
        self.chooseFile(index)
        self.dropDir=""
        self.getDropDir(index)

    def dragEnterEvent(self,event):
        if event.mimeData().hasFormat("text/uri-list")==True:#External drag
            self.dragFrom="External"
            event.acceptProposedAction()
        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist")==True:#Internal drag
            self.dragFrom="Internal"
            event.acceptProposedAction()
        else:
            self.dragFrom=""
            event.ignore()
    def dragMoveEvent(self,event):
        pass
    def dragLeaveEvent(self,event):
        pass
    def dropEvent(self,event):
        if event.mimeData().hasUrls:
            urls=event.mimeData().urls()
            dropDownFileName=""
            for url in urls:
                dropDownFileName=url.toLocalFile()

            index=self.indexAt(self.mapFrom(self,event.pos()))

            if self.dragFrom=="External":
                self.dropDir=""
                self.getDropDir(index)
                print("dropdir=%s"%self.dropDir)
                if self.dropDir=="":
                    self.ui.terminal.append("drop to this place is not support")
                    return

                filename=""
                dorpdownfilename=""
                dirList=self.dropDir.split("/")
                if dirList[1]=="device" and str(dirList[-1]).find(".")<0:
                    self.dropDir=self.dropDir[7:]
                    dorpdownfilename=dropDownFileName.split("/")
                    filename=self.ui.rootDir+self.dropDir+"/"+dorpdownfilename[-1]
                elif dirList[1]=="device" and str(dirList[-1]).find(".")>0:
                    self.dropDir=self.dropDir[7:str(self.dropDir).find(dirList[-1])-1]
                    dorpdownfilename=dropDownFileName.split("/")
                    filename=self.ui.rootDir+self.dropDir+"/"+dorpdownfilename[-1]
                elif dirList[1]=="workSpace" and str(dirList[-1]).find(".")<0:
                    shutil.copyfile(dropDownFileName,self.ui.workspacePath[0:-10]+self.dropDir+"/"+dropDownFileName.split("/")[-1])
                    self.ui.createWorkSpaceMenu()
                    return
                elif dirList[1]=="workSpace" and str(dirList[-1]).find(".")>0:
                    newPath=self.ui.workspacePath[0:-10]
                    for i in self.dropDir.split("/"):
                        if i=="":
                            pass
                        elif i==self.dropDir.split("/")[-1]:
                            break
                        else:
                            newPath=newPath+"/"+i
                    newPath=newPath+"/"+dropDownFileName.split("/")[-1]
                    shutil.copyfile(dropDownFileName,newPath)
                    self.ui.createWorkSpaceMenu()
                    return
                else:
                    self.ui.terminal.append("drop to this place is not support")
                    return

                if not self.ui.myserial.ser.isOpen():
                    self.ui.terminal.append("serial not open,can not download file")
                    return
                self.ui.changeDragDropModel.emit(True)
                self.ui.uitoctrlQueue.put("dropdownfile:::%s:::%s"%(filename,dropDownFileName))
                print("filename=%s"%filename)
                print("dropDownFileName=%s"%dropDownFileName)
                
            elif self.dragFrom=="Internal":
                if not self.ui.myserial.ser.isOpen():
                    self.ui.terminal.append("serial not open,can not drag file")
                    return
                oldDragFileName=self.dropDir
                print("oldDragFileName=%s"%oldDragFileName)
                if oldDragFileName=="/device" or oldDragFileName=="/sd" or \
                   oldDragFileName=="/uPy_lib" or oldDragFileName=="workSpace":
                    self.ui.terminal.append("dir device,sd,uPy_lib can't be move.")
                    return
                self.dropDir=""
                self.getDropDir(index)
                newDropFileName=self.dropDir
                if self.dropDir=="":
                    self.ui.terminal.append("error place")
                    return
                try: 
                    purposeFileName=str(self.dropDir).split("/")[1]
                except Exception:
                    self.ui.terminal.append("drag error")
                    return
                if purposeFileName=="sd" or purposeFileName=="uPy_lib" or purposeFileName=="workSpace":
                    self.ui.terminal.append("file can't be move to sd or uPy_lib or workSpace.")
                    return

                if str(oldDragFileName).find(".")<0:
                    self.ui.terminal.append("now version only suport drag file,no suport for dir.")
                    return

                dirListDrag=oldDragFileName.split("/")
                dirListDrop=newDropFileName.split("/")                
                if dirListDrag[1]=="device" and str(dirListDrop[-1]).find(".")<0:
                    if oldDragFileName[0:str(oldDragFileName).find(dirListDrag[-1])-1]==newDropFileName:
                        self.ui.terminal.append("the same dir,not move.")
                        return
                    oldDragFileName=oldDragFileName[7:]
                    oldDragFileName=self.ui.rootDir+oldDragFileName
                    newDropFileName=newDropFileName[7:]
                    newDropFileName=self.ui.rootDir+newDropFileName

                    self.ui.uitoctrlQueue.put("dragChangeDir:::%s:::%s"%(oldDragFileName,newDropFileName))
                elif dirListDrag[1]=="device" and str(dirListDrop[-1]).find(".")>0:
                    if oldDragFileName[0:str(oldDragFileName).find(dirListDrag[-1])-1]\
                       ==newDropFileName[0:str(newDropFileName).find(dirListDrop[-1])-1]:
                        self.ui.terminal.append("the same dir,not move.")
                        return
                    oldDragFileName=oldDragFileName[7:]
                    oldDragFileName=self.ui.rootDir+oldDragFileName
                    newDropFileName=newDropFileName[7:str(newDropFileName).find(dirListDrop[-1])-1]
                    newDropFileName=self.ui.rootDir+newDropFileName

                    self.ui.uitoctrlQueue.put("dragChangeDir:::%s:::%s"%(oldDragFileName,newDropFileName))
                elif dirListDrag[1]=="sd":
                    pass
                elif dirListDrag[1]=="uPy_lib" or dirListDrag[1]=="workSpace":#device外部拖入，需下载
                    if dirListDrag[1]=="uPy_lib":
                        oldDragFileName="%s/AppData/Local/uPyCraft/examples"%rootDirectoryPath+oldDragFileName
                    elif dirListDrag[1]=="workSpace":
                        oldDragFileName=self.ui.workspacePath[0:-10]+oldDragFileName
                    if str(dirListDrop[-1]).find(".")<0:
                        newDropFileName=newDropFileName[7:]
                        newDropFileName=self.ui.rootDir+newDropFileName
                    else:
                        newDropFileName=newDropFileName[7:str(newDropFileName).find(dirListDrop[-1])-1]
                        newDropFileName=self.ui.rootDir+newDropFileName
                    self.ui.changeDragDropModel.emit(True)
                    self.ui.uitoctrlQueue.put("dragChangeDir:::%s:::%s"%(oldDragFileName,newDropFileName))
                else:
                    pass
            else:
                pass
        else:
            event.ignore()      

    def getDropDir(self,index):
        if index.data() != None:
            self.dropDir="/"+index.data()+self.dropDir
            self.getDropDir(index.parent())
        else:
            return
        
class myTabWidget(QTabWidget):
    def __init__(self,editorRightMenu,fileitem,parent):
        super(myTabWidget,self).__init__(parent)
        self.ui=parent
        self.setAcceptDrops(True)
        self.editorRightMenu=editorRightMenu
        self.fileitem=fileitem
        self.currentTab=-1

        self.line=0
        self.index=0

        self.tabCloseRequested.connect(self.closeTab)
        self.currentChanged.connect(self.currentTabChange)

    def closeTab(self,tabId):
        if tabId<0:
            return
        tabname = self.tabText(tabId)

        tabTip = self.tabToolTip(tabId)
        self.removeTab(tabId)
        
        if tabname=="untitled":
            pass
        else:
            if tabTip in self.fileitem.list:
                self.fileitem.list.remove(tabTip)
                self.fileitem.size-=1

    def dragEnterEvent(self,event):
        print("tabwidget dragenterevent1.")
        if event.mimeData().hasFormat("text/uri-list")==True:#External drag
            event.acceptProposedAction()
        elif event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist")==True:#Internal drag
            event.ignore()
        else:
            event.ignore()
    def dragMoveEvent(self,event):
        event.acceptProposedAction()
    def dragLeaveEvent(self,event):
        pass
    def dropEvent(self,event):
        print("tabwidget dropevent1.")
        if event.mimeData().hasUrls:
            urls=event.mimeData().urls()
            dropOpenFileName=""
            for url in urls:
                dropOpenFileName=url.toLocalFile()
            print("dropOpenFileName=%s"%dropOpenFileName)
            print(type(dropOpenFileName))
            if dropOpenFileName.find(".py")<0 and\
               dropOpenFileName.find(".txt")<0 and\
               dropOpenFileName.find(".json")<0 and\
               dropOpenFileName.find(".ini")<0:
                print("current version can not open this file")
                return
            self.ui.pcOpenFile(dropOpenFileName)

    def currentTabChange(self,tabId):
        self.currentTab=tabId
        print(self.currentTab)
    def createNewTab(self,filename,msg,lexer):
        if type(msg) is bytes:
            msg=msg.decode(encoding='utf-8')
        #if str(msg).find("\r\n")>=0:
        #    msg=msg.replace('\n','')
        #elif str(msg).find("\n")>=0 and str(msg).find("\r")<0:
        #    msg=msg.replace("\n","\r")
        #else:
        #    print("creatNewTab has other endswith.")
        msg=msg.replace("\r\n","\r")
        msg=msg.replace("\n","\r")

        #editor=QsciScintilla()
        editor=myQsciScintilla()
        editor.setUtf8(True)
        editor.setLexer(lexer)
        editor.setMarginsBackgroundColor(QColor(39,43,48))#行号背景色
        editor.setMarginsForegroundColor(QColor(255,255,255))#行号前景色
        editor.setAutoCompletionThreshold(2)
        editor.setAutoCompletionSource(QsciScintilla.AcsAll)
        editor.setEolMode(QsciScintilla.EolUnix)
        
        #显示缩进参考线
        editor.SendScintilla(QsciScintilla.SCI_SETINDENTATIONGUIDES,QsciScintilla.SC_IV_LOOKFORWARD)
        #设置匹配项的背景色
        editor.setMatchedBraceBackgroundColor(QColor(30,120,184))


        
        

        if str(filename).find("/")>=0:
            tabname=filename.split("/")
            tabname=tabname[-1]
        elif str(filename)=="untitled":
            tabname="untitled"
        else:
            tabname=filename

        self.addTab(editor,tabname)
        self.setTabToolTip(self.count()-1,filename)

        if filename=="untitled":
            self.tabBar().setTabTextColor(self.count()-1, QColor(Qt.red))
            self.setTabIcon(self.count()-1, QIcon(':/pc.png'))
            if self.ui.currentBoard=="microbit":
                msg="from microbit import *\r#write your program:\r"
        elif (sys.platform=="linux" and str(filename).find(rootDirectoryPath)>=0) or (sys.platform=="win32" and str(filename).find(":")>0) or (sys.platform=="darwin" and str(filename).find(rootDirectoryPath)>=0):
            self.tabBar().setTabTextColor(self.count()-1, QColor(Qt.red))
            self.setTabIcon(self.count()-1, QIcon(':/pc.png'))
        else:
            self.tabBar().setTabTextColor(self.count()-1, QColor(Qt.blue))
            self.setTabIcon(self.count()-1, QIcon(':/ic.png'))

        editor.setText(msg)

        editor.setContextMenuPolicy(Qt.CustomContextMenu)
        editor.customContextMenuRequested.connect(self.slotEditorRightClickMenu)

        if self.editorRightMenu==None:
            self.editorRightMenu=QMenu(self)
            self.editorRightMenu.setStyleSheet("""
                QMenu{background-color:rgb(67,67,67);
                        color:white;}
                QMenu::item{padding:4px 16px;}
                QMenu::item::selected{background-color:rgb(124,124,124);}
            """)
            
            undo=QAction(self.tr("Undo"),self)
            undo.setShortcut("Ctrl+Z")
            undo.triggered.connect(self.slotUndo)

            redo=QAction(self.tr("Redo"),self)
            redo.setShortcut("Ctrl+Y")
            redo.triggered.connect(self.slotRedo)

            cut=QAction(self.tr("Cut"),self)
            cut.setShortcut("Ctrl+X")
            cut.triggered.connect(self.slotCut)

            copy=QAction(self.tr("Copy"),self)
            copy.setShortcut("Ctrl+C")
            copy.triggered.connect(self.slotCopy)

            paste=QAction(self.tr("Paste"),self)
            paste.setShortcut("Ctrl+V")
            paste.triggered.connect(self.slotPaste)

            self.editorRightMenu.addAction(undo)
            self.editorRightMenu.addAction(redo)
            self.editorRightMenu.addAction(cut)
            self.editorRightMenu.addAction(copy)
            self.editorRightMenu.addAction(paste)

        #set brace match
        editor.setBraceMatching(editor.StrictBraceMatch)

        #set indent replace 4 space        
        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(2)

        #The line number display area
        editor.setMarginType(0, QsciScintilla.NumberMargin)
        editor.setMarginLineNumbers(0, True)
        editor.setMarginWidth(0,35)

        #set auto indentation
        editor.setAutoIndent(True)

        #syntax check
        editor.setMarginType(1, QsciScintilla.SymbolMargin)
        editor.setMarginLineNumbers(1, False)
        editor.setMarginWidth(1,5)
        editor.setMarginSensitivity(1,False)
        editor.setMarginMarkerMask(1,0x1FFFFFF)
        editor.markerDefine(QsciScintilla.Background,1)

        #set cursor color
        editor.setCaretForegroundColor(QColor(255,255,255))
    
        #Automatic folding area
        editor.setFolding(QsciScintilla.PlainFoldStyle)
        editor.setFoldMarginColors(QColor(39,43,48),QColor(39,43,48))

        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        #set tab's stylesheet
        editor.setStyleSheet("""QWidget{font-size:20px;border: 0px solid white;border-radius:1px;}""")



        self.setCurrentWidget(editor)
        if filename!="untitled":
            self.fileitem.size+=1
            self.fileitem.list.append(filename)


        editor.dragOpenFile.connect(self.dragOpenFile)

        editor.textChanged.connect(self.editorTextChange)
        editor.selectionChanged.connect(self.selectionChanged)
        editor.linesChanged.connect(self.linesChanged)
        editor.cursorPositionChanged.connect(self.cursorPositionChanged)
        editor.userListActivated.connect(self.userListActivated)
        #self.connect(editor,SIGNAL("SCN_AUTOCSELECTION(const char*,int)"),self.scn_updateui)

    def slotEditorRightClickMenu(self,point):
        self.editorRightMenu.exec_(self.currentWidget().mapToGlobal(point))

    def slotUndo(self):
        if self.currentTab<0:
            return
        self.currentWidget().undo()

    def slotRedo(self):
        if self.currentTab<0:
            return
        self.currentWidget().redo()

    def slotCut(self):
        if self.currentTab<0:
            return
        elif not self.currentWidget().hasSelectedText():
            print("cut no msg selected")
            return
        else:
            self.ui.clipboard.setText(self.currentWidget().selectedText())
            self.currentWidget().removeSelectedText()

    def slotCopy(self):
        if self.currentTab<0:
            return
        if not self.currentWidget().hasSelectedText():
            print("copy no msg selected")
        self.ui.cutCopyPasteMsg = self.currentWidget().selectedText()
        self.ui.clipboard.setText(self.ui.cutCopyPasteMsg)

    def slotPaste(self):
        if self.currentTab<0:
            return
        else:
            self.currentWidget().insertAt(self.ui.clipboard.text(),self.line,self.index)

    def editorTextChange(self):
        tabname=self.tabText(self.currentTab)
        if tabname=="untitled":
            return
        elif tabname[0] == "*":
            return
        else:
            if str(self.tabToolTip(self.currentTab)).find(currentExamplesPath)<0:
                tabname = "*" + tabname
                self.setTabText(self.currentTab,tabname)

    def selectionChanged(self):
        pass

    def linesChanged(self):#linesChanged is before cursorPositionChanged
        #such as import math,should be:write(dir(math)),then read return and into 
        #functionList
        return

        lastlinetext= str(self.tabWidget.currentWidget().text(self.editorLine))

        if self.myserial.ser.isOpen()==False:
            return

        return
        #self.IntoFun(lastlinetext)

    def cursorPositionChanged(self,line,index):
        self.line=line
        self.index=index
        if self.ui.currentBoard=="microbit":
            return
        
        linetext= str(self.currentWidget().text(line))
        
        if linetext=="" or linetext==None or len(linetext)==0:
            return

        if linetext.find("\r")>=0 or linetext.find('\n')>=0:
            if len(linetext)<=2 or index==0:
                return
            linetext=linetext[0:index]
            #try:
            if linetext[-1]==".":
                begin=0
                result=-1
                showText=""
                for i in linetext[0:-1]:
                    if ord(i)<=0x2F or (ord(i)>=0x3A and ord(i)<=0x40) or (ord(i)>=0x5B and ord(i)<0x5F) or (ord(i)>0x5F and ord(i)<=0x60) or \
                       (ord(i)>=0x7B and ord(i)<=0x7F):
                        result=begin
                    begin+=1

                if result==-1:
                    showText=linetext[0:-1]
                elif result==0:
                    showText=linetext[1:-1]
                else:
                    showText=linetext[result+1:-1]

                #if functionList.get(showText)!=None:
                #    self.tabWidget.currentWidget().showUserList(1,functionList.get(showText))
            #except:
                #pass
        else:
            if index==0:
                return
            linetext=linetext[0:index]
            if linetext[-1]==".":
                begin=0
                result=-1
                showText=""
                for i in linetext[0:-1]:
                    if ord(i)<=0x2F or (ord(i)>=0x3A and ord(i)<=0x40) or (ord(i)>=0x5B and ord(i)<0x5F) or (ord(i)>0x5F and ord(i)<=0x60) or \
                       (ord(i)>=0x7B and ord(i)<=0x7F):
                        result=begin
                    begin+=1
                if result==-1:
                    showText=linetext[0:-1]
                elif result==0:
                    showText=linetext[1:-1]
                else:
                    showText=linetext[result+1:-1]

                #if functionList.get(showText)!=None:
                #    self.tabWidget.currentWidget().showUserList(1,functionList.get(showText))

    def userListActivated(self,ida,text):
        linetext= str(self.tabWidget.currentWidget().text(self.editorLine))
        linetext=linetext[0:self.editorIndex]
        textsplit= linetext.split(' ')
        linetext=textsplit[-1]
        linetext=linetext.split(".")[-1]
 
        if linetext=="":
            self.currentWidget().insertAt(text,self.line,self.index)
            self.currentWidget().setCursorPosition(self.line,self.index+len(text))
        else:
            self.currentWidget().insertAt(text[str(text).find(linetext)+len(linetext):],self.line,self.index)
            self.currentWidget().setCursorPosition(self.line,self.index+len(text[str(text).find(linetext)+len(linetext):]))

    def dragOpenFile(self,filename):
        if filename.find(".py")<0 and filename.find(".txt")<0 and\
          filename.find(".json")<0 and filename.find(".ini")<0:
            print("current version can not open this file.")
            return
        else:
            self.ui.pcOpenFile(filename)

class myQsciScintilla(QsciScintilla):
    customContextMenuRequested = pyqtSignal()
    dragOpenFile = pyqtSignal(str)
    textChanged = pyqtSignal()
    selectionChanged = pyqtSignal()
    linesChanged = pyqtSignal()
    cursorPositionChanged = pyqtSignal(int, int)
    userListActivated = pyqtSignal(int, str)

    def __init__(self,parent=None):
        super(myQsciScintilla,self).__init__(parent)

    def dragEnterEvent(self,event):
        print("tabwidget dragenterevent2.")
        if event.mimeData().hasFormat("text/url-list")==True:
            event.acceptProposedAction()
        else:
            event.ignore()
    def dragMoveEvent(self,event):
        event.acceptProposedAction()
    def dropEvent(self,event):
        print("tabwidget dropevent2.")
        if event.mimeData().hasUrls:
            urls=event.mimeData().urls()
            dropOpenFileName=""
            for url in urls:
                dropOpenFileName=url.toLocalFile()
            self.dragOpenFile.emit(dropOpenFileName)



















 
    

#app=QApplication(sys.argv)
#main=myTextEdit()中
#main.show()
#app.exec_()
