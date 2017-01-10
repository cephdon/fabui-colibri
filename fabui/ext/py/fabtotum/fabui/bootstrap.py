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

__authors__ = "Daniel Kesler"
__license__ = "GPL - https://opensource.org/licenses/GPL-3.0"
__version__ = "1.0"

# Import standard python module
import gettext
import json
import os, re

# Import external modules

# Import internal modules
from fabtotum.fabui.config import ConfigService

# Set up message catalog access
tr = gettext.translation('gpusher', 'locale', fallback=True)
_ = tr.ugettext

def read_eeprom(gcodeSender):
        
    def serialize(string_source, regex_to_serach, keys):
        match = re.search(regex_to_serach, string_source, re.IGNORECASE)
        if match != None:
            string = match.group(1)
            object = {}
            object.update({'string':string})
            for index in keys:
                match_temp = re.search(index+'([0-9.]+)', string, re.IGNORECASE)
                if match_temp != None:
                    val = match_temp.group(1)
                    object.update({index:val})
            return object
            
    def getServoEndstopValues(string_source):
        match = re.search('Servo\sEndstop\ssettings:\sR:\s([0-9.]+)\sE:\s([0-9.]+)', string_source, re.IGNORECASE)
        if match != None:
            object = {'r': match.group(1), 'e': match.group(2)}
            return object
    
    #reply = app.macro('M503', None, 1, _("Reading settings from eeprom"), verbose=False)
    reply = gcodeSender.send('M503', group='bootstrap')

    eeprom = {}

    for line in reply:
        line = line.strip()
        
        if line.startswith('M92 '):
            eeprom["steps_per_unit"] = serialize(line, '(M92\sX[0-9.]+\sY[0-9.]+\sZ[0-9.]+\sE[0-9.]+)', ['x', 'y', 'z', 'e'])
        elif line.startswith('M203'):
            eeprom["maximum_feedrates"] = serialize(line, '(M203\sX[0-9.]+\sY[0-9.]+\sZ[0-9.]+\sE[0-9.]+)', ['x', 'y', 'z', 'e'])
        elif line.startswith('M201'):
            eeprom["maximum_accelaration"] = serialize(line, '(M201\sX[0-9.]+\sY[0-9.]+\sZ[0-9.]+\sE[0-9.]+)', ['x', 'y', 'z', 'e'])
        elif line.startswith('M204'):
            eeprom["acceleration"] = serialize(reply[9], '(M204\sS[0-9.]+\sT1[0-9.]+)', ['s', 't1'])
        elif line.startswith('M205'):
           eeprom["advanced_variables"] = serialize(line,'(M205\sS[0-9.]+\sT0[0-9.]+\sB[0-9.]+\sX[0-9.]+\sZ[0-9.]+\sE[0-9.]+)', ['s', 't', 'b', 'x', 'z', 'e'])
        elif line.startswith('M206'):
            eeprom["home_offset"] = serialize(line,'(M206\sX[0-9.]+\sY[0-9.]+\sZ[0-9.]+)', ['x', 'y', 'z'])
        elif line.startswith('M31'):
            eeprom["pid"] = serialize(line,'(M301\sP[0-9.]+\sI[0-9.]+\sD[0-9.]+)', ['p', 'i', 'd'])
        elif line.startswith('Z Probe Length') or line.startswith('Probe Length'):
            eeprom["probe_length"] = line.split(':')[1].strip()
        elif line.startswith('Servo Endstop'):
            eeprom["servo_endstop"] = getServoEndstopValues(line)
    
    return eeprom

def customHardware(gcodeSender, config, log):
    """
    Revision for customs edits
    """
    custom_overrides_file = config.get('settings', 'custom_overrides')
    if custom_overrides_file:
        with open(custom_overrides_file, 'r') as f:
            for line in f:
                gcodeSender.send(line.strip())
    
    logic = 1 if int(config.get('settings', 'invert_x_endstop_logic')) else 0

    #set x endstop logic
    gcodeSender.send("M747 X{0}".format(logic), group='bootstrap')
    #save settings
    gcodeSender.send("M500", group='bootstrap')
    log.debug("Custom Hardware")

