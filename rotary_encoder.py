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

      decoder = rotary_encoder.decoder(pi, 7, 8, 128)

      time.sleep(300)

      decoder.cancel()

      pi.stop()

      """

      #set the values according to the constructor
      self.pi = pi
      self.gpioA = gpioA
      self.gpioB = gpioB

      #initially the encoder outputs are set to 0
      self.levA = 0
      self.levB = 0

      #set the resolution of the encoder (number of pulses per revolution)
      self.resolution = resolution

      #postion direction and time are used to determine the direction and speed
      self.prevPos = 0
      self.currPos = 0
      self.direction = 1
      self.timestamp = time.time()

      #last gpio is used to determine which channel was triggered last
      #this can be handy for debouncing mechanical encoders.
      self.lastGpio = None

      #set the GPIO as inputs
      self.pi.set_mode(gpioA, pigpio.INPUT)
      self.pi.set_mode(gpioB, pigpio.INPUT)

      #atthach the internal pullup resistors to the GPIO
      self.pi.set_pull_up_down(gpioA, pigpio.PUD_UP)
      self.pi.set_pull_up_down(gpioB, pigpio.PUD_UP)

      #here we set the interrupts on the input pins
      #when a pulse is detected the _pulse function is called
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

      #set the current level of the input that triggered the interrupt
      if gpio == self.gpioA:
         self.levA = level
      else:
         self.levB = level


      if gpio != self.lastGpio: # debounce
         self.lastGpio = gpio  #set the last gpio to call this function

         #if the gpio was A and it was a level 1
         if   gpio == self.gpioA and level == 1:
            if self.levB == 1:  # and if gpio b is also a 1
               self.callback( 1) # then we are going forward
               #send the direction to the callback function for analysis
         #if the gpio was B and it was a level 1
         elif gpio == self.gpioB and level == 1:
            if self.levA == 1: # and if gpio a is also a level 1
               self.callback( -1) #then we are going backwards
               #send the direction to the callback function for analysis

   def cancel(self):

      """
      Cancel the rotary encoder decoder.
      """
      #shut down the gpio
      self.cbA.cancel()
      self.cbB.cancel()

   def speed(self):
      """
      Measure the speed of the encoder
      """
      now = time.time() # get the current time
      elapsed = now-self.timestamp  #compare to the previous timestamp
      distance = self.currPos-self.prevPos  #calculate the distance traveled
      self.timestamp = now  # set the timestamp to the current time
      self.prevPos = self.currPos #set the previous position to the current position
      if elapsed:  #if elapsed is not 0... this way we do not divide by zero
         #revolutions = distance (pulse count) / resolution (pulses per revolution)
         #minutes = elapsed time (seconds) * (1 miunte / 60 seconds)
         #speed (RPM) = revolutions / minute
         return (float(distance) / float(self.resolution)) / (float(elapsed) / 60.0)
      else:
         return 0

   """
   Return the current position
   """
   def position(self):
      return self.currPos

   """
   Sets the current direction
   """
   def callback(self,way):
      #set the current direction
      self.currPos += way

      #if direction has changed
      #set the direction
      #and since a direction change means that the postion
      #reached or passed 0 we will reset the timestamp
      if self.direction != way:
         self.timestamp = time.time()
         self.direction = way

   #cleans up the variables on exit.
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
