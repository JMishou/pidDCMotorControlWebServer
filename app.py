  #!/usr/bin/env python
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import pigpio
import time
import atexit
import rotary_encoder
import PID
from Queue import Queue
from threading import Thread
from collections import deque
import json

encA = 20
encB = 21
encRes = 120

L298N_ENA = 24
L298N_IN1 = 23
L298N_IN2 = 22

max_speed = 300

enc_speed = 0



class PIDControlWorker(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.speed = 100
        self.encoderSpeed = 0
        self.direction = -1
        self.Kp = 1.0
        self.Ki = 0.25
        self.Kd = 0.5
        self.isEnabled = 0
        self.gpio = pigpio.pi()
        self.encoder = rotary_encoder.decoder(self.gpio, encA, encB, encRes)
        self.PID = PID.PID()

        self.gpio.set_mode(L298N_ENA, pigpio.OUTPUT)
        self.gpio.set_mode(L298N_IN1, pigpio.OUTPUT)
        self.gpio.set_mode(L298N_IN2, pigpio.OUTPUT)
        self.gpio.set_PWM_frequency(L298N_ENA, 60)


        self.daemon = True
        self.start()

    def run(self):
        self.resume()
        while True:
            try:
                self.setOutput()
                time.sleep(0.1)
                pass
            except Exception as e:
                self.kill()
                raise e

    def setDirection(self, direction): #1 for forward and 0 for reverse
        self.direction = direction
        if not direction:
            self.gpio.write(L298N_IN2,1)
            self.gpio.write(L298N_IN1,0)
        else:
            self.gpio.write(L298N_IN1,1)
            self.gpio.write(L298N_IN2,0)

    def setSpeed(self, speed):
        if abs(speed > max_speed):
            speed = max_speed
        self.speed = speed
        self.PID.setPoint(self.speed)

    def setKp(self, Kp):
        self.Kp = Kp
        self.PID.setKp(Kp)

    def setKi(self, Ki):
        self.Ki = Ki
        self.PID.setKi(Ki)

    def setKd(self, Kd):
        self.Kd = Kd
        self.PID.setKd(Kd)

    def kill(self):
        self.PID.setPoint(0)
        self.gpio.write(L298N_IN1,0)
        self.gpio.write(L298N_IN2,0)
        self.gpio.set_PWM_dutycycle(L298N_ENA,0)

    def resume(self):
        self.setDirection(self.direction)
        self.PID.setPoint(self.speed)

    def setEnabled(self, en):
        self.isEnabled = en
        if not en:
            self.kill()
        else:
            self.resume()

    def setOutput(self):
        self.encoderSpeed = self.encoder.speed()
        if self.isEnabled:
            pid_out = self.PID.update(self.encoderSpeed)
            #print("encoder speed = {} pid output = {}".format(self.encoderSpeed, pid_out))
            if pid_out < 0:
                self.setDirection(0)
            else:
                self.setDirection(1)
            PWM = abs(pid_out)
            if PWM > 255:
              PWM = 255
            self.gpio.set_PWM_dutycycle(L298N_ENA, PWM)
        #self.speedJSON()

    def pidState(self):
        return "Set speed = {} measured speed = {} direction = {} Kp = {} Ki = {} Kd = {} enabled = {}".format(self.speed,self.encoderSpeed,self.direction,self.Kp,self.Ki,self.Kd,self.isEnabled)

    def pushLatest(self):
        return self.encoderSpeed


# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
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



@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@app.route('/d3.html')
def d3():
    return render_template('d3.html', async_mode=socketio.async_mode)

@socketio.on('json_request', namespace='/motorControl')
def sendJSON():
    emit('send_JSON', {'Time': time.time(), 'Speed': pidThread.pushLatest()})

@socketio.on('speed_event', namespace='/motorControl')
def speed_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': message['data'], 'count': session['receive_count']})
    pidThread.setSpeed(int(message['data']))

@socketio.on('direction_event', namespace='/motorControl')
def direction_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
        {'data': message['data'], 'count': session['receive_count']})
    pidThread.setDirection(int(message['data']))

@socketio.on('Kp_event', namespace='/motorControl')
def Kp_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
        {'data': message['data'], 'count': session['receive_count']})
    pidThread.setKp(float(message['data']))

@socketio.on('Ki_event', namespace='/motorControl')
def Ki_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
    pidThread.setKi(float(message['data']))

@socketio.on('Kd_event', namespace='/motorControl')
def Kd_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
    pidThread.setKd(float(message['data']))

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
