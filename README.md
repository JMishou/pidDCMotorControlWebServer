# pidDCMotorControlWebServer

Web app to serve a PID controlled motor

# dependancies

Flask - python web server library

Flask-SocketIO - extension for flask that implements web sockets

PIGPIO - Hardware timed gpio library

# Install dependancies

sudo apt-get update

sudo apt-get install pigpio python-pigpio python3-pigpio


sudo apt-get install python-pip

pip install flask

pip install flask-socketio

# Usage

start the pigpio daemon

sudo pigpiod

start the webserver

sudo python app.py