def hardware1(gcodeSender, config, log):
    """
    Rev1: September 2014 - May 2015
    - Original FABtotum
    """
    
    config.set('settings', 'hardware.id', 1)
    config.set('settings', 'feeder.show', True)
    config.set('settings', 'a', 177.777778)
    config.save('settings')
    
    log.debug("Rev1")
    
def hardware2(gcodeSender, config, log):
    """
    Rev2: June 2015 - August 2015
    - Simplified Feeder (Removed the disengagement and engagement procedure), if you want you can update it easily following this Tutorial: Feeder update.
    - Bowden tube improvement (Added a protection external sleeve to avoid the bowden tube get stuck in the back panel).
    - Endstops logic inverted.
    """
    #invert x endstop logic
    gcodeSender.send("M747 X1", group='bootstrap')
    #set maximum feedrate
    gcodeSender.send("M203 X550.00 Y550.00 Z15.00 E12.00", group='bootstrap')
    #save settings
    gcodeSender.send("M500", group='bootstrap')
    
    config.set('settings', 'hardware.id', 2)
    config.set('settings', 'feeder.show', True)
    config.set('settings', 'a', 177.777778)
    config.save('settings')
    
    log.debug("Rev2")
    
def hardware3(gcodeSender, config, log):
    """
    Rev3: Aug 2015 - Jan 2016
    - Back panel modified to minimize bowden tube collisions
    - Hotplate V2 as standard duty hotplate
    - Reed sensor (Contactless sensor for the frontal door)
    - Head V1 (hybrid) discontinued
    - Milling Head V2 (store.fabtotum.com/eu/store/milling-head-v2.html).
    - Print head V2 (store.fabtotum.com/eu/store/printing-head-v2.html).
    """
    #invert x endstop logic
    gcodeSender.send("M747 X1", group='bootstrap')
    #set maximum feedrate
    gcodeSender.send("M203 X550.00 Y550.00 Z15.00 E12.00", group='bootstrap')
    #save settings
    gcodeSender.send("M500", group='bootstrap')
    
    config.set('settings', 'hardware.id', 3)
    config.set('settings', 'feeder.show', False)
    config.set('settings', 'a', 177.777778)
    config.save('settings')
    
    log.debug("Rev3")
    
    
def hardware4(gcodeSender, config, log):
    """
    Rev4(CORE): Jan 2016 - xxx
    - TBA
    """
    #invert x endstop logic
    gcodeSender.send("M747 X1", group='bootstrap')
    #set maximum feedrate
    gcodeSender.send("M203 X550.00 Y550.00 Z15.00 E12.00", group='bootstrap')
    #save settings
    gcodeSender.send("M500", group='bootstrap')
    
    eeprom = read_eeprom(gcodeSender)
    
    config.set('settings', 'hardware.id', 4)
    config.set('settings', 'feeder.show', False)
    config.set('settings', 'a', 88.888889)
    config.set('settings', 'e', eeprom['steps_per_unit']['e'])
    config.save('settings')
    
    log.debug("Rev4")
    
def hardware5(gcodeSender, config, log):
    """
    Rev5(CORE): Oct 2016 - xxx
    - RPi3
    """
    #invert x endstop logic
    gcodeSender.send("M747 X1", group='bootstrap')
    #set maximum feedrate
    gcodeSender.send("M203 X550.00 Y550.00 Z15.00 E12.00", group='bootstrap')
    #save settings
    gcodeSender.send("M500", group='bootstrap')
    
    eeprom = read_eeprom(gcodeSender)
    
    config.set('settings', 'hardware.id', 5)
    config.set('settings', 'feeder.show', False)
    config.set('settings', 'a', 88.888889)
    config.set('settings', 'e', eeprom['steps_per_unit']['e'])
    config.save('settings')
    
    log.debug("Rev5")

