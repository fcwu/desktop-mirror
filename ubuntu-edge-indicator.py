#!/usr/bin/python
from gi.repository import Gtk, GObject
from gi.repository import AppIndicator3 as appindicator
import urllib, re, os, time, datetime

def openit(*args):
    os.system("xdg-open http://www.indiegogo.com/projects/ubuntu-edge")

# both UTC
STARTTIME = datetime.datetime(2013, 7, 22, 15, 0, 0)
ENDTIME = datetime.datetime(2013, 8, 22, 7, 0, 0)

def update(*args):
    # screen scraping of glory
    fp = urllib.urlopen('http://www.indiegogo.com/projects/ubuntu-edge')
    data = fp.read()
    mtch = [x for x in data.split('\n') if '$2,' in x and 'amount' in x and 'medium' in x]
    if len(mtch) != 1:
        ind.set_label("?????", "$32.00m")
        return True
    val = re.search("\$([0-9,]+)<", mtch[0])
    val = val.groups()[0]
    val = val.replace(",", "")
    val = int(val)
    mval = val / 1000000.0
    ind.set_label("$%0.2fm" % mval, "$32.0m")
    lst.get_child().set_text("Last updated: %s" % time.strftime("%H:%M"))
    now = datetime.datetime.utcnow()
    done = now - STARTTIME
    togo = ENDTIME - now
    done_seconds = (done.days * 24 * 60 * 60) + done.seconds
    togo_seconds = (togo.days * 24 * 60 * 60) + togo.seconds
    ratio = float(togo_seconds) / done_seconds
    projected = val + (ratio * val)
    mprojected = projected / 1000000.0
    prj.get_child().set_text("Projected: $%0.2fm" % mprojected)
    return True

if __name__ == "__main__":
    ind = appindicator.Indicator.new("ubuntu-edge-indicator", "",
        appindicator.IndicatorCategory.APPLICATION_STATUS)
    ind.set_status(appindicator.IndicatorStatus.ACTIVE)
    ind.set_label("$$$$$", "$32.0m")

    menu = Gtk.Menu()
    opn = Gtk.MenuItem("Open IndieGogo")
    menu.append(opn)
    lst = Gtk.MenuItem("Last updated: ?????")
    menu.append(lst)
    prj = Gtk.MenuItem("Projected: ?????")
    menu.append(prj)
    menu.show_all()
    opn.connect("activate", openit)

    ind.set_menu(menu)

    GObject.timeout_add_seconds(300, update)
    update()
    Gtk.main()
