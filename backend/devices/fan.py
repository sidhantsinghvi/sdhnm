import RPi.GPIO as GPIO

class Fan():
    __FANSTATUS = False

    def __init__(self, fan_pin, frequency = (25)):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(fan_pin, GPIO.OUT)
        GPIO.output(fan_pin, GPIO.LOW)
        _PWM = GPIO.PWM(fan_pin, frequency)
        self.PWM = _PWM
        
        self.fan_pin = fan_pin

    def fan_status(self) -> bool:
        """Returns the status of the fan: True - On, False - Off"""
        return self.__FANSTATUS

    def fan_on(self) -> None :
        """Switches on the fan""" 
        GPIO.output(self.fan_pin, GPIO.HIGH)
        self.__FANSTATUS = True
    
    def fan_off(self) -> None:
        """Switches off the fan""" 
        self.PWM.stop()
        GPIO.output(self.fan_pin, GPIO.LOW)
        self.__FANSTATUS = False
    
    def fan_at_speed(self, duty_cycle) -> None:
        """Switches the fan on at a given speed in percent"""
        if duty_cycle < 0 or duty_cycle > 100:
            raise ValueError('The speed for the fan must be in a range from 0 to 100')
        _PWM = self.PWM
        PWM_duty_cycle = duty_cycle
        _PWM.start(PWM_duty_cycle)
        self.__FANSTATUS = True
