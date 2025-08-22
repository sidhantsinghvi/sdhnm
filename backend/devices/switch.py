import RPi.GPIO as GPIO

class Switch():

    def __init__(self, switch_pin):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(switch_pin, GPIO.IN)
        self.switch_pin = switch_pin

    def get_status(self) -> bool:
        """Returns the status of the switch"""
        return (bool(GPIO.input(self.switch_pin)))
