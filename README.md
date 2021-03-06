desktop-mirror
====

![main screen](https://raw.github.com/fcwu/desktop-mirror/master/screenshots/main.png)

A utility to stream screen and audio between Windows, Ubuntu or XBMC. The features include

* Cross platforms in Windows 7, Ubuntu and XBMC
* Encode video to H264 and audio to mp3 via ffmpeg
* Support to stream a area of screen or full screen
* Easily to find available nodes in LAN by mDNS(Avahi)

Find video to show how it works

* [desktop-mirror between Windows, Ubuntu and XBMC](http://youtu.be/9ruu2L2MrSU)
* [Streaming to QNAP's NAS](http://youtu.be/_ODvcmgMZyo)

Install
====

[Download binary for Windows 7](http://qnap-ubuntu.dorowu.com/internal/desktop-mirror.exe)

For ubuntu,

```
$ sudo add-apt-repository ppa:fcwu-tw/ppa
$ sudo apt-get update
$ sudo apt-get install desktop-mirror
```

Build Windows Execution
====

Install Windows 7 32-bits,

1. Install Microsoft Visual Studio Express 2012 for Windows Desktop
2. Install Python 2.7.x and py2exe-0.6.9
3. Install nsis
4. ```git checkout -b win7 origin/win7```, then run ```build.bat```

Troubleshooting
====

1. No audio is streaming out on Ubuntu

    Open pavcontrol, select Recording tab and find "ALSA [plug-ins](avconv)..." as following image

    ![PulseAudio Volume Control](https://raw.github.com/fcwu/desktop-mirror/master/screenshots/pavcontrol.png)

    Check it is capturing the right device.

2. More log messages

    Run the application in console and append parameters "--log-level debug"

License
====

desktop-mirror is under the Apache 2.0 license. See the LICENSE file for details.
