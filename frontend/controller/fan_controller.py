from threading import Thread
import logging
from gpiozero import CPUTemperature
import time
import Entomoscope.globals as globals
import Entomoscope.backend.configuration as configuration
from Entomoscope.backend.devices.fan import Fan
from Entomoscope.backend.devices.temperature_sensor import TemperaureSensor


class FanController(Thread):
    def __init__(self):
        super(FanController, self).__init__()
        self.cooling_fan = Fan(configuration.FAN_PIN)
        self.temp_sensor = TemperaureSensor()
        self.cpu = CPUTemperature()
        self.interrupted = False
        self.timestamp_fan_on = None

    def run(self):
        while not self.interrupted:
            temp = self.temp_sensor.get_temp()
            cpu_temp = self.cpu.temperature
            if cpu_temp >= 75 or temp >= 45:
                if self.timestamp_fan_on is None:
                    self.timestamp_fan_on = time.time()
                self.cooling_fan.fan_at_speed(60)
                #self.cooling_fan.fan_on()
            else:
                if self.timestamp_fan_on is not None and abs(time.time()-self.timestamp_fan_on) >= globals.MIN_RUNTIME_FOR_FAN_IN_SEC:
                    self.cooling_fan.fan_at_speed(0)
                    self.timestamp_fan_on = None
        logging.info('Stopping Fan Controller. Fan now at Speed 0.')
        self.cooling_fan.fan_off()

    def interrupt(self):
        self.interrupted = True
