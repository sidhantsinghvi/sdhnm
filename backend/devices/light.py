import RPi.GPIO as GPIO

class Light():
    __LIGHTSTATUS = False

    def __init__(self, light_pin):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(light_pin, GPIO.OUT)
        GPIO.output(light_pin, GPIO.LOW)
        self.light_pin = light_pin

    def light_status(self) -> bool:
        """Returns the status of the light: True - On, False - Off"""
        return self.__LIGHTSTATUS

    def light_on(self) -> None :
        """Switches on the light""" 
        GPIO.output(self.light_pin, GPIO.HIGH)
        self.__LIGHTSTATUS = True
    
    def light_off(self) -> None:
        """Switches off the light""" 
        GPIO.output(self.light_pin, GPIO.LOW)
        self.__LIGHTSTATUS = False
