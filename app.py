  #!/usr/bin/env python
#import the flask libraries required
from flask import Flask, render_template, session, request
#import the flask_socketio libraries required
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import pigpio # import the harware timed gpio library
import time   # time library
import atexit # cleanup library
import rotary_encoder # import the library for handling the rotary encoder
import PID # library for handling the PID control
from threading import Thread  # library to run the app in two different threads
import json

#Constant variables
encA = 20       #pin a of the encoder
encB = 21       #pin b of the encoder
encRes = 128    #number of pulses per revolution

L298N_ENA = 24  #PWM control pin on the L298N
L298N_IN1 = 23  #L298N Input 1
L298N_IN2 = 22  #L298N Input 2

max_speed = 350  #maximum speed for the motor

enc_speed = 0    #current speed reading


# Class to create a new thread to work the PID control
class PIDControlWorker(Thread):

    def __init__(self):         #initialize the worker thread
        Thread.__init__(self)
        self.speed = 100        #set the initial conditions of the variables
        self.encoderSpeed = 0   #""
        self.direction = -1     #""
        self.Kp = 1.0           #""
        self.Ki = 0.25          #""
        self.Kd = 0.5           #""
        self.isEnabled = 0      #""
        self.gpio = pigpio.pi() #create new instance of the gpio clibrary

        #create new instance of the encoder class library
        self.encoder = rotary_encoder.decoder(self.gpio, encA, encB, encRes)

        #create new instance of the PID control class library
        self.PID = PID.PID()

        #set the gpio output pins for mor motor control
        self.gpio.set_mode(L298N_ENA, pigpio.OUTPUT)
        self.gpio.set_mode(L298N_IN1, pigpio.OUTPUT)
        self.gpio.set_mode(L298N_IN2, pigpio.OUTPUT)
        self.gpio.set_PWM_frequency(L298N_ENA, 60)


        self.daemon = True
        self.start()

    def run(self):      #when the class is run
        self.resume()   #set the initial conditions of the motor control
        while True:     #infinite loop to run the PID contol loop
            try:
                #set the output parameter based on the current readings
                #and set point
                self.setOutput()
                time.sleep(0.1) # wait 1/10th second
                pass
            except Exception as e:
                self.kill()  # on error shut down tidly
                raise e

    def setDirection(self, direction): #1 for forward and 0 for reverse
        #set the current direction to the new direction
        self.direction = direction
        if not direction:
            #if backward set the L298N inputs accordingly
            self.gpio.write(L298N_IN2,1)
            self.gpio.write(L298N_IN1,0)
        else:
            #if forward set the L298N inputs accordingly
            self.gpio.write(L298N_IN1,1)
            self.gpio.write(L298N_IN2,0)


    #Set the speed of the PID control loop
    def setSpeed(self, speed):
        #if the new set speed is greater than the max speed set
        #the speed to equal the max speed
        if abs(speed > max_speed):
            speed = max_speed
        #set the speed to the new speed
        self.speed = speed
        #set the set point in the PID class to the desired speed
        self.PID.setPoint(self.speed)

    #set the proportional gain
    def setKp(self, Kp):
        self.Kp = Kp
        self.PID.setKp(Kp)

    #set the integral gain
    def setKi(self, Ki):
        self.Ki = Ki
        self.PID.setKi(Ki)

    #set the differential gain
    def setKd(self, Kd):
        self.Kd = Kd
        self.PID.setKd(Kd)

    #kill the motor outputs
    def kill(self):
        self.PID.setPoint(0)
        self.gpio.write(L298N_IN1,0)
        self.gpio.write(L298N_IN2,0)
        self.gpio.set_PWM_dutycycle(L298N_ENA,0)

    #restart the motor by setting the direction and speed
    def resume(self):
        self.setDirection(self.direction)
        self.PID.setPoint(self.speed)

    #if enabled than run otherwise kill the output
    def setEnabled(self, en):
        self.isEnabled = en
        if not en:
            self.kill()
        else:
            self.resume()

    #set the outputs to get the motor to the desired setpoint
    def setOutput(self):
        #get the current speed
        self.encoderSpeed = self.encoder.speed()
        #if enabled
        if self.isEnabled:
            #get the output of the PID algorithm
            pid_out = self.PID.update(self.encoderSpeed)

            #if the output is negative start the motor in reverse
            #otherwise set the direction to forward
            if pid_out < 0:
                self.setDirection(0)
            else:
                self.setDirection(1)

            #get the pwm setting
            PWM = abs(pid_out)
            if PWM > 255:
              PWM = 255
            #set the pwm duty cycle
            self.gpio.set_PWM_dutycycle(L298N_ENA, PWM)


    def pidState(self):
        return "Set speed = {} measured speed = {} direction = {} Kp = {} Ki = {} Kd = {} enabled = {}".format(self.speed,self.encoderSpeed,self.direction,self.Kp,self.Ki,self.Kd,self.isEnabled)

    def pushLatest(self):
        return self.encoderSpeed

#setup the web server
async_mode = None

app = Flask(__name__)       #create a nen instance of the server
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)  #create new instance of socketio
thread = None
pidThread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    atexit.register(pidThread.kill)
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': pidThread.pidState(), 'count': count},
                      namespace='/motorControl')


#when the webserver is contacted it serves index.html
@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

#when the socket recieves the 'json_request'
@socketio.on('json_request', namespace='/motorControl')
def sendJSON():
    emit('send_JSON', {'Time': time.time(), 'Speed': pidThread.pushLatest()})

#when the speed on the webpage is changed set the speed
@socketio.on('speed_event', namespace='/motorControl')
def speed_message(message): #send back the response and set the speed
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': message['data'], 'count': session['receive_count']})
    pidThread.setSpeed(int(message['data']))

#when the direction is changed on the webpage set the direction accordingly
@socketio.on('direction_event', namespace='/motorControl')
def direction_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
        {'data': message['data'], 'count': session['receive_count']})
    pidThread.setDirection(int(message['data']))

#when the proportional gain is changed on the webpage set the proportional gain accordingly
@socketio.on('Kp_event', namespace='/motorControl')
def Kp_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
        {'data': message['data'], 'count': session['receive_count']})
    pidThread.setKp(float(message['data']))

#when the integral gain is changed on the webpage set the integral gain accordingly
@socketio.on('Ki_event', namespace='/motorControl')
def Ki_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
    pidThread.setKi(float(message['data']))

#when the differential gain is changed on the webpage set the differential gain accordingly
@socketio.on('Kd_event', namespace='/motorControl')
def Kd_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
    pidThread.setKd(float(message['data']))

#when the enabled field is changed on the webpage set the enabled flag accordingly
@socketio.on('enable_event', namespace='/motorControl')
def speed_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
    pidThread.setEnabled(int(message['data']))


@socketio.on('my_ping', namespace='/motorControl')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/motorControl')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/motorControl')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    pidThread = PIDControlWorker()

    socketio.run(app, host='0.0.0.0', port=80, debug=True)
