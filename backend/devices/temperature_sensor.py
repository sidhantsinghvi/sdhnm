# coding=utf-8
# Benoetigte Module werden importiert und eingerichtet
import glob
import time
from time import sleep
import logging
import RPi.GPIO as GPIO
import subprocess

 
class TemperaureSensor():

    def __init__(self, temp_sensor_pin = 4):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(temp_sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        base_dir = '/sys/bus/w1/devices/'
        num_tries = 0
        device_folder = None
        while num_tries < 3:
            try:
                device_folder = glob.glob(base_dir + '28*')[0]
                break
            except IndexError:
                logging.info('Could not detect temperatur messing. Trying to initiate it.')
                subprocess.run(["sudo", "modprobe", "w1-gpio"])
                subprocess.run(["sudo", "modprobe", "w1-therm"])
                sleep(0.5)
                num_tries+=1
                continue
        if device_folder is None:
            logging.error('Could not init Fan control. Will be disabled. CAUTION !!')
            self.device_file = None
        else:
            self.device_file = device_folder + '/w1_slave'
 
    def measure_temp(self):
        if self.device_file is None:
            return None
        f = open(self.device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def get_temp(self):
        lines = self.measure_temp()
        if lines is None:
            # if there is temp module
            return 0
        while len(lines) == 0:
            lines = self.measure_temp()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.measure_temp()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
    
