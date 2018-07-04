# -*- coding: utf-8 -*-   
from PyQt4.QtGui  import *  
from PyQt4.QtCore import *
from PyQt4        import Qsci
from PyQt4.Qsci   import QsciScintilla, QsciScintillaBase, QsciLexerPython

import binascii
import PyQt4
import queue
import base64
import sys
import math
import json
import os
import Esp
import shutil
import webbrowser
import qrc_resources
import time
import platform
import threading
import urllib
import subprocess
from subprocess import check_output
import codecs
import socket
import ctypes
import pyflakes
from urllib import request
from pyflakes.api import main as pyflakesMain

from graphicsInterface          import saveUntitled, createBoardNewDirName, findReplaceText, \
                                       SerialWidget, LanLocWidget, Preferences, treeRightClickRename
from readWriteUart              import readWriteUart
from ctrl                       import ctrlAction
from updateNewFirmware          import updateNewFirmware, updateNewFirmwareBar
from mainComponents             import myTerminal,myTreeView,myTabWidget
from check                      import checkVersionExampleFire, attentionUpdata, ProgressIDEorExampleBar
from threadDownloadFirmware     import threadDownloadFirmware, threadUserFirmware
from microbit_api               import MICROPYTHON_APIS

from SYUAN import syuan

mainShow=True
nowIDEVersion      ="1.0"
isCheckFirmware    =False
rootDirectoryPath  =os.path.expanduser("~")
rootDirectoryPath  =rootDirectoryPath.replace("\\","/")
currentTempPath    ="%s/AppData/Local/uPyCraft/temp/"%rootDirectoryPath
currentExamplesPath="%s/AppData/Local/uPyCraft/examples"%rootDirectoryPath
print(rootDirectoryPath)
print(currentTempPath)
print(currentExamplesPath)

if not os.path.exists("%s/AppData/Local/uPyCraft"%rootDirectoryPath):
    os.makedirs("%s/AppData/Local/uPyCraft"%rootDirectoryPath)
if not os.path.exists("%s/AppData/Local/uPyCraft/download"%rootDirectoryPath):
    os.makedirs("%s/AppData/Local/uPyCraft/download"%rootDirectoryPath)
if not os.path.exists("%s/AppData/Local/uPyCraft/temp"%rootDirectoryPath):
    os.makedirs("%s/AppData/Local/uPyCraft/temp"%rootDirectoryPath)

EXPANDED_IMPORT = ("from microbit import pin15, pin2, pin0, pin1,\
                   pin3, pin6, pin4, i2c, pin5, pin7, pin8, Image,\
                   pin9, pin14, pin16, reset, pin19, temperature,\
                   sleep, pin20, button_a, button_b, running_time,\
                   accelerometer, display, uart, spi, panic, pin13,\
                   pin12, pin11, pin10, compass")

MICROBIT_QSCI_APIS=["import","from","class","global","else","while","break",\
                    "False","True","with"]

updateFirmwareList=[]

class fileItem:
    def __init__(self):
        self.size=0
        self.list=[]

class MainWidget(QMainWindow):
    def __init__(self,parent=None):
        super(MainWidget,self).__init__(parent)
        #self.setWindowFlags(Qt.WindowCloseButtonHint)#HelpButtonHint?
#basic set
        self.setWindowTitle("uPyCraft V%s"%nowIDEVersion)
        self.setWindowIcon(QIcon(':/logo.png'))
        self.resize(1000,800)
        self.setFont()
        self.setIconSize(QSize(36,36))

        self.fileitem=fileItem()

        self.fileName=''
        self.rootDir="."
        self.currentCom=""
        self.myDefaultProgram=""
        self.checkDefaultProgram=""
        self.cutCopyPasteMsg=""
        self.currentBoard="esp32"
        self.workspacePath=""
        self.canNotIdentifyBoard=False

        #self.setStyleSheet("background-color: rgb(254, 138, 58);")

        self.clipboard=QApplication.clipboard()

        self.readwriteQueue=queue.Queue()
        self.uitoctrlQueue=queue.Queue()
        
        self.inDownloadFile=False #判断是否正在下载，避免多次快速F5，导致异常
#tree
        self.tree=None
        self.createTree()
#lexer
        self.lexer=None
        self.createLexer()
        self.autoAPI=Qsci.QsciAPIs(self.lexer)
#terminal
        self.terminal=None
        self.createTerminal()
#tabWidget
        self.editorLine=0
        self.editorIndex=0
        self.editorRightMenu=None
        
        self.tabWidget=None
        self.createTabWidget()
#rightSplitter
        self.rightSplitter=None
        self.createRightSplitter()
#mainWindow
        self.mainWindow=None
        self.createMainWindow()

        self.setCentralWidget(self.mainWindow)
#serial
        self.myserial=SerialWidget()
        self.serialComList=[]

#basic config contains:check config.json,fill workspacePath
        if not self.createBasicConfig():
            global mainShow
            mainShow=False
            return
#actions
        self.createActions()
#menus
        self.createMenus()
#toolBars
        self.createToolBars()

#create graphics interface
        self.createGraphicsInterface()  

#thread
        
        self.readuart=readWriteUart(self.readwriteQueue,self)
        self.connect(self.readuart,SIGNAL("uiRecvFromUart"),self.uiRecvFromUart)

        self.ctrl=ctrlAction(self.readuart,self.readwriteQueue,self.uitoctrlQueue,self)
        self.connect(self.ctrl,SIGNAL("uiRecvFromCtrl"),self.uiRecvFromCtrl)
        self.connect(self.ctrl,SIGNAL("reflushTree"),self.reflushTree)
        self.connect(self.ctrl,SIGNAL("checkFiremware"),self.checkFiremware)
        self.connect(self.ctrl,SIGNAL("loadFileSig"),self.loadFileSig)
        self.connect(self.ctrl,SIGNAL("deleteBoardFileSig"),self.deleteBoardFileSig)
        self.connect(self.ctrl,SIGNAL("renameDirDeleteDirTab"),self.renameDirDeleteDirTab)
        #self.connect(self.ctrl,SIGNAL("intoFuncSig"),self.intoFuncSig)
#timer for serial check
        self.timerClose=False
        global timer
        timer=threading.Timer(1,self.fun_timer)
        self.connect(self,SIGNAL("timerCloseTerminal"),self.timerCloseTerminal)
        self.connect(self,SIGNAL("timerAddComMenu"),self.timerAddComMenu)
        self.connect(self,SIGNAL("timerSetComMenu"),self.timerSetComMenu)
        self.connect(self,SIGNAL("timerClearComMenu"),self.timerClearComMenu)
        timer.start()
        
