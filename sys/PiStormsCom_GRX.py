#!/usr/bin/env python
#
# Copyright (c) 2015 mindsensors.com
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

#mindsensors.com invests time and resources providing this open source code, 
#please support mindsensors.com  by purchasing products from mindsensors.com!
#Learn more product option visit us @  http://www.mindsensors.com/

# History:
# Date       Author          Comments
# June 2017  Seth Tenembaum  Initial Authoring

from mindsensors_i2c import mindsensors_i2c
from fractions import Fraction
import struct, numpy


## GRXCom: this class provides communication functions for PiStorms-GRX.
#  Do not use this class directly in user programs.
class GRXCom():
    class I2C:
        A = mindsensors_i2c(0x34 >> 1)
        B = mindsensors_i2c(0x36 >> 1)
    class TYPE:
        NONE = 0
        ANALOG_INPUT = 1
        DIGITAL_OUTPUT = 2
        DIGITAL_INPUT = 3
        I2C = 4
        ENCODER = 5
        SERIAL = 6
    #class TYPE_SUPPORT must be defined after the entirity of GRXCom is defined
    # because it relies on value which must first be initialized in this class.
    SERVO   = [0x42+i*0x02 for i in range(3)]
    ANALOG  = [0x48+i*0x16 for i in range(3)]
    DIGITAL = [0x8A+i*0x16 for i in range(2)]
    class OFFSET:
        TYPE = 0
        MODE = 1
        RATE = 2
        GO = 3
        DATA = 4
        ENCODER_VALUE = 4
        ENCODER_TARGET = 8
    class REGISTER:
        FIRMWARE_VERSION = 0x00
        VENDOR_NAME = 0x08
        DEVICE_MODEL = 0x10
        FEATURE = 0x18
        COMMAND = 0x41
        LED = 0xB6
        LED_R = 0xB6
        LED_G = 0xB7
        LED_B = 0xB8
        PID = 0xB9
        P_NUMERATOR = 0xB9
        P_DENOMINATOR = 0xBA
        I_NUMERATOR = 0xBB
        I_DENOMINATOR = 0xBC
        D_NUMERATOR = 0xBD
        D_DENOMINATOR = 0xBE
        GO_BUTTON_STATE = 0xBF
        GO_PRESS_COUNT = 0xC0
        BATTERY_VOLTAGE = 0xC1
        TOUCHSCREEN_X = 0xE3
        TOUCHSCREEN_Y = 0xE5
    class COMMAND:
        SHUTDOWN = ord('H')
        RESET_ENCODERS = ord('R')
        UNLOCK_TOUCHSCREEN_CALIBRATION = ord('E')
        SAVE_TOUCHSCREEN_CALIBRATION = ord('t')

    def __init__(self, i2c, address):
        self.i2c = i2c
        self.address = address

    def setType(self, newType, mode=0):
        self.i2c.writeByte(self.address, newType)
        self.i2c.writeByte(self.address+1, mode)

    def digitalRead(self):
        return self.i2c.readByte(self.address + self.OFFSET.DATA)

    def analogRead(self):
        return self.i2c.readInteger(self.address + self.OFFSET.DATA)

    def readEncoderValue(self):
        return self.i2c.readLongSigned(self.address + self.OFFSET.ENCODER_VALUE)

    def setEncoderTarget(self, target):
        data = map(lambda b: struct.unpack('B', b)[0], struct.pack('l', target))
        self.i2c.writeArray(self.address + self.OFFSET.ENCODER_TARGET, data)

    def setPID(self, p, i, d):
        def floatToByteFraction(n):
            f = Fraction(n).limit_denominator(255)
            try:
                return [ord(chr(f.numerator)), ord(chr(f.denominator))]
            except ValueError: # fallback
                if n > 255: n = 255
                return [int(n), 1]
        data = sum(map(floatToByteFraction, [p,i,d]), [])
        self.i2c.writeArray(self.REGISTER.PID, data)

    # only needed/used in mindsensorsUI, otherwise use the method in PiStorms_GRX will suffice
    @classmethod
    def getKeyPressCount(self):
        return self.I2C.A.readByte(self.REGISTER.GO_PRESS_COUNT)

    @classmethod
    def getKeyPressValue(self):
        x, y = self.getTouchscreenCoordinates()
        if x > 300 and y > 0:
            return [8, 16, 24, 40][(y-1)/(240/4)]
        else:
            return 0

    @classmethod
    def getTouchscreenCoordinates(self):
        sampleSize = 3
        tolerance = 3
        x = [0]*sampleSize
        y = [0]*sampleSize
        try:
            for i in range(sampleSize):
                x[i] = self.I2C.A.readInteger(self.REGISTER.TOUCHSCREEN_X)
                y[i] = self.I2C.A.readInteger(self.REGISTER.TOUCHSCREEN_Y)
        except:
            print "Failed to read touchscreen"
            return (0, 0)
        if (numpy.std(x) < tolerance and numpy.std(y) < tolerance):
            return (int(numpy.mean(x)), int(numpy.mean(y)))
        else:
            return (0, 0)

class TYPE_SUPPORT:
    ALL = [GRXCom.TYPE.NONE, GRXCom.TYPE.DIGITAL_OUTPUT, GRXCom.TYPE.DIGITAL_INPUT, GRXCom.TYPE.I2C]
    ANALOG = ALL + [GRXCom.TYPE.ANALOG_INPUT]
    DIGITAL = ALL + [GRXCom.TYPE.ENCODER]
    # note: SERIAL is only supported on A1 and A2
GRXCom.TYPE_SUPPORT = TYPE_SUPPORT
del TYPE_SUPPORT

