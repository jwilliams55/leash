__version__ = '1.0.0'

CMD_NAME = 'leash'  # Lower case command and module name
APP_NAME = 'Leash'  # Application name in texts meant to be human readable
APP_URL = 'https://github.com/opulo-inc/'

import time

from .logger import Logger
from .serial import SerialManager

from .photon import Photon
from .camera import Camera
from .pump import Pump

"""Lumen object, containing all other subsystems
"""

class Lumen():

    def __init__(self, debug=True, topCam = False, botCam = False):

        self.log = Logger(debug)

        self.sm = SerialManager(self.log)
        self.photon = Photon(self.sm, self.log)

        self.leftPump = Pump("LEFT", self.sm, self.log)
        self.rightPump = Pump("RIGHT", self.sm, self.log)

        self.position = {
            "x": None, 
            "y": None,
            "z": None,
            "a": 0,
            "b": 0
        }

        if topCam is not False:
            self.topCam = Camera(topCam)

        if botCam is not False:
            self.botCam = Camera(botCam)


        self._bootCommands = [
            "G90",
            "M260 A112 B1 S1",
            "M260 A109",
            "M260 B48",
            "M260 B27",
            "M260 S1",
            "M260 A112 B2 S1",
            "M260 A109",
            "M260 B48",
            "M260 B27",
            "M260 S1",
            "G0 F50000",
            "M204 T4000",
            "G90"
        ]

        self._preHomeCommands = [
            "M204 T2000"
        ]

        self._postHomeCommands = [
            "M204 T4000"
        ]

        self.parkX = 220
        self.parkY = 400
        self.parkZ = 31.5


#####################
# Serial
#####################

    def connect(self):
        if self.sm.scanPorts():
            if self.sm.openSerial():
                self.sendBootCommands()
                return True
            
        return False
    
    def disconnect(self):
        self.sm._ser.close()
        if self.sm._ser.is_open:
            return False
        else:
            return True
        
    def finishMoves(self):
        self.sm.clearQueue()

    def sleep(self, seconds):
        self.finishMoves()
        time.sleep(seconds)

    def getHardwareID(self):
        #probe for all hardware pullup pins, plus chimera jumper
        # if any of these commands fail, it means is probably v3 or earlier
        # this also uses M115 to learn about the firmware
        pass
    
#####################
# Movement
#####################

    def goto(self, x=None, y=None, z=None, a=None, b=None):
        command = "G0"
        if x is not None:
            command = command + " X" + str(x)
            self.position["x"] = x
        if y is not None:
            command = command + " Y" + str(y)
            self.position["y"] = y
        if z is not None:
            command = command + " Z" + str(z)
            self.position["z"] = z
        if a is not None:
            command = command + " A" + str(a)
            self.position["a"] = a
        if b is not None:
            command = command + " B" + str(b)
            self.position["b"] = b

        print(command)
        self.sm.send(command)

    def setSpeed(self, f=None):
        if f is not None:
            command = "G0 F" + str(f)
            self.sm.send(command)
        
    def sendBootCommands(self):

        for i in self._bootCommands:
            if not self.sm.send(i):
               self.log.error("Halted sending boot commands because sending failed.")
               break


    def sendPreHomingCommands(self):

        for i in self._preHomeCommands:
            if not self.sm.send(i):
               self.log.error("Halted sending pre homing commands because sending failed.")
               break

    def idle(self):
        self.leftPump.off()
        self.rightPump.off()

        self.lightOff("TOP")
        self.lightOff("BOT")

        self.safeZ()

        self.goto(x=self.parkX, y=self.parkY)


    def home(self, x = True, y = True, z = True):

        self.log.info("Homing")

        self.sendPreHomingCommands()

        if x and y and z:
            self.sm.send("G28")
            self.position["x"] = 0
            self.position["y"] = 0
            self.position["z"] = 0

        else:
            if x or y or z:
                command = "G28"
                if x:
                    command = command + " X"
                if y:
                    command = command + " Y"
                if z:
                    command = command + " Z"

                self.sm.send(command)

        self.finishMoves()
        
        self.sendPostHomingCommands()

    def sendPostHomingCommands(self):

        for i in self._postHomeCommands:
            if not self.sm.send(i):
               self.log.error("Halted sending post homing commands because sending failed.")
               break
        
    def safeZ(self):
        self.goto(z=self.parkZ)


# LEDS

    def lightOff(self, index):
        s = 0 if index == "BOT" else 1

        self.sm.send(f"M150 P0 R0 U0 B0 S{s}")

    def lightOn(self, index, r=255, g=255, b=255, a=255):

        s = 0 if index == "BOT" else 1

        self.sm.send(f"M150 P{a} R{r} U{g} B{b} S{s}")

        print("turned on light yo")