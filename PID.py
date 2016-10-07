#A simple implementation of a Discrete Proportional-Integral-Derivative (PID) controller. PID controller gives output value for error between desired reference input and measurement feedback to minimize error value.
#######	Example	#########
#
#p=PID(3.0,0.4,1.2)
#p.setPoint(5.0)
#while True:
#     pid = p.update(measurement_value)
#
#


class PID:
	"""
	Discrete PID control
	"""

	#Initialize the class
	def __init__(self, P=1.0, I=0.5, D=1.0, Derivator=0, Integrator=0, Integrator_max=500, Integrator_min=-500):

		#set the different paramaters based on the input of the contructor
		self.Kp=P
		self.Ki=I
		self.Kd=D
		self.Derivator=Derivator
		self.Integrator=Integrator
		self.Integrator_max=Integrator_max
		self.Integrator_min=Integrator_min

		#initially the set point and error are set to zero
		self.set_point=0.0
		self.error=0.0

	def update(self,current_value):
		"""
		Calculate PID output value for given reference input and feedback
		"""

		#Get the error
		self.error = self.set_point - current_value

		#determine the proportional component
		self.P_value = self.Kp * self.error

		#determine the derivative component
		self.D_value = self.Kd * ( self.error - self.Derivator)
		self.Derivator = self.error

		#determine the integral component
		self.Integrator = self.Integrator + self.error

		#since the integral can get very large very fast we have imposed limits
		if self.Integrator > self.Integrator_max:
			self.Integrator = self.Integrator_max
		elif self.Integrator < self.Integrator_min:
			self.Integrator = self.Integrator_min

		self.I_value = self.Integrator * self.Ki

		#summing up each component gives us our output value
		PID = self.P_value + self.I_value + self.D_value

		return PID

	def setPoint(self,set_point):
		"""
		Initilize the setpoint of PID
		"""
		self.set_point = set_point

	"""
	The following functions set the parameters individually whereas the
	constructor sets them all initially.
	"""
	def setIntegrator(self, Integrator):
		self.Integrator = Integrator

	def setDerivator(self, Derivator):
		self.Derivator = Derivator

	def setKp(self,P):
		self.Kp=P

	def setKi(self,I):
		self.Ki=I

	def setKd(self,D):
		self.Kd=D

	"""
	The following functions return the parameters of the control loop.
	"""
	def getPoint(self):
		return self.set_point

	def getError(self):
		return self.error

	def getIntegrator(self):
		return self.Integrator

	def getDerivator(self):
		return self.Derivator
