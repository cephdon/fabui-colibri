#!/bin/env python
# -*- coding: utf-8; -*-
#
# (c) 2016 FABtotum, http://www.fabtotum.com
#
# This file is part of FABUI.
#
# FABUI is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# FABUI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FABUI.  If not, see <http://www.gnu.org/licenses/>.

__authors__ = "Marco Rizzuto, Daniel Kesler"
__license__ = "GPL - https://opensource.org/licenses/GPL-3.0"
__version__ = "1.0"

# Import standard python module
import os
import json
import gettext

from fabtotum.fabui.macros.common import getPosition
from fabtotum.fabui.macros.common import doG30

# Import external modules

# Import internal modules


# Set up message catalog access
tr = gettext.translation('gmacro', 'locale', fallback=True)
_ = tr.ugettext


def probe_setup_prepare(app, args = None):
    #~ app.trace( _("Preparing Calibration procedure") )
    #~ app.trace( _("This may take a wile") )
    app.macro("M104 S200",          "ok", 90,   _("Heating Extruder") )
    app.macro("M140 S45",           "ok", 90,   _("Heating Bed (fast)") )
    app.macro("G90",                "ok", 2,    _("Setting rel position"), verbose=False)
    app.macro("G27",                "ok", 100,  _("Homing all axes") )
    app.macro("G0 Z50 F10000",      "ok", 100,    _("G0 Z50 F10000"), verbose=False)
    app.macro("G28",                "ok", 100,  _("Homing all axes") )
    app.macro("G90",                "ok", 2,    _("Setting rel position"), verbose=False)
    app.macro("G0 X86 Y58 Z50 F10000",                "ok", 2,    _("Setting rel position"), verbose=False)
    app.macro("G91",                "ok", 2,    _("Relative mode"), verbose=False)
    app.macro("G0 X17 Y61.5 F6000", "ok", 100,    _("Offset"), verbose=False)
    app.macro("G90",                "ok", 2,    _("Setting rel position"), verbose=False)
    app.macro("G0 Z5 F1000",        "ok", 100,    _("Moving to calibration position") )
    app.macro("G91",                "ok", 2,    _("Setting abs position"), verbose=False)
    #app.macro("M109",               None, 300,  _("Witing for extruder temperature"), warning=False) 
    
def probe_setup_calibrate(app, args = None):
    
    
    app.macro("M104 S0",    "ok", 2,   _("Extruder heating off") )
    app.macro("M140 S0",    "ok", 2,   _("Bed heating off") )
    
    app.trace( _("Calculating Z Max Height") )
    
    app.macro("G90",    "ok", 2,   _("Set Absolute Mode"), verbose=True )
    app.macro("G92 Z0.08",    "ok", 2,   _("Setting paper heigth"), verbose=True )
    app.macro("G0 Z300 F1000",    "ok", 90,   _("Lowering bed"), verbose=True )
    app.trace( _("Bed is down") )
    
    current_position = getPosition(app)
    z_offset_max = current_position['count']['z']
    app.macro('G92 Z{0}'.format(z_offset_max),    "ok", 2,   _("setting position"), verbose=True )
    
    # Get old probe-nozzle height difference
    app.trace( _("Calibrating probe") )
    
    
    app.macro('G0 X86 Y58 Z40 F1000',  "ok", 90,   _("calibration point"), verbose=True )
    app.macro('M401',  "ok", 2,   _("open probe"), verbose=True )
    
    doG30(app)
    
    #app.macro("G0 X86 Y58 Z50 F1000",    "ok", 90,   _("calibration point"), verbose=True )
    #app.macro("M401",    "ok", 90,   _("Open probe"), verbose=True )
    
    # TODO: handle error cases
    z_probe_old = None
    
    data = app.macro("M503", None, 2, _("Reading eeprom"), verbose=False )
    for line in data:
        line = line.strip()
        if line.startswith("Z Probe Length:"):
            z_probe_old = float(line.split("Z Probe Length: ")[1])
    
    app.trace( _("Old Position : {0} mm").format(str(z_probe_old)) )
    
    # get Z position
    data = app.macro("M114", "ok", 2, _("Get Z position"), verbose=False)
    data = data[0]
    z_touch = float(data.split("Z:")[1].split(" ")[0])

    app.trace( _("Current height : {0} mm").format(str(z_touch)) )
    
    # write config to EEPROM
    z_probe_new = abs( z_probe_old + (z_touch - 0.1) )
    app.macro("M710 S{0}".format(z_probe_new), "ok", 2, _("Write config to EEPROM"), verbose=False)
    
    # Store offset to head config
    head_file = os.path.join( app.config.get('hardware', 'heads'), app.config.get('settings', 'hardware.head') + '.json');
    with open(head_file) as json_f:
        head_info = json.load(json_f)
        
    head_info['probe_offset'] = str(round(z_probe_new,2))
    
    with open(head_file, 'w') as outfile:
        json.dump(head_info, outfile, sort_keys=True, indent=4)
    #############################
    
    app.macro("G90",            "ok", 2,    _("Abs_mode"),  verbose=False)
    app.macro("G0 Z50 F1000",   "ok", 3,    _("Moving the plane"), verbose=False)
    app.macro("G28 X0 Y0",      "ok", 90,   _("homing all axis"), verbose=False)
    app.trace( _("Probe calibrated : {0} mm").format(str(z_probe_new)) )
    app.macro("M300",           "ok", 5,    _("Done!"), verbose=False)
    
    return {
        'old_probe_lenght' : str(z_probe_old),
        'new_probe_length' : str(z_probe_new),
        'z_touch'    : str(z_touch)
    }
    
def raise_bed_no_g27(app, args = None):
    #for homing procedure before probe calibration.
    
    zprobe = app.config.get('units', 'zprobe')
    zprobe_disabled = (zprobe['disable'] == 1)
    zmax_home_pos   = float(zprobe['zmax'])
    
    app.macro("M402",   "ok", 4,    _("Raising probe") )
    app.macro("G90",    "ok", 2,    _("Setting abs position"), verbose=False)
    
    if zprobe_disabled:
        app.macro("G27 X0 Y0 Z" + str(zmax_home_pos),   "ok", 100,  _("Homing all axes") )
        app.macro("G0 Z50 F10000",                      "ok", 15,   _("raising") )
    else:
        app.macro("G0 Z20 F10000",  "ok", 15,   _("Raising bed"), verbose=False)
        app.macro("G28",            "ok", 100,  _("Homing all axes") )
