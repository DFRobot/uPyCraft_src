# uPyCraft_src
#### uPyCraft is an IDE designed for micropython that supports Windows 7, Windows 8, Windows 10, MAC OSX 10.11, and above.To make it easier for users to use, uPyCraft is released in green in all systems, no need to install.

## Installation
This requires you to have python3.4, pyqt4, py2exe, qsci, pyserial and pyflakes installed.

1. python3.4:<br>

    download address:https://www.python.org/downloads/windows/ <br>
        add python to the windows environment variable when installed.<br> 

    update pip： python -m pip install -U pip 
        add pip to the windows environment variable, such as C:/Python34/Scripts 
        
    pyserial:pip install pyserial 
    
    py2exe  :pip install py2exe 
    
    pyflakes:pip install pyflakes 
        find api.py and replace with pyflakesChange/api.py 
    
2. pyqt4:<br>

    sip：<br>
        download address:https://www.riverbankcomputing.com/software/sip/download <br>
        
        unpack the directory and open
        exec:
            python configure.py
        
        enter Visual Studio command prompt, changedir to sip installed path
            nmake
            nmake install
        
    PyQt4:
        download address:https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/ <br>
        follow "next" to install. <br>

## Running
Open uPyCraft.py with python3.4 IDE, click the run module button/F5 to run.

## pakege uPyCraft
uPyCraft.exe will created in directory dist/ .
  