def hardwareBootstrap(gcs, config = None, logger = None):
    if not config:
        config = ConfigService()
    
    config.reload()
    
    if logger:
       log = logger
    else:
        log = logging.getLogger('GCodeService')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s : %(message)s")
        ch.setFormatter(formatter)
        log.addHandler(ch)
        
        
    try:
        color = config.get('settings', 'color')
    except KeyError:
        color = {
            'r' : 255,
            'g' : 255,
            'b' : 255,
        }
    
    try:
        safety_door = config.get('settings', 'safety.door')
    except KeyError:
        safety_door = 0
    
    try:
        switch = config.get('settings', 'switch')
    except KeyError:
        switch = 0
    
    try:
        collision_warning = config.get('settings', 'safety.collision_warning')
    except KeyError:
        collision_warning = 0

    gcs.atomic_begin(group='bootstrap')

    # Get hardware id (version)
    reply = gcs.send('M763', group='bootstrap')
    try:
        hardwareID = reply[0].strip()
    except Exception as e:
        print "ERROR", e
        hardwareID = 0
    
    # Raise probe
    gcs.send('M402', group='bootstrap')
    # Send ALIVE
    gcs.send('M728', group='bootstrap')

    # Set ambient colors
    gcs.send("M701 S{0}".format(color['r']), group='bootstrap')
    gcs.send("M702 S{0}".format(color['g']), group='bootstrap')
    gcs.send("M703 S{0}".format(color['b']), group='bootstrap')
    
    # Set safety door open warnings: enabled/disabled
    gcs.send("M732 S{0}".format(safety_door), group='bootstrap')
    # Set collision warning: enabled/disabled
    gcs.send("M734 S{0}".format(collision_warning), group='bootstrap')
    # Set homing preferences
    gcs.send("M714 S{0}".format(switch), group='bootstrap')
    
    # Load Head
    #~ try:
    head_file = os.path.join( config.get('hardware', 'heads'), config.get('settings', 'hardware.head') + '.json');
    
    try:
        with open(head_file) as json_f:
            head = json.load(json_f)
            
        pid     = head.get('pid')
        th_idx  = int(head.get('thermistor_index', 0))
        mode    = int(head.get('working_mode', 0))
        offset  = float(head.get('probe_offset', 0))
        fw_id   = int(head.get('fw_id',0))
        max_temp= int(head.get('max_temp',0))
        
        # Set head PID
        if pid is not None:
            gcs.send( head['pid'], group='bootstrap' )
        
        # Set Thermistor index
        gcs.send( "M800 S{0}".format( th_idx ), group='bootstrap' )
        
        # Set max_temp
        if max_temp > 25:
            gcs.send( "M801 S{0}".format( max_temp ), group='bootstrap' )
        
        # Working mode
        gcs.send( "M450 S{0}".format( mode ), group='bootstrap' )
        
        # Set installed head
        if fw_id is not None:
            gcs.send( "M793 S{0}".format( fw_id ), group='bootstrap' )
        
        # Set probe offset
        if offset:
            gcs.send( "M710 S{0}".format( offset ), group='bootstrap' )
        
        # Save settings
        gcs.send( "M500", group='bootstrap' )
    except Exception as e:
        print "ERROR (head install)", e
        
    # Execute version specific intructions
    HW_VERSION_CMDS = {
        'custom' : customHardware,
        '1'      : hardware1,
        '2'      : hardware2,
        '3'      : hardware3,
        '4'      : hardware4,
        '5'      : hardware5
    }
    if config.get('settings', 'settings_type') == 'custom':
        customHardware(gcs, config, log)
    elif hardwareID in HW_VERSION_CMDS:
        HW_VERSION_CMDS[hardwareID](gcs, config, log)
    else:
        log.error("Unsupported hardware version: %s", hardwareID)

    gcs.atomic_end()
