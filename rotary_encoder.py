#!/usr/bin/env python

import pigpio
import atexit
import time

class decoder:

   """Class to decode mechanical rotary encoder pulses."""

   def __init__(self, pi, gpioA, gpioB, resolution):

      """
      Instantiate the class with the pi and gpios connected to
      rotary encoder contacts A and B.  The common contact
      should be connected to ground.  The callback is
      called when the rotary encoder is turned.  It takes
      one parameter which is +1 for clockwise and -1 for
      counterclockwise.

      EXAMPLE

      import time
      import pigpio

      import rotary_encoder

      pos = 0

      def callback(way):

         global pos

         pos += way

         print("pos={}".format(pos))

      pi = pigpio.pi()

      decoder = rotary_encoder.decoder(pi, 7, 8, callback)

      time.sleep(300)

      decoder.cancel()

      pi.stop()

      """

      self.pi = pi
      self.gpioA = gpioA
      self.gpioB = gpioB

      self.levA = 0
      self.levB = 0
      
      self.resolution = resolution
      
      self.prevPos = 0
      self.currPos = 0
      self.direction = 1
      self.timestamp = time.time()

      self.lastGpio = None

      self.pi.set_mode(gpioA, pigpio.INPUT)
      self.pi.set_mode(gpioB, pigpio.INPUT)

      self.pi.set_pull_up_down(gpioA, pigpio.PUD_UP)
      self.pi.set_pull_up_down(gpioB, pigpio.PUD_UP)

      self.cbA = self.pi.callback(gpioA, pigpio.EITHER_EDGE, self._pulse)
      self.cbB = self.pi.callback(gpioB, pigpio.EITHER_EDGE, self._pulse)

   def _pulse(self, gpio, level, tick):
      """
      Decode the rotary encoder pulse.

                   +---------+         +---------+      0
                   |         |         |         |
         A         |         |         |         |
                   |         |         |         |
         +---------+         +---------+         +----- 1

             +---------+         +---------+            0
             |         |         |         |
         B   |         |         |         |
             |         |         |         |
         ----+         +---------+         +---------+  1
      """

      if gpio == self.gpioA:
         self.levA = level
      else:
         self.levB = level;

      if gpio != self.lastGpio: # debounce
         self.lastGpio = gpio

         if   gpio == self.gpioA and level == 1:
            if self.levB == 1:
               self.callback( 1)
         elif gpio == self.gpioB and level == 1:
            if self.levA == 1:
               self.callback( -1)

   def cancel(self):

      """
      Cancel the rotary encoder decoder.
      """

      self.cbA.cancel()
      self.cbB.cancel()
      
   def speed(self):
      now = time.time()
      elapsed = now-self.timestamp
      distance = self.currPos-self.prevPos
      self.timestamp = now
      self.prevPos = self.currPos
      if elapsed:
         return (float(distance) / float(self.resolution)) / (float(elapsed) / 60.0)
      else:
         return 0
         
   def position(self):
      return self.currPos


   def callback(self,way):

      self.currPos += way
      
      if self.direction != way:
         self.timestamp = time.time()
         self.direction = way
         
   def cleanup(self):
      self.cancel()
      self.pi.stop()

"""
if __name__ == "__main__":

   import time
   import pigpio
   import RPi.GPIO as GPIO

   import rotary_encoder

   GPIO.setmode(GPIO.BOARD)
   GPIO.setup(12, GPIO.OUT)
   GPIO.setup(12, GPIO.OUT)
   GPIO.setup(12, GPIO.OUT)



   pi = pigpio.pi()

   decoder = rotary_encoder.decoder(pi, 20, 21)

   atexit.register(cleanup)

   while 1:

      now = time.time()
      
      elapsed = now - timestamp
      distance = pos - lastpos
      if elapsed:
          speed = (distance / 120) / (elapsed / 60)
      print ("Time elapsed = " + str(elapsed))
      print ("Distance = " + str(distance))
      print ("Speed = " + str(speed) + " RPM")


      timestamp = time.time()*1000.0
      lastpos = pos

      time.sleep(1)      
      
"""