#check version(IDE,examples)
        self.check=checkVersionExampleFire(self)
        self.connect(self.check,SIGNAL("updateThing"),self.updateThing)
        self.connect(self.check,SIGNAL("updatePer"),self.updataPer)
        self.connect(self.check,SIGNAL("reflushExamples"),self.reflushExamples)
        self.connect(self.check,SIGNAL("changeUpdateFirmwareList"),self.changeUpdateFirmwareList)
        self.connect(self.check,SIGNAL("changeIsCheckFirmware"),self.setIsCheckFirmware)
        
        self.check.start()

        self.setStyleSheet("""
        QMessageBox { background-color: rgb(236,236,236);color:black; }
        QPushButton{background-color:rgb(253,97,72);color:white;}
        """)

    def setFont(self):
        fonts=None
        if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):#for windows
            FONTDIRS=os.path.join(os.environ['WINDIR'],'Fonts')
            fonts=os.listdir(FONTDIRS)
            flags=False
        elif sys.platform.startswith('darwin'):#for mac
            FONTDIRS=os.path.join(os.environ['PWD'])
            fonts=os.listdir(FONTDIRS)
            flags=False
        if fonts==None:
            return
        for filename in fonts:
            if(filename.upper().find('SYUAN.TTF')==0):
                flags=True
                break
        if flags is False:
            checkfont=QMessageBox.question(self,"SYUAN Font",  
                                    "Please install SYUAN font",
                                    QMessageBox.Ok|QMessageBox.Cancel,  
                                    QMessageBox.Ok)  
            if checkfont==QMessageBox.Ok:
                ttf=binascii.unhexlify(syuan)
                fp=open('./SYUAN.TTF','wb')
                fp.write(ttf)
                fp.close()
                if sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
                    os.system('SYUAN.TTF')
                elif sys.platform.startswith('darwin'):
                    subprocess.call(['open','SYUAN.TTF'])
                #os.remove("SYUAN.TTF")
						  
        font=QFont(self.tr("syuan"),10)
        QApplication.setFont(font)

    def createTree(self):
        self.tree=myTreeView(self)
        self.connect(self.tree,SIGNAL("doubleClicked(QModelIndex)"),self.slotTreeDoubleClickOpenFile)
        
        self.rootDevice=QStandardItem(QIcon(":/treeMenuClosed.png"),"device")
        self.rootSD=QStandardItem(QIcon(":/treeMenuClosed.png"),"sd")
        self.rootLib=QStandardItem(QIcon(":/treeMenuClosed.png"),"uPy_lib")
        self.workSpace=QStandardItem(QIcon(":/treeMenuClosed.png"),"workSpace")

        model=QStandardItemModel(self.tree)
        #stringlist = [' board']
        #model.setHorizontalHeaderLabels(stringlist)

        model.appendRow(self.rootDevice)
        model.appendRow(self.rootSD)
        model.appendRow(self.rootLib)
        model.appendRow(self.workSpace)

        self.tree.setModel(model)
        self.tree.createRightMenu()

        

    def createLexer(self):
        self.lexer = QsciLexerPython()
        self.lexer.setDefaultPaper(QColor(38,45,52))
        self.lexer.setDefaultColor(QColor(255,255,255))

        self.lexer.setFont(QFont(self.tr("Consolas"),13,1))

        self.lexer.setColor( Qt.darkGreen, QsciLexerPython.Comment)
        self.lexer.setColor( QColor(255,128,0), QsciLexerPython.TripleDoubleQuotedString )

        self.lexer.setColor( QColor(165,42,42), QsciLexerPython.ClassName )
        self.lexer.setColor( QColor(0,138,140), QsciLexerPython.FunctionMethodName )
                
        self.lexer.setColor( Qt.green, QsciLexerPython.Keyword )
        self.lexer.setColor( QColor(255,0,255), QsciLexerPython.Number )
        self.lexer.setColor( Qt.darkBlue, QsciLexerPython.Decorator )
        self.lexer.setColor( QColor(165,152,36), QsciLexerPython.DoubleQuotedString )
        self.lexer.setColor( QColor(165,152,36), QsciLexerPython.SingleQuotedString )

        #self.lexer.setIndentationWarning(QsciLexerPython.Spaces)

    def createTerminal(self):
        self.terminal=myTerminal(self.readwriteQueue,self)
        
        self.cursor=self.terminal.textCursor()
        self.cursorLeftOrRight=0
        self.moveposition=0
        
        self.connect(self.terminal,SIGNAL("cursorPositionChanged()"),self.slotTerminalCursorChanged)
        self.connect(self.terminal,SIGNAL("setCursor"),self.slotTerminalSetCursor)
        
    def createTabWidget(self):
        self.tabWidget=myTabWidget(self.editorRightMenu,self.fileitem,self)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setFont(QFont(self.tr("syuan"),10,100))
        self.tabWidget.setStyleSheet(""" QWidget{background-color: qlineargradient(x1: 0, x2: 1,stop: 0 #262D34, stop: 1 #222529);
                                     border-width:0px;border-color:#666666;border-style:none;color:white;}
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
        

        #self.connect(self.tabWidget, SIGNAL("tabCloseRequested(int)"),self.closeTab)
        #self.connect(self.tabWidget, SIGNAL("currentChanged(int)"),self.currentTabChange)

    def createRightSplitter(self):
        self.rightSplitter=QSplitter(Qt.Vertical)
        self.rightSplitter.setOpaqueResize(False)
        self.rightSplitter.setStyleSheet("QSplitter{background-color:qlineargradient(x1: 0, x2: 1,stop: 0 #646464, stop: 1 #171717);}"
            "QTabBar::tab{ border-top-left-radius:3px; border-top-right-radius:5px; \
                                    min-width:120px;  \
                                    min-height:25px;  \
                                    border:0px solid rgb(255,0,0); \
                                    border-bottom:none;  \
                                    margin-top: 3; \
                                    color: rgb(255,255,255);\
                                    }"
        "QTabWidget::pane{border-width:0px;border-color:rgb(161,161,161);    border-style: inset;background-color: rgb(64, 64, 64);}"
        "QTabBar::tab::selected{background-color:rgb(38,45,52);border-bottom:2px solid rgb(254,152,77);}" 
        "QTabBar::tab::!selected{background-color:rgb(64,64,64);}"
        "QTabBar::close-button{subcontrol-position:right;image: url(:/tabClose.png)  }"
        "QTabBar::close-button:hover{subcontrol-position:right;image: url(:/tabCloseHover.png)  }"
                                    )
        self.rightSplitter.setHandleWidth(1)

        self.rightSplitter.addWidget(self.tabWidget)
        self.rightSplitter.addWidget(self.terminal)
        self.rightSplitterList=[600,200]
        self.rightSplitter.setSizes(self.rightSplitterList)

    def createMainWindow(self):
        self.mainWindow=QSplitter(Qt.Horizontal,self)
        self.mainWindow.setStyleSheet("background-color: rgb(236, 236, 236);")
        self.mainWindow.setStyleSheet("QSplitter::handle { background-color: rgb(236, 236, 236);}")
        self.mainWindow.setHandleWidth(1)

        self.mainWindow.addWidget(self.tree)
        self.mainWindow.addWidget(self.rightSplitter)

        self.mainWindow.setStretchFactor(0,1)
        self.mainWindow.setStretchFactor(1,7)
        self.mainWindow.setFrameShape(QFrame.NoFrame)

    def createActions(self):
#File
        #self.fileOpenAction=QAction(QIcon(":/fileOpen.png"),self.tr("Open"),self)
        self.fileOpenAction=QAction(self.tr("Open"),self) 
        self.fileOpenAction.setShortcut("Ctrl+O")  
        self.fileOpenAction.setStatusTip(self.tr("open a new file"))  
        self.connect(self.fileOpenAction,SIGNAL("triggered()"),self.slotOpenFile)

        self.fileOpenToolsAction=QAction(QIcon(":/fileOpen.png"),self.tr("Open"),self) 
        self.fileOpenToolsAction.setShortcut("Ctrl+O")  
        self.fileOpenToolsAction.setStatusTip(self.tr("open a new file"))  
        self.connect(self.fileOpenToolsAction,SIGNAL("triggered()"),self.slotOpenFile)

        #self.fileNewAction=QAction(QIcon(":/newFile.png"),self.tr("New"),self)
        self.fileNewAction=QAction(self.tr("New"),self)  
        self.fileNewAction.setShortcut("Ctrl+N")  
        self.fileNewAction.setStatusTip(self.tr("create a new file"))  
        self.connect(self.fileNewAction,SIGNAL("triggered()"),self.slotNewFile)

        self.fileNewToolsAction=QAction(QIcon(":/newFile.png"),self.tr("New"),self)
        self.fileNewToolsAction.setShortcut("Ctrl+N")  
        self.fileNewToolsAction.setStatusTip(self.tr("create a new file"))  
        self.connect(self.fileNewToolsAction,SIGNAL("triggered()"),self.slotNewFile)

        #self.fileSaveAction=QAction(QIcon(":/save.png"),self.tr("Save"),self)
        self.fileSaveAction=QAction(self.tr("Save"),self)  
        self.fileSaveAction.setShortcut("Ctrl+S")  
        self.fileSaveAction.setStatusTip(self.tr("save the file"))  
        self.connect(self.fileSaveAction,SIGNAL("triggered()"),self.slotSaveFile)

        self.fileSaveToolsAction=QAction(QIcon(":/save.png"),self.tr("Save"),self)  
        self.fileSaveToolsAction.setShortcut("Ctrl+S")  
        self.fileSaveToolsAction.setStatusTip(self.tr("save the file"))  
        self.connect(self.fileSaveToolsAction,SIGNAL("triggered()"),self.slotSaveFile)

        #self.fileSaveAsAction=QAction(QIcon(":/saveas.png"),self.tr("Save as"),self)
        self.fileSaveAsAction=QAction(self.tr("Save as"),self)  
        self.fileSaveAsAction.setStatusTip(self.tr("save as a file"))  
        self.connect(self.fileSaveAsAction,SIGNAL("triggered()"),self.slotSaveFileAs)

        #self.refreshBoardFileAction=QAction(QIcon(":/flush.png"),self.tr("Reflush Directory "),self)
        self.refreshBoardFileAction=QAction(self.tr("Reflush Directory "),self)  
        self.refreshBoardFileAction.setStatusTip(self.tr("refresh board file"))  
        self.connect(self.refreshBoardFileAction,SIGNAL("triggered()"),self.slotTreeModel)

        #self.exampleTools=QAction(QIcon(":/examples.png"),self.tr("Examples"),self)
        self.exampleTools=QAction(self.tr("Examples"),self)
        self.exampleMenu=QMenu(self.tr("example"))
        self.connect(self.exampleMenu,SIGNAL("triggered(QAction*)"),self.showExamples)

        self.exampleMenu.setStyleSheet("""QMenu {background-color: rgb(254,254,254);}
                                   QMenu::item::selected { background-color: rgb(255,239,227); color: #000;}""")

        if self.currentBoard=="esp32":
            self.boardEsp32()
        elif self.currentBoard=="esp8266":
            self.boardEsp8266()
        elif self.currentBoard=="pyboard":
            self.boardPyboard()
        elif self.currentBoard=="microbit":
            self.boardMicrobit()
        else:
            self.boardOther()

        self.createUpyLibMenu()
        self.createWorkSpaceMenu()

        #self.exitAction=QAction(QIcon(":/exit.png"),self.tr("Exit"),self)
        self.exitAction=QAction(self.tr("Exit"),self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.setStatusTip(self.tr("Out"))
        self.connect(self.exitAction,SIGNAL("triggered()"),self.close)
#Edit
        #self.cutAction=QAction(QIcon(":/cut.png"),self.tr("Cut"),self)
        self.cutAction=QAction(self.tr("Cut"),self)  
        self.cutAction.setShortcut("Ctrl+X")  
        self.connect(self.cutAction,SIGNAL("triggered()"),self.slotCut)

        #self.copyAction=QAction(QIcon(":/copy.png"),self.tr("Copy"),self)
        self.copyAction=QAction(self.tr("Copy"),self) 
        self.copyAction.setShortcut("Ctrl+C")  
        self.connect(self.copyAction,SIGNAL("triggered()"),self.slotCopy)

        #self.pasteAction=QAction(QIcon(":/paste.png"),self.tr("Paste"),self)
        self.pasteAction=QAction(self.tr("Paste"),self)
        self.pasteAction.setShortcut("Ctrl+V")  
        self.connect(self.pasteAction,SIGNAL("triggered()"),self.slotPaste)

        #self.undoAction=QAction(QIcon(":/undo.png"),self.tr("Undo"),self)
        self.undoAction=QAction(self.tr("Undo"),self)
        self.undoAction.setShortcut("Ctrl+Z")  
        self.connect(self.undoAction,SIGNAL("triggered()"),self.slotUndo)

        self.undoToolsAction=QAction(QIcon(":/undo.png"),self.tr("Undo"),self)
        self.undoToolsAction.setShortcut("Ctrl+Z")  
        self.connect(self.undoToolsAction,SIGNAL("triggered()"),self.slotUndo)

        #self.redoAction=QAction(QIcon(":/redo.png"),self.tr("Redo"),self)
        self.redoAction=QAction(self.tr("Redo"),self)
        self.redoAction.setShortcut("Ctrl+Y")  
        self.connect(self.redoAction,SIGNAL("triggered()"),self.slotRedo)

        self.redoToolsAction=QAction(QIcon(":/redo.png"),self.tr("Redo"),self)
        self.redoToolsAction.setShortcut("Ctrl+Y")  
        self.connect(self.redoToolsAction,SIGNAL("triggered()"),self.slotRedo)

        #self.syntaxCheckAction=QAction(QIcon(":/syntaxCheck.png"),self.tr("syntaxCheck"),self)
        self.syntaxCheckAction=QAction(self.tr("syntaxCheck"),self)
        self.syntaxCheckAction.setStatusTip("the program syntax check")
        self.connect(self.syntaxCheckAction,SIGNAL("triggered()"),self.slotSyntaxCheck)

        self.syntaxCheckToolsAction=QAction(QIcon(":/syntaxCheck.png"),self.tr("syntaxCheck"),self)
        self.syntaxCheckToolsAction.setStatusTip("the program syntax check")
        self.connect(self.syntaxCheckToolsAction,SIGNAL("triggered()"),self.slotSyntaxCheck)

        #self.clearTerminalAction=QAction(QIcon(":/clear.png"),self.tr("Clear"),self)
        self.clearTerminalAction=QAction(self.tr("Clear"),self)  
        self.clearTerminalAction.setStatusTip(self.tr("clear Terminal"))  
        self.connect(self.clearTerminalAction,SIGNAL("triggered()"),self.slotClearTerminal)

        self.clearTerminalToolsAction=QAction(QIcon(":/clear.png"),self.tr("Clear"),self)  
        self.clearTerminalToolsAction.setStatusTip(self.tr("clear Terminal"))  
        self.connect(self.clearTerminalToolsAction,SIGNAL("triggered()"),self.slotClearTerminal)
        
        #self.findAction=QAction(QIcon(":/find.png"),self.tr("find replace"),self)
        self.findAction=QAction(self.tr("find replace"),self)
        self.findAction.setShortcut("Ctrl+F")
        self.connect(self.findAction,SIGNAL("triggered()"),self.slotFindReplaceText)
#tools
        #self.comMenuTools=QAction(QIcon(":/serial.png"),self.tr("Serial"),self)
        self.comMenuTools=QAction(self.tr("Serial"),self)
        self.comMenu=QMenu(self.tr("com"))
        self.comActionGroup=QActionGroup(self)
        
        mylist=self.myserial.Port_List()
        for i in mylist:
            self.serialComList.append(i)
            i=QAction(i,self)
            i.setCheckable(True)
            self.comMenu.addAction(self.comActionGroup.addAction(i))

        self.comActionGroup.setExclusive(True)
        self.connect(self.comMenu,SIGNAL("triggered(QAction*)"),self.slotChooseCom)
        self.comMenuTools.setMenu(self.comMenu)
        
        self.comMenu.setStyleSheet("""QMenu {background-color: rgb(254,254,254);}
                                   QMenu::item::selected { background-color: rgb(255,239,227); color: #000;}""")

        #self.serialConnect=QAction(QIcon(":/connect.png"),self.tr("Connect"),self)
        self.serialConnect=QAction(self.tr("Connect"),self)
        self.connect(self.serialConnect,SIGNAL("triggered()"),self.slotConnectSerial)

        self.serialConnectToolsAction=QAction(QIcon(":/serialConnect.png"),self.tr("Connect"),self)
        self.connect(self.serialConnectToolsAction,SIGNAL("triggered()"),self.slotConnectSerial)

        #self.serialClose=QAction(QIcon(":/serialClose.png"),self.tr("disconnect"),self)
        self.serialClose=QAction(self.tr("disconnect"),self)
        self.connect(self.serialClose,SIGNAL("triggered()"),self.slotCloseSerial)

        self.serialCloseToolsAction=QAction(QIcon(":/serialClose.png"),self.tr("disconnect"),self)
        self.connect(self.serialCloseToolsAction,SIGNAL("triggered()"),self.slotCloseSerial)

        self.esp8266=QAction(self.tr("esp8266"),self)
        self.connect(self.esp8266,SIGNAL("triggered()"),self.boardEsp8266)
        self.esp8266.setCheckable(True)

        self.esp32=QAction(self.tr("esp32"),self)
        self.connect(self.esp32,SIGNAL("triggered()"),self.boardEsp32)
        self.esp32.setCheckable(True)

        self.pyboard=QAction(self.tr("pyboard"),self)
        self.connect(self.pyboard,SIGNAL("triggered()"),self.boardPyboard)
        self.pyboard.setCheckable(True)

        self.microbit=QAction(self.tr("microbit"),self)
        self.connect(self.microbit,SIGNAL("triggered()"),self.boardMicrobit)
        self.microbit.setCheckable(True)

        self.otherBoard=QAction(self.tr("other"),self)
        self.connect(self.otherBoard,SIGNAL("triggered()"),self.boardOther)
        self.otherBoard.setCheckable(True)

        self.boardActionGroup=QActionGroup(self)
        self.boardActionGroup.addAction(self.esp8266)
        self.boardActionGroup.addAction(self.esp32)
        self.boardActionGroup.addAction(self.pyboard)
        self.boardActionGroup.addAction(self.microbit)
        self.boardActionGroup.addAction(self.otherBoard)
        self.boardActionGroup.setExclusive(True)
        
        self.boardMenu = QMenu(self.tr("board"))
        
        self.boardMenu.addAction(self.esp8266)
        self.boardMenu.addAction(self.esp32)
        self.boardMenu.addAction(self.pyboard)
        self.boardMenu.addAction(self.microbit)
        self.boardMenu.addAction(self.otherBoard)
        #self.boardMenuTools=QAction(QIcon(":/board.png"),self.tr("board"),self)
        self.boardMenuTools=QAction(self.tr("board"),self)
        self.boardMenuTools.setMenu(self.boardMenu)

        self.boardMenu.setStyleSheet("""QMenu {background-color: rgb(254,254,254);}
                                   QMenu::item::selected { background-color: rgb(255,239,227); color: #000;}""")

        #self.downloadAction=QAction(QIcon(":/download.png"),self.tr("Download"),self)
        self.downloadAction=QAction(self.tr("Download"),self)
        self.downloadAction.setStatusTip(self.tr("download file to the board"))
        self.connect(self.downloadAction,SIGNAL("triggered()"),self.slotDownloadFile)

        #self.downloadAndRunAction=QAction(QIcon(":/downloadAndRun.png"),self.tr("DownloadAndRun"),self)
        self.downloadAndRunAction=QAction(self.tr("DownloadAndRun"),self) 
        self.downloadAndRunAction.setShortcut("F5") 
        self.downloadAndRunAction.setStatusTip(self.tr("download file and run"))
        self.connect(self.downloadAndRunAction,SIGNAL("triggered()"),self.slotDownloadFileAndRun)

        self.downloadAndRunToolsAction=QAction(QIcon(":/downloadAndRun.png"),self.tr("DownloadAndRun"),self) 
        self.downloadAndRunToolsAction.setShortcut("F5") 
        self.downloadAndRunToolsAction.setStatusTip(self.tr("download file and run"))
        self.connect(self.downloadAndRunToolsAction,SIGNAL("triggered()"),self.slotDownloadFileAndRun)
        self.isDownloadFileAndRun=False

        #self.stopProgramAction=QAction(QIcon(":/stop.png"),self.tr("Stop"),self)
        self.stopProgramAction=QAction(self.tr("Stop"),self)
        self.stopProgramAction.setStatusTip(self.tr("stop the program"))
        self.connect(self.stopProgramAction,SIGNAL("triggered()"),self.slotStopProgram)

        self.stopProgramToolsAction=QAction(QIcon(":/stop.png"),self.tr("Stop"),self)
        self.stopProgramToolsAction.setStatusTip(self.tr("stop the program"))
        self.connect(self.stopProgramToolsAction,SIGNAL("triggered()"),self.slotStopProgram)

        #self.preferenceAction=QAction(QIcon(":/edit.png"),self.tr("Preferences"),self)
        self.preferenceAction=QAction(self.tr("Preferences"),self)
        self.connect(self.preferenceAction,SIGNAL("triggered()"),self.slotPreferences)
        
        #self.initconfig=QAction(QIcon(":/init.png"),self.tr("InitConfig"),self)
        self.initconfig=QAction(self.tr("InitConfig"),self)
        self.connect(self.initconfig,SIGNAL("triggered()"),self.slotInitConfig)

        #self.burnfirmware=QAction(QIcon(":/burnFirmware.png"),self.tr("BurnFirmware"),self)
        self.burnfirmware=QAction(self.tr("BurnFirmware"),self)
        self.connect(self.burnfirmware,SIGNAL("triggered()"),self.slotBurnFirmware)  
#help
        #self.aboutAction=QAction(QIcon(":/about.png"),self.tr("Tutorial online"),self)
        self.aboutAction=QAction(self.tr("Tutorial online"),self) 
        self.connect(self.aboutAction,SIGNAL("triggered()"),self.slotAbout)

    def createMenus(self):
#Files
        self.fileMenu=self.menuBar().addMenu(self.tr("File"))  
        self.fileMenu.addAction(self.fileNewAction)  
        self.fileMenu.addAction(self.fileOpenAction)
        self.fileMenu.addAction(self.exampleTools)
        self.fileMenu.addAction(self.fileSaveAction)
        self.fileMenu.addAction(self.fileSaveAsAction)
        self.fileMenu.addAction(self.refreshBoardFileAction)
        self.fileMenu.addAction(self.exitAction)

        self.fileMenu.setStyleSheet("background-color: rgb(254,254,254);")
#edit
        editMenu=self.menuBar().addMenu(self.tr("Edit"))  
        editMenu.addAction(self.copyAction)  
        editMenu.addAction(self.cutAction)  
        editMenu.addAction(self.pasteAction)
        editMenu.addAction(self.redoAction)
        editMenu.addAction(self.undoAction)
        editMenu.addAction(self.syntaxCheckAction)
        editMenu.addAction(self.findAction)

        editMenu.setStyleSheet("background-color: rgb(254,254,254);")
#Tools
        toolMenu=self.menuBar().addMenu(self.tr("Tools"))
        toolMenu.addAction(self.comMenuTools)
        toolMenu.addAction(self.boardMenuTools)
        toolMenu.addAction(self.downloadAction)
        toolMenu.addAction(self.downloadAndRunAction)
        toolMenu.addAction(self.stopProgramAction)
        toolMenu.addAction(self.burnfirmware)
        toolMenu.addAction(self.initconfig)
        toolMenu.addAction(self.preferenceAction)

        toolMenu.setStyleSheet("background-color: rgb(254,254,254);")
        
        self.connect(toolMenu,SIGNAL("hovered(QAction*)"),self.slotToolMenuHover) 
#Help
        aboutMenu=self.menuBar().addMenu(self.tr("Help"))
        aboutMenu.addAction(self.aboutAction)
        
        aboutMenu.setStyleSheet("background-color: rgb(254,254,254);")

        self.menuBar().setStyleSheet("""QMenuBar {background-color: rgb(254, 254, 254);}
                                        QMenuBar::item {background: rgb(254, 254, 254);}
                                        QMenu::item::selected { background-color: rgb(255,239,227); color: #000; }
                                        QMenuBar::item::selected {background-color: #FFEFE3;}""")

#create toolBars
    def createToolBars(self):
        fileToolBar=self.addToolBar("File")
        fileToolBar.addAction(self.fileNewToolsAction)
        fileToolBar.addAction(self.fileOpenToolsAction)
        fileToolBar.addAction(self.fileSaveToolsAction)
        fileToolBar.addAction(self.downloadAndRunToolsAction)
        fileToolBar.addAction(self.stopProgramToolsAction)
        fileToolBar.addAction(self.serialConnectToolsAction)
        fileToolBar.addAction(self.serialCloseToolsAction)
        fileToolBar.addAction(self.undoToolsAction)
        fileToolBar.addAction(self.redoToolsAction)
        fileToolBar.addAction(self.syntaxCheckToolsAction)
        fileToolBar.addAction(self.clearTerminalToolsAction)
        self.serialCloseToolsAction.setVisible(False)

        if sys.platform=="darwin":
            self.setUnifiedTitleAndToolBarOnMac(True)
        else:
            self.setUnifiedTitleAndToolBarOnMac(False)

        # #FFBE2B  #FF4E50
        fileToolBar.setStyleSheet("""QToolBar {background-color: qlineargradient( y1: 0,  y2: 1,stop: 0 #FF4E50, stop: 1 #FFBE2B);spacing:8px;}""")
        self.addToolBar(Qt.RightToolBarArea,fileToolBar)
#create examples menu for File->Examples
    def createExampleMenu(self):
        #two follow lines mean:on PC conmon dir and board dir(contians:esp8266,esp32,pyboard,microbit)
        self.PCcommonList=[]
        self.PCboardList=[]
        if self.currentBoard=="esp32":
            self.getPCcommonExamples("%s/AppData/Local/uPyCraft/examples/Common"%rootDirectoryPath)
            self.getPCboardExamples("%s/AppData/Local/uPyCraft/examples/Boards/ESP32"%rootDirectoryPath)
            for filename in self.PCboardList:
                if filename in self.PCcommonList:
                    self.PCcommonList.remove(filename)

            self.getPCexamples("%s/AppData/Local/uPyCraft/examples/Boards/ESP32"%rootDirectoryPath,self.exampleMenu)

            menuTitle=[]

            for i in self.exampleMenu.findChildren(QMenu):
                if i.title() not in menuTitle:
                    menuTitle.append(i.title())

            for adir in self.PCcommonList:
                adirList = adir.split("/")
                if adirList[1] in menuTitle:
                    for i in self.exampleMenu.findChildren(QMenu):
                        if i.title()==adirList[1]:
                            self.addPCcommonExamples(adir[1:],i,adir[1:])
                            break
                else:
                    newMenu = self.exampleMenu.addMenu(adirList[1])
                    self.addPCcommonExamples(adir[1:],newMenu,adir[1:])
                    menuTitle.append(adirList[1])
        elif self.currentBoard=="esp8266":
            self.getPCcommonExamples("%s/AppData/Local/uPyCraft/examples/Common"%rootDirectoryPath)
            self.getPCboardExamples("%s/AppData/Local/uPyCraft/examples/Boards/ESP8266"%rootDirectoryPath)
            for filename in self.PCboardList:
                if filename in self.PCcommonList:
                    self.PCcommonList.remove(filename)

            self.getPCexamples("%s/AppData/Local/uPyCraft/examples/Boards/ESP8266"%rootDirectoryPath,self.exampleMenu)
            menuTitle=[]
            for i in self.exampleMenu.findChildren(QMenu):
                menuTitle.append(i.title())
            for adir in self.PCcommonList:
                adirList = adir.split("/")
                if adirList[1] in menuTitle:
                    for i in self.exampleMenu.findChildren(QMenu):
                        if i.title()==adirList[1]:
                            self.addPCcommonExamples(adir[1:],i,adir[1:])
                            break
                else:
                    newMenu = self.exampleMenu.addMenu(adirList[1])
                    self.addPCcommonExamples(adir[1:],newMenu,adir[1:])
                    menuTitle.append(adirList[1])
        elif self.currentBoard=="pyboard":
            self.getPCboardExamples("%s/AppData/Local/uPyCraft/examples/Boards/pyboard"%rootDirectoryPath)
            for filename in self.PCboardList:
                if filename in self.PCcommonList:
                    self.PCcommonList.remove(filename)
            self.getPCexamples("%s/AppData/Local/uPyCraft/examples/Boards/pyboard"%rootDirectoryPath,self.exampleMenu)
            menuTitle=[]
            for i in self.exampleMenu.findChildren(QMenu):
                menuTitle.append(i.title())
            for adir in self.PCcommonList:
                adirList = adir.split("/")
                if adirList[1] in menuTitle:
                    for i in self.exampleMenu.findChildren(QMenu):
                        if i.title()==adirList[1]:
                            self.addPCcommonExamples(adir[1:],i,adir[1:])
                            break
                else:
                    newMenu = self.exampleMenu.addMenu(adirList[1])
                    self.addPCcommonExamples(adir[1:],newMenu,adir[1:])
                    menuTitle.append(adirList[1])
        elif self.currentBoard=="microbit":
            self.getPCboardExamples("%s/AppData/Local/uPyCraft/examples/Boards/microbit"%rootDirectoryPath)
            for filename in self.PCboardList:
                if filename in self.PCcommonList:
                    self.PCcommonList.remove(filename)

            self.getPCexamples("%s/AppData/Local/uPyCraft/examples/Boards/microbit"%rootDirectoryPath,self.exampleMenu)

            menuTitle=[]
            for i in self.exampleMenu.findChildren(QMenu):
                menuTitle.append(i.title())

            for adir in self.PCcommonList:
                adirList = adir.split("/")
                if adirList[1] in menuTitle:
                    for i in self.exampleMenu.findChildren(QMenu):
                        if i.title()==adirList[1]:
                            self.addPCcommonExamples(adir[1:],i,adir[1:])
                            break
                else:
                    newMenu = self.exampleMenu.addMenu(adirList[1])
                    self.addPCcommonExamples(adir[1:],newMenu,adir[1:])
                    menuTitle.append(adirList[1])
        else:
            pass

        self.exampleTools.setMenu(self.exampleMenu)

    def createUpyLibMenu(self):
        if not os.path.exists("%s/AppData/Local/uPyCraft/examples/uPy_lib"%rootDirectoryPath):
            return
        uPyLibPath="%s/AppData/Local/uPyCraft/examples/uPy_lib"%rootDirectoryPath
        row=self.rootLib.rowCount()     #clear board treemodel
        self.rootLib.removeRows(0,row)  #use for refresh treemodel,these two lines

        self.getPCLibFile(self.rootLib,uPyLibPath)

    def createWorkSpaceMenu(self):
        if not os.path.exists(self.workspacePath):
            row=self.workSpace.rowCount()
            self.workSpace.removeRows(0,row)
            return
        path=self.workspacePath
        row=self.workSpace.rowCount()
        self.workSpace.removeRows(0,row)

        self.getPCLibFile(self.workSpace,path)

    def createWorkSpacePath(self):
        if not os.path.exists(self.workspacePath):
            print("workspacePath is none")
            print(self.workspacePath)
            self.workspacePath = QFileDialog.getExistingDirectory(self,"set your work space path","./")
            if self.workspacePath=="":
                return False
            
            self.workspacePath=self.workspacePath.replace("\\","/")
            self.workspacePath+="/workSpace"

            if not os.path.exists(self.workspacePath):
                os.mkdir(self.workspacePath)
                os.mkdir(self.workspacePath+"/user_lib")
            else:
                pass

            if os.path.exists("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath):
                configfile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
                mymsg=configfile.read()
                configfile.close()
                jsonDict=eval(mymsg)
                
                jsonDict['workSpace']=str(self.workspacePath)
                jsonMsg=str(jsonDict)
                configfile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
                configfile.write(jsonMsg)
                configfile.close()
            
        if not os.path.exists(self.workspacePath+"/user_lib"):
            os.mkdir(self.workspacePath+"/user_lib")

        return True

#create graphics interface
    def createGraphicsInterface(self):
        self.saveUntitled=saveUntitled()
        self.connect(self.saveUntitled.okButton,SIGNAL("clicked()"),self.saveUntitledOK)

        self.newBoardDirName=createBoardNewDirName()
        self.connect(self.newBoardDirName.okButton,SIGNAL("clicked()"),self.getBoardDirName)
        
        self.getTreeRightMenuRename=treeRightClickRename()
        self.connect(self.getTreeRightMenuRename.okButton,SIGNAL("clicked()"),self.getTreeRenameOk)

    def createBasicConfig(self):
        path=os.getcwd()
        path=path.replace("\\","/")

        if not os.path.exists("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath):
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
            configFile.write("{'serial':'None',\
                         'updateURL':'https://git.oschina.net/dfrobot/upycraft/raw/master/uPyCraft.json',\
                         'checkFirmware':'check update',\
                         'address':'China Mainland',\
                         'workSpace':'%s'}"%(path+"/workSpace"))
            configFile.close()
            
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'rU')
            configMsg=configFile.read()
            configFile.close()

            try:
                jsonDict=eval(configMsg)
            except:
                QMessageBox.information(self,self.tr("attention"),self.tr("Please put the uPy_Craft and workSpace into non-Chinese dir."),QMessageBox.Ok)
                os.remove("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath)
                return False
            self.workspacePath=path+"/workSpace"
        else:
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'rU')
            configMsg=configFile.read()
            configFile.close()

            try:
                jsonDict=eval(configMsg)
            except:
                QMessageBox.information(self,self.tr("attention"),self.tr("Please put the uPy_Craft and workSpace into non-Chinese dir."),QMessageBox.Ok)
                os.remove("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath)
                return False

            if jsonDict.get("workSpace") != None:
                self.workspacePath=jsonDict['workSpace']
            else:
                self.workspacePath=path+"/workSpace"
            
            if jsonDict.get('serial')==None or \
               jsonDict.get('updateURL')==None or \
               jsonDict.get('checkFirmware')==None or \
               jsonDict.get('address')==None or \
               jsonDict.get('workSpace')==None:
                configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
                configFile.write("{'serial':'None','updateURL':'https://git.oschina.net/dfrobot/upycraft/raw/master/uPyCraft.json',\
                            'checkFirmware':'check update','address':'China Mainland','workSpace':'%s'}"%self.workspacePath)
                configFile.close()

        return True
      
###any slot function
#File
    def slotOpenFile(self):
        filename=QFileDialog.getOpenFileName(self)
        filename=filename.replace("\\","/")
        if str(filename).find(".py")<0 and \
           str(filename).find(".txt")<0 and \
           str(filename).find(".json")<0 and \
           str(filename).find(".ini")<0:
            self.terminal.append("current version only open py txt json ini file")
            return
        self.pcOpenFile(filename)

    def slotTreeDoubleClickOpenFile(self,index):
        if self.fileName.find(".py")<0 and \
           self.fileName.find(".txt")<0 and \
           self.fileName.find(".json")<0 and \
           self.fileName.find(".ini")<0:
            self.terminal.append("current version only open py txt json ini file.")
            return
        
        if sys.platform=="linux" and self.fileName.find(rootDirectoryPath)>=0:
            self.pcOpenFile(self.fileName)
            return
        elif sys.platform=="win32" and self.fileName.find(":")>=0:
            self.pcOpenFile(self.fileName)
            return
        elif sys.platform=="darwin" and self.fileName.find(rootDirectoryPath)>=0:
            self.pcOpenFile(self.fileName)
            return
        else:
            if self.editClassFileitem(self.fileName):
                self.uitoctrlQueue.put("loadfile:::%s"%self.fileName)
                pass
            else:
                print("double false")

    def slotNewFile(self):
        self.tabWidget.createNewTab("untitled","",self.lexer)

    def slotSaveFile(self):
        if self.tabWidget.currentWidget() is None:
            print("slotSaveFile none file")
            return
        self.saveStr=self.tabWidget.currentWidget().text()
        if self.tabWidget.tabText(self.tabWidget.currentIndex())=="untitled":
            if self.saveUntitled.isHidden():
                self.saveUntitled.show()
        elif self.tabWidget.tabToolTip(self.tabWidget.currentTab).find(currentExamplesPath)>=0:
            self.slotSaveFileAs()
        else:
            tabname = self.tabWidget.tabText(self.tabWidget.currentIndex())
            filepath = self.tabWidget.tabToolTip(self.tabWidget.currentIndex())
            print(tabname)
            print(filepath)
            if tabname[0] != "*":#tabname have *,means it's changed,can be save
                return
            elif sys.platform=="linux" and filepath.find(rootDirectoryPath)<0:
                savefile=codecs.open(currentTempPath+str(filepath),'wb')
            elif sys.platform=="win32" and  filepath.find(":")<0:
                savefile=codecs.open(currentTempPath+str(filepath),'wb')
            elif sys.platform=="darwin" and filepath.find(rootDirectoryPath)<0:
                savefile=codecs.open(currentTempPath+str(filepath),'wb')
            else:
                savefile=open(filepath,'wb')

            self.saveStr=self.saveStr.replace("\r\n","\r")
            self.saveStr=self.saveStr.replace("\n","\r")
            saveStrSplit = self.saveStr.split("\r")
            self.saveStr=""
            for i in saveStrSplit:
                self.saveStr = self.saveStr + i
                self.saveStr = self.saveStr + "\r\n"
            
            if type(self.saveStr) is bytes:
                self.saveStr=self.saveStr.decode('utf-8')
            savefile.write(self.saveStr.encode('utf-8'))
            savefile.close()
            self.tabWidget.setTabText(self.tabWidget.currentIndex(),tabname[1:])

    def slotSaveFileAs(self):
        if self.tabWidget.currentTab<0:
            return
        filename=QFileDialog.getSaveFileName(self)
        print(filename)
        if filename:
            self.saveStr=self.tabWidget.currentWidget().text()
            savefile=open(filename,'wb')

            self.saveStr=self.saveStr.replace("\r\n","\r")
            self.saveStr=self.saveStr.replace("\n","\r")
            saveStrSplit = self.saveStr.split("\r")
            self.saveStr=""
            for i in saveStrSplit:
                self.saveStr = self.saveStr + i
                self.saveStr = self.saveStr + "\r\n"

            if type(self.saveStr) is bytes:
                self.saveStr=self.saveStr.decode('utf-8')
            savefile.write(self.saveStr.encode('utf-8'))
            savefile.close()
        else:
            pass

    def saveUntitledOK(self):
        tabname=self.saveUntitled.saveFileTextedit.text()
        self.saveUntitled.saveFileTextedit.clear()
        if tabname=="":
            return
        if str(tabname).find(".")<0:
            tabname=tabname+'.py'
        elif str(tabname)[-1]==".":
            if(tabname[0]) == ".":
                self.terminal.append("filename error")
                return
            else:
                tabname=tabname+"py"
        else:
            tabname=str(tabname)
            if tabname[-3:].lower()==".py":
                tabname=tabname[0:-3]+".py"
            elif tabname[-5:].lower()==".json":
                tabname=tabname[0:-5]+".json"
            elif tabname[-4:].lower()==".ini":
                tabname=tabname[0:-4]+".ini"
            elif tabname[-4:].lower()==".txt":
                tabname=tabname[0:-4]+".txt"

        if not self.createWorkSpacePath():
            return
        
        confirmFileIsExists=False
        if os.path.exists(self.workspacePath+"/"+tabname)==True:
            fileIsExists=QMessageBox.question(self,"waring",  
                                "This file is already exists,continue to insted?",
                                QMessageBox.Ok|QMessageBox.Cancel,  
                                QMessageBox.Ok)
            if fileIsExists==QMessageBox.Ok:
                confirmFileIsExists=True
            else:
                return

        self.fileName=self.workspacePath+"/"+tabname
        self.str = self.tabWidget.currentWidget().text()
        savefile=open(self.fileName,'wb')

        self.saveStr=self.saveStr.replace("\r\n","\r")
        self.saveStr=self.saveStr.replace("\n","\r")
        saveStrSplit = self.saveStr.split("\r")
        self.saveStr=""
        for i in saveStrSplit:
            self.saveStr = self.saveStr + i
            self.saveStr = self.saveStr + "\r\n"
            
        if type(self.saveStr) is bytes:
            self.saveStr=self.saveStr.decode('utf-8')
        savefile.write(self.saveStr.encode('utf-8'))
        savefile.close()

        transitFile=self.fileName
        self.tabWidget.setTabToolTip(self.tabWidget.currentIndex(),transitFile)
        self.tabWidget.setTabText(self.tabWidget.currentIndex(),tabname)

        if confirmFileIsExists:
            if transitFile in self.fileitem.list:
                num=0
                while num<self.tabWidget.count():
                    text=self.tabWidget.tabToolTip(num)
                    if text==transitFile:
                        self.tabWidget.removeTab(num)
                        self.fileitem.list.remove(transitFile)
                        self.fileitem.size-=1
                        break
                    num+=1

        self.fileitem.size+=1
        self.fileitem.list.append(str(transitFile))
        #print(self.fileitem.list)
        #self.createWorkSpaceMenu()

    def slotTreeModel(self):
        self.createUpyLibMenu()
        self.createWorkSpaceMenu()
        if not self.myserial.ser.isOpen():
            #self.terminal.append("serial not open")
            return
        
        self.uitoctrlQueue.put("treeModel")

    def slotCut(self):
        if self.tabWidget.currentTab<0:
            return
        if not self.tabWidget.currentWidget().hasSelectedText():
            self.terminal.append("no msg selected")
            return
        self.cutCopyPasteMsg = self.tabWidget.currentWidget().selectedText()
        self.tabWidget.currentWidget().removeSelectedText()
        self.clipboard.setText(self.cutCopyPasteMsg)

    def slotCopy(self):
        if self.tabWidget.currentTab<0:
            return
        if not self.tabWidget.currentWidget().hasSelectedText():
            self.terminal.append("no msg selected")
            return
        self.cutCopyPasteMsg = self.tabWidget.currentWidget().selectedText()
        self.clipboard.setText(self.cutCopyPasteMsg)

    def slotPaste(self):
        self.tabWidget.slotPaste()

    def slotUndo(self):
        self.tabWidget.slotUndo()

    def slotRedo(self):
        self.tabWidget.slotRedo()

    def slotSyntaxCheck(self):
        if self.tabWidget.currentWidget()==None:
            return

        self.tabWidget.currentWidget().markerDeleteAll()
        #self.tabWidget.currentWidget().setMarkerBackgroundColor(QColor(255,0,0))

        syntaxCheckFilePath="%s/AppData/Local/uPyCraft/temp/syntaxCheck.py"%rootDirectoryPath
        syntaxCheckFileText=self.tabWidget.currentWidget().text()

        filehandle=open(syntaxCheckFilePath,"wb")
        syntaxCheckFileText=syntaxCheckFileText.split("\r")
        nocheck=0
        for i in syntaxCheckFileText:
            if i.find("'''")>=0 and nocheck==0:
                nocheck=1
            elif i.find("'''")>=0 and nocheck==1:
                nocheck=0

            if nocheck==1:
                if i=="":
                    filehandle.write('\r'.encode('utf-8'))
                    continue
                else:
                    filehandle.write(i.encode('utf-8'))
                    filehandle.write('\r'.encode('utf-8'))
                    continue

            if i.find("from microbit import *")>=0:
                if i.find("#")>=0:
                    if i.find("from microbit import *")<i.find("#"):
                        i=EXPANDED_IMPORT
                    else:
                        pass
                else:
                    i=EXPANDED_IMPORT
            elif i=="":
                filehandle.write('\r'.encode('utf-8'))
                continue
            filehandle.write(i.encode('utf-8'))
            filehandle.write('\r'.encode('utf-8'))
        
        filehandle.close()

        backStdout=sys.stdout
        backStderr=sys.stderr
        stdoutFilePath="%s/AppData/Local/uPyCraft/temp/stdout.py"%rootDirectoryPath
        stderrFilePath="%s/AppData/Local/uPyCraft/temp/stderr.py"%rootDirectoryPath
        stdoutFile=open(stdoutFilePath,'w')
        stderrFile=open(stderrFilePath,'w')
        sys.stdout=stdoutFile
        sys.stderr=stderrFile

        pyflakesMain(None,str(syntaxCheckFilePath))

        sys.stdout=backStdout
        sys.stderr=backStderr
        stdoutFile.close()
        stderrFile.close()

        stdoutFile=open(stdoutFilePath,'r')
        stderrFile=open(stderrFilePath,'r')
        stdout = stdoutFile.read()
        stderr = stderrFile.read()
        stdoutFile.close()
        stderrFile.close()
        
        if str(stdout)=="" and str(stderr)=="":
            pass
        else:
            if stdout=="":
                pass
            else:
                stdout=stdout.split("\n")
                for i in stdout:
                    if i=="":
                        continue
                    if i.find("imported but unused")>=0:
                        continue
                    if i.find("undefined name 'const'")>=0:
                        continue

                    if sys.platform=="win32":
                        self.tabWidget.currentWidget().markerAdd((int(i.split(":")[2])-1),1)
                    elif sys.platform=="linux":
                        self.tabWidget.currentWidget().markerAdd((int(i.split(":")[1])-1),1)
                    elif sys.platform=="darwin":
                        print("platform1 darwin")
                        self.tabWidget.currentWidget().markerAdd((int(i.split(":")[1])-1),1)
                    else:
                        print("other platform1.")
                        return

                    i=i.split(":")
                    appendMsg=self.tabWidget.tabText(self.tabWidget.currentTab)
                    for n in range(0,len(i)):
                        if n>=2:
                            appendMsg=appendMsg+":"+i[n]
                    self.terminal.append(appendMsg)
                        
                self.tabWidget.currentWidget().setMarkerBackgroundColor(QColor(128,128,128))

            if stderr=="":
                pass
            else:
                stderr=stderr.split("\n")
                print(stderr)
                for i in stderr:
                    if i=="":
                        continue
                    if i.find("syntaxCheck.py")>0:
                        if sys.platform=="win32":
                            self.tabWidget.currentWidget().markerAdd((int(i.split(":")[2])-1),1)
                        elif sys.platform=="linux":
                            self.tabWidget.currentWidget().markerAdd((int(i.split(":")[1])-1),1)
                        elif sys.platform=="darwin":
                            print("platform2 darwin")
                            self.tabWidget.currentWidget().markerAdd((int(i.split(":")[1])-1),1)
                        else:
                            print("other platform2.")
                            return
                        i=i.split(":")
                        appendMsg=self.tabWidget.tabText(self.tabWidget.currentTab)
                        for n in range(0,len(i)):
                            if n>=2:
                                appendMsg=appendMsg+":"+i[n]
                        self.terminal.append(appendMsg)
                        continue
                    self.terminal.append(i)
                self.tabWidget.currentWidget().setMarkerBackgroundColor(QColor(128,128,128))

        self.terminal.append("syntax finish.")

    def slotClearTerminal(self):
        self.terminal.clear()

    def slotFindReplaceText(self):
        if self.tabWidget.currentWidget() == None:
            return
        self.findmsg=findReplaceText()
        self.connect(self.findmsg.findButton,SIGNAL("clicked()"),self.slotFindText)
        self.connect(self.findmsg.replaceButton,SIGNAL("clicked()"),self.slotReplaceText)
        self.findmsg.show()

    def slotFindText(self):
        #1 是否为正则表达 2 是否大小写敏感 3 是否全词匹配 4是否为选中的最后文本
        #1.whether the regular expression
        #2.whether case-sensitive
        #3.whether first character determine the position, then find the whole word
        #4.whether the end text been selected
        if self.tabWidget.currentWidget().findFirst(self.findmsg.findedit.text(),False,False,False,True):
            pass
        else:
            QMessageBox.information(self,self.tr("attention"),self.tr("not find"),QMessageBox.Ok)

    def slotReplaceText(self):
        if self.tabWidget.currentWidget()==None:
            #self.terminal.append("please open a file")
            return

        if self.findmsg.replaceStartEdit.text()=="":
            #self.terminal.append("Please input replace word")
            return
        if self.findmsg.replaceToEdit.text()=="":
            #self.terminal.append("Please input replace to")
            return
        if self.findmsg.replaceStartEdit.text()==self.findmsg.replaceToEdit.text():
            QMessageBox.information(self,self.tr("attention"),self.tr("the same msg could not be replace!"),QMessageBox.Ok)
            return
        
        if self.tabWidget.currentWidget().findFirst(self.findmsg.replaceStartEdit.text(),False,True,True,True)==False:
            #self.terminal.append("can\'t find \'%s\'"%self.findmsg.replaceStartEdit.text())
            return

        while self.tabWidget.currentWidget().findFirst(self.findmsg.replaceStartEdit.text(),False,True,True,True):
            self.tabWidget.currentWidget().replaceSelectedText(self.findmsg.replaceToEdit.text())


    def slotChooseCom(self,action):
        #self.rootDevice.setIcon(QIcon(":/about.png"))
        if self.myserial.ser.isOpen():
            self.terminal.append("serial already opened")
            self.serialConnectToolsAction.setVisible(False)
            self.serialCloseToolsAction.setVisible(True)
            return
        try:
            self.myserial.comChooseOk(action.text())
            self.currentCom=action.text()
        except Exception as e:
            self.terminal.append(str(e))
            return

        configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
        configText=configFile.read()
        configFile.close()

        self.updateFirmwareCom=action.text()
        if configText != "":
            jsonDict=eval(configText)
            jsonDict['serial']=action.text()
            configText=str(jsonDict)

            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
            configFile.write(configText)
            configFile.close()

        self.terminal.clear()
        self.myserial.ser.write('\x03'.encode())

        startdata=""
        startTime=time.time()
        while True:
            n = self.myserial.ser.inWaiting()
            if n>0:
                startdata += (self.myserial.ser.read(n)).decode(encoding='utf-8',errors='ignore')
                if startdata.find(">>> ")>=0:
                    break
            time.sleep(0.1)
            endTime=time.time()
            if endTime-startTime > 3:
                self.terminal.append("open serial error, please try again.")
                self.myserial.ser.close()
                if not self.myserial.ser.isOpen():
                    self.updateFirmwareCom=jsonDict['serial']
                    self.currentCom=""
                    self.canNotIdentifyBoard=True
                    self.updateFirmware()
                return
        self.canNotIdentifyBoard=False
        senddata="import sys\r"
        for i in senddata:
            self.myserial.ser.write(i.encode())
        startdata=""
        startTime=time.time()
        while True:
            n = self.myserial.ser.inWaiting()
            if n>0:
                startdata+=(self.myserial.ser.read(n)).decode('utf-8')
                if startdata.find(">>> ")>=0:
                    self.terminal.append(">>> ")
                    break
            time.sleep(0.1)
            endTime=time.time()
            if endTime-startTime>2:
                self.myserial.ser.close()
                self.terminal.append("connect serial timeout")
                return

        senddata="sys.platform\r"
        for i in senddata:
            self.myserial.ser.write(i.encode())
        startdata=""
        startTime=time.time()
        while True:
            n = self.myserial.ser.inWaiting()
            if n>0:
                startdata+=(self.myserial.ser.read(n)).decode('utf-8')
                if startdata.find(">>> ")>=0:
                    break
            time.sleep(0.1)
            endTime=time.time()
            if endTime-startTime>2:
                self.myserial.ser.close()
                self.terminal.append("connect serial timeout")
                return

        self.currentBoard=startdata.split("\r\n")[1][1:-1]
        
        self.ctrl.start()
        time.sleep(0.005)
        self.uitoctrlQueue.put("clear")
        time.sleep(0.005)
        self.readuart.start()

        self.uitoctrlQueue.put("importOs")
        time.sleep(0.05)

        if self.currentBoard=="pyboard":
            self.boardPyboard()
        else:
            self.uitoctrlQueue.put("checkFirmware")

        if self.currentBoard=="microbit":
            self.boardMicrobit()
        else:
            self.uitoctrlQueue.put("getcwd")


        self.emit(SIGNAL("changeCurrentBoard"),self.currentBoard)
        time.sleep(0.005)
        self.terminal.setReadOnly(False)
        self.slotTreeModel()

        self.terminal.setEventFilterEnable(True)

        self.serialConnectToolsAction.setVisible(False)
        self.serialCloseToolsAction.setVisible(True)

    def slotConnectSerial(self):
        if self.myserial.ser.isOpen():
            self.terminal.append("serial already opened.")
            self.serialConnectToolsAction.setVisible(False)
            self.serialCloseToolsAction.setVisible(True)
            return

        configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
        configText=configFile.read()
        configFile.close()

        if configText != "":
            jsonDict=eval(configText)
            self.updateFirmwareCom=jsonDict['serial']
        else:
            self.updateFirmwareCom=""
            return

        try:
            self.myserial.comChooseOk(jsonDict['serial'])
        except Exception as e:
            self.terminal.append(str(e))
            return
        finally:
            pass

        self.currentCom=jsonDict['serial']

        self.terminal.clear()
        self.myserial.ser.write('\x03'.encode())

        startdata=""
        startTime=time.time()
        while True:
            n = self.myserial.ser.inWaiting()
            if n>0:
                startdata += (self.myserial.ser.read(n)).decode(encoding='utf-8',errors='ignore')
                if startdata.find(">>> ")>=0:
                    break
            time.sleep(0.1)
            endTime=time.time()
            if endTime-startTime > 3:
                self.terminal.append("open serial error, please try again.")
                self.myserial.ser.close()
                if not self.myserial.ser.isOpen():
                    self.updateFirmwareCom=jsonDict['serial']
                    self.currentCom=""
                    self.canNotIdentifyBoard=True
                    self.updateFirmware()
                return
        self.canNotIdentifyBoard=False
        senddata="import sys\r"
        for i in senddata:
            self.myserial.ser.write(i.encode())
        startdata=""
        startTime=time.time()
        while True:
            n = self.myserial.ser.inWaiting()
            if n>0:
                startdata+=(self.myserial.ser.read(n)).decode('utf-8')
                if startdata.find(">>> ")>=0:
                    self.terminal.append(">>> ")
                    break
            time.sleep(0.1)
            endTime=time.time()
            if endTime-startTime>2:
                self.myserial.ser.close()
                self.terminal.append("connect serial timeout")
                return

        senddata="sys.platform\r"
        for i in senddata:
            self.myserial.ser.write(i.encode())
        startdata=""
        startTime=time.time()
        while True:
            n = self.myserial.ser.inWaiting()
            if n>0:
                startdata+=(self.myserial.ser.read(n)).decode('utf-8')
                if startdata.find(">>> ")>=0:
                    break
            time.sleep(0.1)
            endTime=time.time()
            if endTime-startTime>2:
                self.myserial.ser.close()
                self.terminal.append("connect serial timeout")
                return

        self.currentBoard=startdata.split("\r\n")[1][1:-1]
        
        self.ctrl.start()
        time.sleep(0.005)
        self.uitoctrlQueue.put("clear")
        time.sleep(0.005)
        self.readuart.start()

        self.uitoctrlQueue.put("importOs")
        time.sleep(0.05)

        if self.currentBoard=="pyboard":
            self.boardPyboard()
        else:
            self.uitoctrlQueue.put("checkFirmware")

        if self.currentBoard=="microbit":
            self.boardMicrobit()
        else:
            self.uitoctrlQueue.put("getcwd")

        self.emit(SIGNAL("changeCurrentBoard"),self.currentBoard)
        time.sleep(0.005)
        self.terminal.setReadOnly(False)
        self.slotTreeModel()

        self.terminal.setEventFilterEnable(True)

        self.serialConnectToolsAction.setVisible(False)
        self.serialCloseToolsAction.setVisible(True)
        
    def slotCloseSerial(self):
        self.comActionGroup.setDisabled(False)  #enable choose serial
        if not self.myserial.ser.isOpen():
            self.terminal.append("already close.")
            self.serialConnectToolsAction.setVisible(True)
            self.serialCloseToolsAction.setVisible(False)
            self.currentCom=""
            return

        self.readwriteQueue.put("uitouart:::\x03")

        self.readwriteQueue.put("close")
        self.uitoctrlQueue.put("close")
        time.sleep(0.1)
        
        #self.currentCom=""
        self.rootDir="."
        self.terminal.setReadOnly(True)

        row=self.rootDevice.rowCount()    #clear board treemodel
        self.rootDevice.removeRows(0,row) #use for refresh treemodel,these two lines
                                      
        #while self.fileName != "":
        #    if self.tabWidget.currentTab==-1:
        #        break
        #    self.slotCloseTab(self.tabWidget.currentTab)
        
        self.serialConnectToolsAction.setVisible(True)
        self.serialCloseToolsAction.setVisible(False)

        self.terminal.clear()
        
        self.readuart.exit()
        self.ctrl.exit()

        while not self.uitoctrlQueue.empty():
            self.uitoctrlQueue.get()
        while not self.readwriteQueue.empty():
            self.readwriteQueue.get()

        self.emit(SIGNAL("initRecvdata"))
        self.emit(SIGNAL("initMessycode"))
        time.sleep(0.1)
        self.myserial.ser.close()
        #if self.currentBoard=="esp32" or self.currentBoard=="esp8266":
        #    Esp.espCloseReset(self.currentCom,self.currentBoard)
        self.currentCom=""
        self.terminal.setEventFilterEnable(False)

    def slotToolMenuHover(self,action):
        if action.text()=="Serial":
            for i in action.menu().actions():
                if self.currentCom=="":
                    i.setChecked(False)
                elif i.text()==self.currentCom:
                    i.setChecked(True)
                else:
                    pass
        elif action.text()=="board":
            for i in action.menu().actions():
                if i.text()==self.currentBoard:
                    i.setChecked(True)
                else:
                    pass
        else:
            pass
    def slotDownloadFile(self):
        if self.myserial.ser.isOpen()==False:
            self.terminal.append('Please open serial')
            return False

        if self.inDownloadFile==False:
            self.inDownloadFile=True
        else:
            self.terminal.append('already in download model,please wait.')
            return

        self.readwriteQueue.put("uitouart:::\x03")
        time.sleep(0.05)

        self.fileName=self.tabWidget.tabToolTip(self.tabWidget.currentIndex())
        if self.fileName=='':
            self.terminal.append('Please choose file or input something')
            self.inDownloadFile=False
            return False
        if self.fileName=="untitled":
            self.terminal.append('Please save the file before download')
            self.inDownloadFile=False
            return False

        if sys.platform=="linux" and str(self.fileName).find(rootDirectoryPath)>=0:
            afile=self.fileName
        elif sys.platform=="win32" and str(self.fileName).find(":")>=0:
            afile=self.fileName
        elif sys.platform=="darwin" and str(self.fileName).find(rootDirectoryPath)>=0:
            afile=self.fileName
        else:
            afile=self.fileName
            myfile=open(str(currentTempPath+afile[1:]),'w',encoding='utf-8')
            filemsg=self.tabWidget.currentWidget().text()
            if type(filemsg) is bytes:
                filemsg=filemsg.decode('utf-8')
            myfile.write(filemsg)
            myfile.close()

        self.emit(SIGNAL("changeDragDropModel"),False)
        self.uitoctrlQueue.put("downloadfile:::%s"%afile)
            
        return True

    def slotDownloadFileAndRun(self):
        if self.slotDownloadFile():
            self.isDownloadFileAndRun=True
        
    def slotStopProgram(self):
        if self.myserial.ser.isOpen():
            self.terminal.keyPressMsg="else"
            self.readwriteQueue.put("uitouart:::\x03")
            self.inDownloadFile=False
        else:
            self.terminal.append("serial not open")
        
############Tools->InitConfig
    def slotInitConfig(self):
        
        confirmClose = QMessageBox.question(self,"Attention","sure to init?",
                                                    QMessageBox.Ok|QMessageBox.Cancel,
                                                    QMessageBox.Ok)
        if confirmClose==QMessageBox.Ok:
            pass
        elif confirmClose==QMessageBox.Cancel:
            return
        else:
            return

        path=os.getcwd()
        path=path.replace("\\","/")

        configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
        configFile.write("{'serial':'None','updateURL':'https://git.oschina.net/dfrobot/upycraft/raw/master/uPyCraft.json',\
                         'checkFirmware':'check update','address':'China Mainland','workSpace':'null'}")
        configFile.close()
        configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'rU')
        configText=configFile.read()
        configFile.close()

        try:
            jsonDict=eval(configText)
        except Exception:
            QMessageBox.information(self,self.tr("attention"),self.tr("Please put the uPy_Craft and workSpace into non-Chinese dir."),QMessageBox.Ok)
            os.remove("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath)
            return
        self.workspacePath="null"

        self.createWorkSpaceMenu()#reflush workSpace tree

    def slotBurnFirmware(self):
        self.updateFirmware(True)
    
###########Tools->Preferences
        #contains:
        #  slotPreferences
        #  slotLanlocLocation
        #  slotWetherUpdateFirmware
    def slotPreferences(self):
        configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
        configText=configFile.read()
        configFile.close()

        jsonDict=eval(configText)

        self.preferencesDialog=Preferences()
        if jsonDict['address']=="China Mainland":
            self.preferencesDialog.landlocation.locationComboBox.setCurrentIndex(0)
        else:
            self.preferencesDialog.landlocation.locationComboBox.setCurrentIndex(1)

        if jsonDict['checkFirmware']=="check update":
            self.preferencesDialog.configUpdate.checkBinComBox.setCurrentIndex(0)
        else:
            self.preferencesDialog.configUpdate.checkBinComBox.setCurrentIndex(1)

        self.connect(self.preferencesDialog.landlocation.locationComboBox,SIGNAL("activated(int)"),self.slotLanlocLocation)
        self.connect(self.preferencesDialog.configUpdate.checkBinComBox,SIGNAL("activated(int)"),self.slotWetherUpdateFirmware)
        self.preferencesDialog.show()

    def slotLanlocLocation(self,item):
        if self.preferencesDialog.landlocation.locationComboBox.currentText()=="China Mainland":
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
            configText=configFile.read()
            configFile.close()
            jsonDict=eval(configText)

            jsonDict['updateURL']="https://git.oschina.net/dfrobot/upycraft/raw/master/uPyCraft.json"
            jsonDict['address']="China Mainland"
            configText=str(jsonDict)
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
            configFile.write(configText)
            configFile.close()
        else:
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
            configText=configFile.read()
            configFile.close()
            jsonDict=eval(configText)

            jsonDict['updateURL']="https://github.com/DFRobot/uPyCraft/raw/master/uPyCraft.json"
            jsonDict['address']="others"
            configText=str(jsonDict)
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
            configFile.write(configText)
            configFile.close()

    def slotWetherUpdateFirmware(self):
        if self.preferencesDialog.configUpdate.checkBinComBox.currentText()=="check update":
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
            configText=configFile.read()
            configFile.close()
            jsonDict=eval(configText)

            jsonDict['checkFirmware']="check update"
            configText=str(jsonDict)
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
            configFile.write(configText)
            configFile.close()
        else:
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
            configText=configFile.read()
            configFile.close()
            jsonDict=eval(configText)
            
            jsonDict['checkFirmware']="no check"
            configText=str(jsonDict)
            configFile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'w')
            configFile.write(configText)
            configFile.close()

    def slotAbout(self):
        webbrowser.open("http://docs.dfrobot.com.cn/upycraft",0,True)

    def slotTerminalCursorChanged(self):
        if self.terminal.terminalSelect:
            return
        self.moveposition=self.cursor.position()
        self.moveposition+=self.cursorLeftOrRight
        self.cursorLeftOrRight=0
        self.cursor.setPosition(self.moveposition,QTextCursor.MoveAnchor)
        self.terminal.setTextCursor(self.cursor)

    def slotTerminalSetCursor(self):
        self.terminal.terminalSelect=False
        if self.terminal.isReadOnly()==False:
            self.terminal.setTextCursor(self.cursor)   
        
#####
    def pcOpenFile(self,filename):
        print("pcOpenFile:%s"%filename)
        if os.path.isdir(filename)==True:
            if str(filename).split("/")[-1]=="workSpace":
                if sys.platform=="win32":
                    os.startfile(str(filename))
                elif sys.platform=="linux":
                    #subprocess.call(["open",str(filename)])
                    webbrowser.open(filename)
                elif sys.platform=="darwin":#mac debug
                    print("pcopenfile webbrowser")
                    webbrowser.open(filename)
                else:
                    print("other platform3.")
            return

        if not self.editClassFileitem(filename):
            return
        try:
            self.asciiTOutf8(filename)
        except:
            print("file ascii to utf8 err.")
        
        msg=open(filename,"rbU").read()
        if type(msg) is bytes:
            msg=msg.decode('utf-8')
        
        self.tabWidget.createNewTab(filename,msg,self.lexer)
        
    def editClassFileitem(self,filename):
        if filename=="":
            return False
        for i in self.fileitem.list:
            if i==filename:
                openedTabSum=self.tabWidget.count()
                for j in range(0,openedTabSum):
                    if filename==self.tabWidget.tabToolTip(j):
                        self.tabWidget.setCurrentWidget(self.tabWidget.widget(j))
                print("%s already exist"%filename)
                return False
        if sys.platform=="linux" and str(filename).find(rootDirectoryPath)<0:
            return True
        elif sys.platform=="win32" and str(filename).find(":")<0:
            return True
        elif sys.platform=="darwin" and str(filename).find(rootDirectoryPath)<0:
            return True

        return True
            
    def asciiTOutf8(self,path):
        if(os.path.isfile(path)):
            self.convert(path)
        elif os.path.isdir(path):
            self.explore(path)

    def convert(self,file,in_enc="GBK",out_enc="UTF-8"):
        try:
            print("convert " +file)
            f=codecs.open(file,'r',in_enc)
            new_content=f.read()
            codecs.open(file,'w',out_enc).write(new_content)

        except IOError as err:
            print("I/O error: {0}".format(err))


    def explore(self,dir):
        for root,dirs,files in os.walk(dir):
            for file in files:
                path=os.path.join(root,file)
                self.convert(path)

    def boardEsp32(self):
        self.currentBoard="esp32"
        self.emit(SIGNAL("changeCurrentBoard"),self.currentBoard)
        time.sleep(0.005)

        self.autoAPI.clear()
        self.autoAPI.prepare()

        self.exampleTools.setMenu(None)
        #self.exampleMenu.clear()   #QMenu.clear is not work
        self.exampleMenu=QMenu(self.tr("example"))
        self.connect(self.exampleMenu,SIGNAL("triggered(QAction*)"),self.showExamples)

        self.exampleMenu.setStyleSheet("""QMenu {background-color: rgb(254,254,254);}
                                   QMenu::item::selected { background-color: rgb(255,239,227); color: #000;}""")

        self.createExampleMenu()

    def boardEsp8266(self):
        self.currentBoard="esp8266"
        self.emit(SIGNAL("changeCurrentBoard"),self.currentBoard)
        time.sleep(0.005)
        self.autoAPI.clear()
        self.autoAPI.prepare()

        self.exampleTools.setMenu(None)
        self.exampleMenu.clear()    #QMenu.clear is not work
        
        self.createExampleMenu()
        
    def boardPyboard(self):
        self.currentBoard="pyboard"
        self.emit(SIGNAL("changeCurrentBoard"),self.currentBoard)
        time.sleep(0.005)
        
        self.autoAPI.clear()
        self.autoAPI.prepare()
        
        self.exampleTools.setMenu(None)
        self.exampleMenu.clear()    #QMenu.clear is not work,pyboard not use Communicate

        self.createExampleMenu()
    def boardMicrobit(self):
        self.currentBoard="microbit"
        self.emit(SIGNAL("changeCurrentBoard"),self.currentBoard)
        time.sleep(0.005)
        
        for i in MICROPYTHON_APIS:
            self.autoAPI.add(i)

        for i in MICROBIT_QSCI_APIS:
            self.autoAPI.add(i)
        self.autoAPI.clear()  
        self.autoAPI.prepare()
        
        self.exampleTools.setMenu(None)
        self.exampleMenu.clear()    #QMenu.clear is not work,microbit not use Communicate
        
        self.createExampleMenu()

    def boardOther(self):
        self.currentBoard="other"

        self.autoAPI.clear()
        self.autoAPI.prepare()

        self.exampleTools.setMenu(None)
        self.exampleMenu.clear()

    def getPCcommonExamples(self,path):
        if os.path.exists(path):
            exampleList=os.listdir(path)
            for i in exampleList:
                if i.find(".")>0:
                    filename=(path+"/"+i).split("/")
                    commonNum=-1
                    appendFilename=""
                    while True:
                        if filename[commonNum]=="Common":
                            break
                        else:
                            appendFilename="/"+filename[commonNum]+appendFilename
                            commonNum-=1
                    self.PCcommonList.append(appendFilename)
                else:
                    self.getPCcommonExamples(path+"/"+i)

    def getPCboardExamples(self,path):
        if os.path.exists(path):
            exampleList=os.listdir(path)
            for i in exampleList:
                if i.find(".")>0:
                    filename=(path+"/"+i).split("/")
                    boardNum=-1
                    appendFilename=""
                    while True:
                        if filename[boardNum]=="ESP32" or \
                           filename[boardNum]=="ESP8266" or \
                           filename[boardNum]=="pyboard" or \
                           filename[boardNum]=="microbit":
                            break
                        else:
                            appendFilename="/"+filename[boardNum]+appendFilename
                            boardNum-=1
                    self.PCboardList.append(appendFilename) 
                else:
                    self.getPCboardExamples(path+"/"+i)

    def getPCexamples(self,path,menu):
        if os.path.exists(path):
            exampleList=os.listdir(path)
            for i in exampleList:
                if i.find(".")>0:
                    mymsg = i
                    i = QAction(i,self)
                    i.setStatusTip(path+"/"+mymsg)
                    menu.addAction(i)
                else:
                    sencondMenu = menu.addMenu(i)
                    self.getPCexamples(path+"/"+i,sencondMenu)

    def addPCcommonExamples(self,path,menu,allpath):
        pathList=path.split("/")
        if pathList[1].find(".")>0:
            exampleAction=QAction(pathList[1],self)
            exampleAction.setStatusTip("%s/AppData/Local/uPyCraft/examples/Common/%s"%(rootDirectoryPath,allpath))
            menu.addAction(exampleAction)
            return
        menuList=[]
        for i in menu.findChildren(QMenu):
            menuList.append(i.title())
        lenthpath0 = len(pathList[0])+1
        if pathList[1] in menuList:
            for i in menu.findChildren(QMenu):
                if i.title()==pathList[1]:
                    self.addPCcommonExamples(path[lenthpath0:] ,i,allpath)
        else:
            newmenu=menu.addMenu(pathList[1])
            self.addPCcommonExamples(path[lenthpath0:] ,newmenu,allpath)

    def showExamples(self,action):
        if os.path.exists(action.statusTip()):
            self.fileName=action.statusTip()
            self.pcOpenFile(self.fileName)
        else:
            self.terminal.append("None File")

    def getPCLibFile(self,item,path):#mac debug
        if not os.path.exists(path):
            return
        libFileList=os.listdir(path)
        for i in libFileList:
            if not os.path.isdir(path+"/"+i):
                if i[0]=="." or i.find(".lnk")>0 or i.find(".")<0:
                    continue
                itemLib=QStandardItem(QIcon(":/treeFileOpen.png"),i)
                item.appendRow(itemLib)
            else:
                itemLib=QStandardItem(QIcon(":/treeMenuClosed.png"),i)
                item.appendRow(itemLib)
                self.getPCLibFile(itemLib,path+"/"+i)

    def createReflushTree(self,item,msg):
        if type(msg) is str:
            itemDevice=QStandardItem(msg)
            item.appendRow(itemDevice)
            self.checkDefaultProgram=""
            self.getDefaultFile(itemDevice)
  
            item.removeRow(itemDevice.row())
            itemDevice=QStandardItem(QIcon(":/treeFileOpen.png"),msg)
            if self.myDefaultProgram==self.checkDefaultProgram:
                itemDevice.setForeground(QBrush(QColor(255,0,0)))
                
            item.appendRow(itemDevice)
            
        elif type(msg) is dict:
            for i in msg:
                k=eval("%s"%msg[i])
                i=i.split("/")
                itemDevice=QStandardItem(QIcon(":/treeMenuClosed.png"),"%s"%i[-1])
                item.appendRow(itemDevice)
                self.createReflushTree(itemDevice,k)
        elif type(msg) is list:
            for i in msg:
                if type(i) is str:
                    self.createReflushTree(item,i)
                elif type(i) is dict:
                    self.createReflushTree(item,i)           
        else:
            pass

    def getDefaultFile(self,item):
        self.checkDefaultProgram = "/"+item.text()+self.checkDefaultProgram
        if item.parent().text()=="device":
            if self.currentBoard=="esp8266":
                self.checkDefaultProgram = self.rootDir+self.checkDefaultProgram
            elif self.currentBoard=="esp32":
                self.checkDefaultProgram = self.rootDir+self.checkDefaultProgram
            elif self.currentBoard=="pyboard":
                self.checkDefaultProgram = self.rootDir+self.checkDefaultProgram
            elif self.currentBoard=="microbit":
                self.checkDefaultProgram=self.checkDefaultProgram.split("/")[-1]
            else:
                self.checkDefaultProgram = self.rootDir+self.checkDefaultProgram
            return
        self.getDefaultFile(item.parent())

    def deletePCFile(self,filename):
        if filename.find("uPy_lib")>=0:
            if filename.split("/")[-1]=="uPy_lib":
                return
        elif filename.find("workSpace")>=0:
            if filename.split("/")[-1]=="workSpace" or filename.split("/")[-1]=="user_lib":
                return
            if os.path.isdir(filename):
                os.rmdir(filename)
            else:
                os.remove(filename)
                if filename in self.fileitem.list:
                    num=0
                    while num<self.fileitem.size:
                        text = self.tabWidget.tabToolTip(num)
                        if text==filename:
                            self.tabWidget.removeTab(num)
                            self.fileitem.list.remove(filename)
                            self.fileitem.size-=1
                            break
                        num+=1

            self.createWorkSpaceMenu()

    def goProgram(self,filename):
        if filename=="":
            return
        if str(filename).find(".py")<0 and str(filename).find(".mpy")<0:
            print("not py or mpy file.")
            return

        if self.myserial.ser.isOpen():
            self.uitoctrlQueue.put("goprogram:::%s"%filename)
            self.keyPressMsg=""
        else:
            self.terminal.append("serial not already open")

    def treeRightMenuRunFile(self):
        if str(self.fileName).find(":")>0:
            self.terminal.append("This file not in Board")
            return
        self.goProgram(self.fileName)

    def treeRightMenuOpenFile(self):
        if sys.platform=="linux" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.pcOpenFile(self.fileName)
            return
        elif sys.platform=="win32" and str(self.fileName).find(":")>=0:
            self.pcOpenFile(self.fileName)
            return
        elif sys.platform=="darwin" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.pcOpenFile(self.fileName)
        
        if str(self.fileName).find(".py")>0 or str(self.fileName).find(".txt")>0 or str(self.fileName).find(".json")>0 or str(self.fileName).find(".ini")>0:
            pass
        else:
            self.terminal.append("current version only open py,txt,json,ini.")
            return
        if self.editClassFileitem(self.fileName)==False:
            return

        self.uitoctrlQueue.put("loadfile:::%s"%self.fileName)

    def treeRightMenuCloseFile(self):
        if self.fileName in self.fileitem.list:
            num=0
            while num<self.fileitem.size:
                text = self.tabWidget.tabToolTip(num)
                if text==self.fileName:
                    self.tabWidget.removeTab(num)
                    self.fileitem.list.remove(text)
                    self.fileitem.size-=1
                    break
                num+=1
 
    def treeRightMenuDeleteFile(self):
        if self.fileName=='':
            return
        if sys.platform=="linux" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.deletePCFile(self.fileName)
            return
        elif sys.platform=="win32" and str(self.fileName).find(":")>0:
            self.deletePCFile(self.fileName)
            return
        elif sys.platform=="darwin" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.deletePCFile(self.fileName)
            return
        
        deleteText="confirm delete %s?"%str(self.fileName)

        button=QMessageBox.question(self,"DeleteFile",
                                    deleteText,
                                    QMessageBox.Ok|QMessageBox.Cancel,  
                                    QMessageBox.Ok)  
        if button==QMessageBox.Ok:
            self.uitoctrlQueue.put("deleteboardfile:::%s"%self.fileName)
        elif button==QMessageBox.Cancel:
            print("cancel delete")
        else:  
            return

    def treeRightMenuDefaultProgram(self):
        if not self.myserial.ser.isOpen():
            return

        if sys.platform=="linux" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.terminal.append("This file not in board")
            return
        elif sys.platform=="win32" and str(self.fileName).find(":")>=0:
            self.terminal.append("This file not in board")
            return
        elif sys.platform=="darwin" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.terminal.append("This file not in board")
            return
        elif str(self.fileName).find(".py")<0:
            self.terminal.append("only set py file")
            return
        
        self.myDefaultProgram=self.fileName

        self.uitoctrlQueue.put("setdefaultprogram:::%s"%self.myDefaultProgram)

    def treeRightMenuRename(self):
        if sys.platform=="linux" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.terminal.append("not in board,no rename")
            return
        elif sys.platform=="win32" and str(self.fileName).find(":")>0:
            self.terminal.append("not in board,no rename")
            return
        elif sys.platform=="darwin" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.terminal.append("not in board,no rename")
            return
        
        if not self.myserial.ser.isOpen():
            return

        if self.currentBoard=="microbit":
            self.terminal.append("microbit can not rename")
            return
        self.getTreeRightMenuRename.exec_()

    def treeRightMenuNewDir(self):
        if sys.platform=="linux" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.terminal.append("not board file,no new dir")
            return
        elif sys.platform=="win32" and str(self.fileName).find(":")>0:
            self.terminal.append("not board file,no new dir")
            return
        elif sys.platform=="darwin" and str(self.fileName).find(rootDirectoryPath)>=0:
            self.terminal.append("not board file,no new dir")
            return

        if not self.myserial.ser.isOpen():
            return
        if self.currentBoard=="microbit":
            self.terminal.append("microbit can not mkdir")
            return

        if self.newBoardDirName.isHidden(): 
            self.newBoardDirName.show()

    def updateFirmware(self,isAuto=False):
        if self.currentBoard=="pyboard":
            self.terminal.append("You chose pyboard,you should reconnect to serial or hardware burnt by yourself!")
            self.canNotIdentifyBoard=False
            return
        elif self.currentBoard=="other":
            self.bottomText.append("You chose other board,you should reconnect to serial or hardware burnt by yourself!")
            self.canNotIdentifyBoard=False
            return

        if self.canNotIdentifyBoard:
            self.updateBin = updateNewFirmware("Burn Firmware",isAuto)
        else:
            self.updateBin = updateNewFirmware("update Firmware",isAuto)
        self.connect(self.updateBin.okButton,SIGNAL("clicked()"),self.updateFirmwareOk)
        self.connect(self.updateBin.chooseFirmwareButton,SIGNAL("clicked()"),self.chooseUserFirmware)
        self.updateBin.exec_()

    def chooseUserFirmware(self):
        self.updateBin.hide()
        usersFirmware=QFileDialog.getOpenFileName(self)
        self.updateBin.show()
        usersFirmware=usersFirmware.replace("\\","/")
        self.updateBin.firmwareName.setText(usersFirmware)

    def updateFirmwareOk(self):
        if self.updateBin.isAuto:
            self.updateFirmwareCom=self.updateBin.comChoose.currentText()
        if self.updateBin.radioUPY.isChecked():
            global isCheckFirmware
            if isCheckFirmware:
                if self.myserial.ser.isOpen():
                    self.slotCloseSerial()
                
                print("updata!")
                if os.path.exists("%s/AppData/Local/uPyCraft/update.json"%rootDirectoryPath)==False:
                    self.terminal.append("hope to connect internet and restart the IDE")
                    return
                myfile=open("%s/AppData/Local/uPyCraft/update.json"%rootDirectoryPath,"r")
                page = myfile.read()
                myfile.close()
                #print page
                jsonmsg=json.loads(page)
                firmwareList=jsonmsg["firmware"]
                #print firmwareList
                try:
                    url = firmwareList[str(self.updateBin.boardComboBox.currentText())][0]["url"]
                except:
                    self.terminal.append("Please reOpne the uPy.")

                self.firmwareNameList=url.split("/")
                self.updateSize=firmwareList[str(self.updateBin.boardComboBox.currentText())][0]["size"]
                self.firmwareSavePath=("%s/AppData/Local/uPyCraft/download/%s"%(rootDirectoryPath,self.firmwareNameList[-1]))

                if self.updateBin.boardComboBox.currentText()=="microbit" and os.path.exists(self.firmwareSavePath):
                    self.microbitUpdate()
                    return
        
                if self.updateBin.eraseComboBox.currentText()=='yes' and self.canNotIdentifyBoard:
                    self.updateFirmwareBar=updateNewFirmwareBar("Burn Firmware",True,True)
                elif self.updateBin.eraseComboBox.currentText()=='yes' and not self.canNotIdentifyBoard:
                    self.updateFirmwareBar=updateNewFirmwareBar("update Firmware",True,True)
                elif self.updateBin.eraseComboBox.currentText()=='no' and self.canNotIdentifyBoard:
                    self.updateFirmwareBar=updateNewFirmwareBar("Burn Firmware",False,True)
                else:
                    self.updateFirmwareBar=updateNewFirmwareBar("update Firmware",False,True)

                self.updateFirmwareBar.show()
                
                self.firmwareAny=threadDownloadFirmware(url,self.updateBin.boardComboBox.currentText(),self.firmwareSavePath,self.updateFirmwareCom,\
                                                        self.updateBin.eraseComboBox.currentText(),self.updateSize,\
                                                        self.updateBin.burnAddrComboBox.currentText(),self)
                self.connect(self.firmwareAny,SIGNAL("firmwareAnyDown"),self.firmwareAnyDown)
                self.connect(self.firmwareAny,SIGNAL("firmwareAnyErase"),self.firmwareAnyErase)
                self.connect(self.firmwareAny,SIGNAL("firmwareAnyUpdate"),self.firmwareAnyUpdate)
                self.connect(self.firmwareAny,SIGNAL("goMicrobitUpdate"),self.microbitUpdate)
                self.firmwareAny.start()
                return
            else:
                self.terminal.append("hope to connect internet and try again.")
                return
        else:
            if self.updateBin.firmwareName.text()!="":
                userFirmwareName=self.updateBin.firmwareName.text()
                userFirmwareName=userFirmwareName.replace("\\","/")
                if not os.path.exists(userFirmwareName):
                    self.terminal.append("user choosed firmware file is not exists!")
                    return
                if self.updateBin.boardComboBox.currentText()=="esp8266" or self.updateBin.boardComboBox.currentText()=="esp32":
                    if userFirmwareName[-4:] != ".bin":
                        self.terminal.append("choosed esp8266 or esp32,firmware must be '.bin' at the end.")
                        return
                if self.updateBin.boardComboBox.currentText()=="microbit":
                    if userFirmwareName[-4:] != ".hex":
                        self.terminal.append("choosed micro:bit,firmware must be '.hex' at the end.")
                        return
                if self.myserial.ser.isOpen():
                    self.slotCloseSerial()
                    
                userFirmwareSize=os.path.getsize(userFirmwareName)
                
                #board:self.updateBin.boardComboBox.currentText()
                #savepath:userFirmwareName
                #com:self.updateFirmwareCom
                #iserase:self.updateBin.eraseComboBox.currentText()
                #size:userFirmwareSize
                if self.updateBin.boardComboBox.currentText()=="microbit":
                    self.firmwareSavePath=userFirmwareName
                    self.microbitUpdate()
                    return
                
                if self.updateBin.eraseComboBox.currentText()=='yes':
                    self.updateFirmwareBar=updateNewFirmwareBar("Burn Firmware",True,False)
                else:
                    self.updateFirmwareBar=updateNewFirmwareBar("Burn Firmware",False,False)
                self.updateFirmwareBar.show()
                self.firmwareAny=threadUserFirmware(self.updateBin.boardComboBox.currentText(),userFirmwareName,self.updateFirmwareCom,\
                                                        self.updateBin.eraseComboBox.currentText(),userFirmwareSize,\
                                                        self.updateBin.burnAddrComboBox.currentText(),self)
                self.connect(self.firmwareAny,SIGNAL("firmwareAnyDown"),self.firmwareAnyDown)
                self.connect(self.firmwareAny,SIGNAL("firmwareAnyErase"),self.firmwareAnyErase)
                self.connect(self.firmwareAny,SIGNAL("firmwareAnyUpdate"),self.firmwareAnyUpdate)
                self.connect(self.firmwareAny,SIGNAL("goMicrobitUpdate"),self.microbitUpdate)
                self.firmwareAny.start()
                return

    def firmwareAnyDown(self,per):
        if per==-1:
            self.updateFirmwareBar.close()
            QMessageBox.information(self,self.tr("attention"),self.tr("download false."),QMessageBox.Ok)
            return
        print(per)
        if per>=100:
            per=100
            self.updateFirmwareBar.downloadEvent(per)
            return
        
        self.updateFirmwareBar.downloadEvent(per)

    def firmwareAnyUpdate(self,per):
        if per==-1:
            self.updateFirmwareBar.close()
            QMessageBox.information(self,self.tr("attention"),self.tr("update false."),QMessageBox.Ok)
            return
        elif per==-2:#microbit 
            self.updateFirmwareBar.close()
            return
        
        if per>=100:
            per=100
            self.updateFirmwareBar.updateEvent(per)
            return
        
        self.updateFirmwareBar.updateEvent(per)

    def firmwareAnyErase(self,per):
        if per==-1:
            self.updateFirmwareBar.close()
            QMessageBox.information(self,self.tr("attention"),self.tr("erase false."),QMessageBox.Ok)
            return
        if per>=100:
            per=100
            self.updateFirmwareBar.eraseEvent(per)
            return
        
        self.updateFirmwareBar.eraseEvent(per)

    def microbitUpdate(self):
        microbitUP=QMessageBox.question(self,"microbit update",  
                                    "Please wait,untill the yellow light is not blink.ready to update?",
                                    QMessageBox.Ok|QMessageBox.Cancel,  
                                    QMessageBox.Ok)
        if microbitUP==QMessageBox.Ok:
            if os.name == "posix":
                mount_output=check_output("mount").splitlines()
                mounted_volumes=[x.split()[2] for x in mount_output]
                for volume in mounted_volumes:
                   if volume.endswith(b'MICROBIT'):
                       volume=volume.decode('utf-8')
                       shutil.copyfile(self.firmwareSavePath,volume+"/microbit.hex")
                       break
            elif os.name == "nt":
                if self.get_fs_info(self.firmwareSavePath):
                    QMessageBox.information(self,self.tr("microbit update"),self.tr("update ok"),QMessageBox.Ok)
                else:
                    QMessageBox.information(self,self.tr("microbit update"),self.tr("update false"),QMessageBox.Ok)
            else:
                print("system not support.")
        else:
            pass

    def get_volume_name(self,disk_name):
        vol_name_buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(disk_name), vol_name_buf,
            ctypes.sizeof(vol_name_buf), None, None, None, None, 0)
        return vol_name_buf.value

    def get_fs_info(self,oldpath):
        old_mode=ctypes.windll.kernel32.SetErrorMode(1)
        for disk in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            path='{}:/'.format(disk)
            if os.path.exists(path) and self.get_volume_name(path)=='MICROBIT':
                print(path)
                print("!!!we find microBit!!!")
                path=path+'microbit.hex'
                try:
                    shutil.copyfile(oldpath,path)
                    return True
                except Exception as e:
                    self.terminal.append(str(e))
                    return False
            else:
                pass
        self.terminal.append("!!!we can't find microBit!!!")
        return False

#check version
    def reflushExamples(self):
        self.exampleTools.setMenu(None)
        self.exampleMenu.clear()
        self.createExampleMenu()
        
    def updateThing(self,windowname,title):
        self.updateThingWindowName=windowname
        self.updateIdeExample=attentionUpdata(windowname,title)
        self.connect(self.updateIdeExample.okButton,SIGNAL("clicked()"),self.updateIdeExampleOk)
        self.connect(self.updateIdeExample.cancelButton,SIGNAL("clicked()"),self.updateIdeExampleCancel)
        self.updateIdeExample.exec_()

    def updateIdeExampleCancel(self):
        self.emit(SIGNAL("confirmUpdata"),self.updateThingWindowName.split(" ")[-1]+"cancel")
        self.updateIdeExample.close()

    def updateIdeExampleOk(self):
        self.updataIDEorExamplesBar=ProgressIDEorExampleBar(self.updateThingWindowName+"...")
        self.updataIDEorExamplesBar.show()
        
        self.emit(SIGNAL("confirmUpdata"),self.updateThingWindowName.split(" ")[-1])
        self.updateIdeExample.close()

    def updataPer(self,per):
        if per==-1:
            self.updataIDEorExamplesBar.close()
            QMessageBox.information(self,self.tr("attention"),self.tr("download false."),QMessageBox.Ok)
            return
        
        self.updataIDEorExamplesBar.show()
        self.updataIDEorExamplesBar.timerEvent(per)
        if per>=100:
            per=100
            self.updataIDEorExamplesBar.hide()
    
#signals
    def closeEvent(self,event):
        global timer
        while self.fileName != "":
            if self.tabWidget.currentTab==-1:
                break
            if str(self.tabWidget.tabText(self.tabWidget.currentTab))[0]=="*":
                self.terminal.append("some file is not be saved")
                confirmClose = QMessageBox.question(self,"Attention","some file is not saved, continue close?",
                                                    QMessageBox.Ok|QMessageBox.Cancel,
                                                    QMessageBox.Ok)
                if confirmClose==QMessageBox.Ok:
                    event.accept()
                    self.tabWidget.closeTab(self.tabWidget.currentTab)
                elif confirmClose==QMessageBox.Cancel:
                    event.ignore()
                    return
                else:
                    event.ignore()
                    return
            else:
                self.tabWidget.closeTab(self.tabWidget.currentTab)

        self.timerClose=True
        self.check.exit()
        self.slotCloseSerial()
        
                

    def uiRecvFromUart(self,data):
        self.terminal.uiRecvFromUart(data)

    def uiRecvFromCtrl(self,data):
        if data==".":
            self.cursor.insertText(data)
        elif data=="download false":
            self.terminal.append(data+"\n")
            self.inDownloadFile=False
            self.slotTreeModel()
        elif data=="download ok":
            self.terminal.append(data+"\n")
            self.slotTreeModel()
        elif data=="newdir ok":
            self.slotTreeModel()
        elif data=="rename ok":
            self.slotTreeModel()
        elif data=="rmdir ok":
            self.slotTreeModel()
        elif data=="set Default ok":
            self.slotTreeModel()
        elif data.find("rootDir")>=0:
            data=data.split(":")
            self.rootDir=data[1]
            if self.rootDir=="/":
                self.rootDir="."
            elif self.rootDir == "/flash":
                self.rootDir="."
        elif data=="import os timeout" or data=="getcwd timeout":
            if self.myserial.ser.isOpen()==True:
                self.terminal.append("read timeout,please reset the board or reopen the uPy.")
                self.slotCloseSerial()
        elif data=="runningFileBreakFalse":
            self.inDownloadFile=False
        else:
            self.terminal.append(data+"\n")

    def reflushTree(self,data):
        if data=="err":
            self.terminal.append("reflush tree error")
            self.inDownloadFile=False
            return
        print("reflushTree=====================%s"%data)
        row=self.rootDevice.rowCount()
        self.rootDevice.removeRows(0,row)

        if type(data) is not dict:
            self.terminal.append("reflush tree error, try again.")
            self.inDownloadFile=False
            return

        self.createReflushTree(self.rootDevice,data['.'])

        if self.isDownloadFileAndRun:
            self.isDownloadFileAndRun=False
            if sys.platform=="linux" and str(self.fileName).find(rootDirectoryPath)>=0:
                goProgramFile = str(self.fileName).split("/")[-1]
            elif sys.platform=="win32" and str(self.fileName).find(":")>=0:
                goProgramFile = str(self.fileName).split("/")[-1]
            elif sys.platform=="darwin" and str(self.fileName).find(rootDirectoryPath)>=0:
                goProgramFile = str(self.fileName).split("/")[-1]
            else:
                goProgramFile=self.fileName
            
            self.goProgram(goProgramFile)
        self.inDownloadFile=False

    def changeUpdateFirmwareList(self,mlist):
        global updateFirmwareList
        updateFirmwareList=mlist

    def setIsCheckFirmware(self,ischeck):
        global isCheckFirmware
        isCheckFirmware=ischeck
        
    def checkFiremware(self,msg):
        global updateFirmwareList
        print("checkfirmware=%s"%msg)
        if msg=="false":
            return
        msg=msg.split("\r\n")
        msg=msg[1][1:-1]
        msg=msg.split(",")
        board=msg[0][9:-1]
        
        if board=="esp32":
            self.boardEsp32()
        elif board=="esp8266":
            self.boardEsp8266()
        elif board=="pyboard":
            self.boardPyboard()
            return
        elif board=="microbit":
            self.boardMicrobit()
        else:
            self.boardOther()
            return
        
        myfile=open("%s/AppData/Local/uPyCraft/config.json"%rootDirectoryPath,'r')
        jsonMsg=myfile.read()
        myfile.close()
        jsonDict=eval(jsonMsg)

        if str(jsonDict['checkFirmware'])=="no check":
            return
        if board=="microbit":
            nowVersionDate=msg[3].split(";")[0].split(" ")
            nowVersionDate=nowVersionDate[-1]
        else:
            nowVersionDate=msg[3].split(" ")
            nowVersionDate=nowVersionDate[-1][:-1]
        print(board)
        print(nowVersionDate)
        if updateFirmwareList:
            newVersion=updateFirmwareList[board][0]["version"].split(" ")
            newVersionDate=newVersion[-1]
            if newVersionDate>nowVersionDate:
                print("has new firmware")
                self.updateFirmware()
            else:
                print("no new firmware")
        else:
            print("internal false")
        

    def loadFileSig(self,filename,data):
        self.tabWidget.createNewTab(filename,data,self.lexer)

    def deleteBoardFileSig(self,deletedFile):
        self.terminal.append("delete ok")
        if deletedFile in self.fileitem.list:
            num=0
            while num<self.fileitem.size:
                text = self.tabWidget.tabToolTip(num)
                if text==deletedFile:
                    self.tabWidget.removeTab(num)
                    self.fileitem.list.remove(deletedFile)
                    self.fileitem.size-=1
                    break
                num+=1
        self.slotTreeModel()

    def getTreeRenameOk(self):
        oldname = self.fileName
        if self.currentBoard=="esp32":
            if self.fileName==self.rootDir:
                self.terminal.append("root dir not be change")
                return
        elif self.currentBoard=="esp8266":
            if self.fileName==self.rootDir:
                self.terminal.append("root dir not be change")
                return
        elif self.currentBoard=="pyboard":
            if self.fileName==self.rootDir:
                self.terminal.append("root dir not be change")
                return
        else:
            print("*********renamecontinue")
        readyChangeName=""
        if str(self.fileName).find(".py")>0 or \
           str(self.fileName).find(".json")>0 or \
           str(self.fileName).find(".txt")>0 or \
           str(self.fileName).find(".ini")>0: 
            nameList=str(self.fileName).split("/")
            for i in nameList:
                if i=="":
                    readyChangeName="/"
                    continue
                elif i.find(".py")>0 or i.find(".json")>0 or i.find(".txt")>0 or i.find(".ini")>0:
                    readyChangeName=readyChangeName+self.getTreeRightMenuRename.nameLineEdit.text()
                else:
                    readyChangeName=readyChangeName+i+"/"

            #close tab about this file,if it is opened
            if oldname in self.fileitem.list:
                openedfilesize=self.fileitem.size
                openedtab=0
                while openedfilesize:
                    if oldname==self.tabWidget.tabToolTip(openedtab):
                        self.tabWidget.removeTab(openedtab)
                        self.fileitem.list.remove(oldname)
                        self.fileitem.size-=1
                        break
                    openedtab+=1
                    openedfilesize-=1
            
            self.uitoctrlQueue.put("rename:::%s:::%s"%(str(oldname),readyChangeName))
        else:#rename of dir
            oldname = self.fileName
            readyChangeName=""
            nameList=oldname.split("/")
            for i in nameList:
                if i=="":
                    readyChangeName="/"
                    continue
                elif i==nameList[-1]:
                    readyChangeName=readyChangeName+self.getTreeRightMenuRename.nameLineEdit.text()
                else:
                    readyChangeName=readyChangeName+i+"/"
                    
            print("oldname:%s,newname:%s"%(oldname,readyChangeName))
            self.uitoctrlQueue.put("rename:::%s:::%s"%(str(oldname),readyChangeName))

    def getBoardDirName(self):
        if self.newBoardDirName.nameLineEdit.text()=="":
            self.terminal.append("None board name")
        else:
            if str(self.newBoardDirName.nameLineEdit.text()).find(".")>=0:
                self.terminal.append("error board dir name")
            else:
                readyDirList=str(self.fileName).split("/")
                readyDir=""
                if self.currentBoard=="esp32":
                    if readyDirList[0]==".":
                        readyDir="."
                    for adir in readyDirList:
                        if str(adir).find(".")<0 and adir != "":
                            readyDir = readyDir+"/"+str(adir)
                elif self.currentBoard=="esp8266":
                    if readyDirList[0]==".":
                        readyDir="."
                    for adir in readyDirList:
                        if str(adir).find(".")<0 and adir != "":
                            readyDir = readyDir+"/"+str(adir)
                elif self.currentBoard=="pyboard":
                    if readyDirList[0]==".":
                        readyDir="."
                    for adir in readyDirList:
                        if str(adir).find(".")<0 and adir != "":
                            readyDir = readyDir+"/"+str(adir)
                elif  self.currentBoard=="microbit":
                    for adir in readyDirList:
                        if str(adir).find(".")<0 and adir != "":
                            readyDir = readyDir+"/"+str(adir)
                else:
                    if readyDirList[0]==".":
                        readyDir="."
                    for adir in readyDirList:
                        if str(adir).find(".")<0 and adir != "":
                            readyDir = readyDir+"/"+str(adir)
                print("currentBoard=%s,selfname=%s"%(self.currentBoard,self.fileName))
                self.uitoctrlQueue.put("createnewdir:::%s:::%s"%(readyDir,self.newBoardDirName.nameLineEdit.text()))

    def renameDirDeleteDirTab(self,renameDirDeleteOpenedTab):
        renameDirFileList=[]
        renameDirDeleteOpenedTab=str(renameDirDeleteOpenedTab).split("'")
        for i in renameDirDeleteOpenedTab:
            if i.find("[")>=0 or i.find(",")>=0 or i.find("]")>=0:
                pass
            else:
                renameDirFileList.append(i)

        for i in renameDirFileList:
            if i in self.fileitem.list:
                openedfilesize=self.fileitem.size
                
                openedtab=0
                while openedfilesize:
                    if i==self.tabWidget.tabToolTip(openedtab):
                        self.tabWidget.removeTab(openedtab)
                        self.fileitem.list.remove(i)
                        self.fileitem.size-=1
                        break
                    openedtab+=1
                    openedfilesize-=1

    def timerCloseTerminal(self):
        self.uitoctrlQueue.put("close")
        self.readwriteQueue.put("close")
        time.sleep(0.1)

        self.myserial.ser.close()

        row=self.rootDevice.rowCount()    #clear board treemodel
        self.rootDevice.removeRows(0,row) #use for refresh treemodel,these two lines
        
        self.serialConnectToolsAction.setVisible(True)
        self.serialCloseToolsAction.setVisible(False)
            
        self.readuart.exit()
        self.ctrl.exit()

        while not self.uitoctrlQueue.empty():
            self.uitoctrlQueue.get()
        while not self.readwriteQueue.empty():
            self.readwriteQueue.get()

        self.emit(SIGNAL("initRecvdata"))
        self.emit(SIGNAL("initMessycode"))
            
        self.terminal.clear()
        self.terminal.setReadOnly(True)
        self.terminal.setEventFilterEnable(False)

    def timerAddComMenu(self,port):
        port=QAction(port,self)
        port.setCheckable(True)
        self.comMenu.addAction(self.comActionGroup.addAction(port))
    def timerSetComMenu(self,port):
        port=QAction(port,self)
        port.setCheckable(True)
        self.comMenu.addAction(port)
        self.comMenuTools.setMenu(self.comMenu)
    def timerClearComMenu(self):
        self.comMenu.clear()

    def fun_timer(self):
        global timer
        if self.timerClose:
            timer.cancel()
            return
        mylist=self.myserial.Port_List()
        for i in mylist:
            if i in self.serialComList:
                continue
            self.serialComList.append(i)

            self.emit(SIGNAL("timerAddComMenu"),i)

        for i in self.serialComList:
            if i not in mylist:
                self.serialComList.remove(i)
                self.emit(SIGNAL("timerClearComMenu"))
                time.sleep(0.1)
                for j in self.serialComList:
                    self.emit(SIGNAL("timerSetComMenu"),j)
        if self.currentCom=="":
            self.serialConnectToolsAction.setVisible(True)
            self.serialCloseToolsAction.setVisible(False)
        elif self.currentCom not in self.serialComList:
            self.currentCom=""
            self.emit(SIGNAL("timerCloseTerminal"))
        timer=threading.Timer(0.2,self.fun_timer)
        timer.start()

    

app=QApplication(sys.argv)
main=MainWidget()
if mainShow:
    main.show()
    app.exec_()























