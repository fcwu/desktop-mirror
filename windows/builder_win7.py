#!/usr/bin/python

from distutils.core import setup
from glob import glob
from py2exe.build_exe import py2exe
import sys

import os
import subprocess

NSIS_SCRIPT_TEMPLATE = r"""
!include "MUI2.nsh"
!include "x64.nsh"

!define py2exeOutputDirectory '{output_dir}\'
!define exe '{program_name}.exe'

SetCompressor /SOLID lzma
Caption "{program_name} - {program_desc}"

Name '{program_name}'
OutFile ${{exe}}
Icon '{icon_location}'
InstallDir $PROGRAMFILES\{program_name}

InstallDirRegKey HKLM "Software\{program_name}" "Install_Dir"
RequestExecutionLevel admin

;--------------------------------

; Pages

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
;--------------------------------

; The stuff to install
Section "{program_name} (required)"

  SectionIn RO

  SetOutPath $INSTDIR

  ; Put file there
  File /r '${{py2exeOutputDirectory}}\*'

  ; Screen Recorder
  ; https://github.com/rdp/screen-capture-recorder-to-video-windows-free
  ${{If}} ${{RunningX64}}
    ExecWait "regsvr32 /s screen-capture-recorder-x64.dll"
    ExecWait "regsvr32 /s audio_sniffer-x64.0.3.13.dll"
    ExecWait "$INSTDIR\vcredist_x64.exe /passive /qb /i "
  ${{Else}}
    ExecWait "regsvr32 /s screen-capture-recorder.dll"
    ExecWait "regsvr32 /s audio_sniffer.0.3.13.dll"
    ExecWait "$INSTDIR\vcredist_x86.exe /passive /qb /i "
  ${{EndIf}}

  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\{program_name} "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{program_name}" "DisplayName" "{program_name}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{program_name}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{program_name}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{program_name}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

  ExecWait "$INSTDIR\BonjourPSSetup.exe /qr"
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\{program_name}"
  CreateShortCut "$SMPROGRAMS\{program_name}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\{program_name}\{program_name}.lnk" "$INSTDIR\advanced.exe" "" "$INSTDIR\share\icon.ico"

SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{program_name}"
  DeleteRegKey HKLM SOFTWARE\{program_name}

  ; Remove directories used
  RMDir /r "$SMPROGRAMS\{program_name}"
  RMDir /r "$INSTDIR"

SectionEnd

"""


class NSISScript(object):

    NSIS_COMPILE = r'C:\Program Files\NSIS\makensis'

    def __init__(self, program_name, program_desc, dist_dir, icon_loc):
        self.program_name = program_name
        self.program_desc =  program_desc
        self.dist_dir = dist_dir
        self.icon_loc = icon_loc

        self.pathname = "setup_%s.nsi" % self.program_name

    def create(self):
        contents = NSIS_SCRIPT_TEMPLATE.format(
                    program_name = self.program_name,
                    program_desc = self.program_desc,
                    output_dir = self.dist_dir,
                    icon_location = os.path.join(self.dist_dir, self.icon_loc))

        with open(self.pathname, "w") as outfile:
            outfile.write(contents)

    def compile(self):
        subproc = subprocess.Popen(
            # "/P5" uses realtime priority for the LZMA compression stage.
            # This can get annoying though.
            [self.NSIS_COMPILE, self.pathname, "/P5"], env=os.environ)
        subproc.communicate()

        retcode = subproc.returncode

        if retcode:
            raise RuntimeError("NSIS compilation return code: %d" % retcode)


class build_installer(py2exe):
    # This class first builds the exe file(s), then creates an NSIS installer
    # that runs your program from a temporary directory.
    def run(self):
        # First, let py2exe do it's work.
        py2exe.run(self)

        lib_dir = self.lib_dir
        dist_dir = self.dist_dir

        # Create the installer, using the files py2exe has created.
        script = NSISScript('desktop-mirror',
                            'A tools to stream screen(video and audio) out',
                            'dist',
                            os.path.join('share', 'icon.ico'))
        print "*** creating the NSIS setup script***"
        script.create()
        print "*** compiling the NSIS setup script***"
        script.compile()

zipfile = r"lib\shardlib"

sys.path.append('lib')

manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1"
manifestVersion="1.0">
<assemblyIdentity
    version="0.64.1.0"
    processorArchitecture="x86"
    name="Controls"
    type="win32"
/>
<description>Desktop Mirror</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
"""

"""
installs manifest and icon into the .exe
but icon is still needed as we open it
for the window icon (not just the .exe)
changelog and logo are included in dist
      data_files=["yourapplication.ico"]
            "other_resources": [(24,1,manifest)]
    data_files=data_files,
"""
data_files = [
              ("share", ('share\\crtmpserver.lua', 'share\\default_win7.ini', 'share\\desktop-mirror-64.png', 'share\\icon.ico')),
              ("", glob(r'windows\*.exe')),
              ("", glob(r'windows\*.dll')),
              ]
includes = []
excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger',
            'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
            'Tkconstants', 'Tkinter']
packages = []
dll_excludes = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl84.dll',
                'tk84.dll']

setup(
    windows=[
        {
            "script": "lib/advanced.py",
            "icon_resources": [(1, "icon.ico")]
        }
    ],
    data_files=data_files,
    options={"py2exe": {"compressed": 2,
                        "optimize": 2,
                        "includes": includes,
                        "excludes": excludes,
                        "packages": packages,
                        "dll_excludes": dll_excludes,
                        "bundle_files": 3,
                        "dist_dir": "dist",
                        "xref": False,
                        "skip_archive": False,
                        "ascii": False,
                        "custom_boot_script": '',
                       }
             },
    zipfile = zipfile,
    cmdclass = {"py2exe": build_installer},
)
