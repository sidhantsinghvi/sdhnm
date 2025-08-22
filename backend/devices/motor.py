# import RPi.GPIO as GPIO
# from time import sleep
from operator import truediv
import time
import pigpio
from Entomoscope.backend.components.axis import Axis

class Motor():

    __CLOCKWISE = 1
    __ANTI_CLOCKWISE = 0
    __DUTY_CYCLE = 1

    def __init__(self,
                ms1,
                ms2,
                spread,
                uart1,
                uart2,
                en,
                step,
                dir,
                microstep_resolution = 8,
                speed = 100,
                ) -> None:       

        #Calculates des delay in [us] from a given value in steps/s
        delay = int((0.5 * 10**6)/speed)

        pi = pigpio.pi()
        pi.set_mode(step, pigpio.OUTPUT)
        pi.set_mode(en, pigpio.OUTPUT)

        pi.wave_clear()

        pulse = []
        pulse.append(pigpio.pulse(1<<step, 0, delay))
        pulse.append(pigpio.pulse(0, 1<<step, delay))
        pi.wave_add_generic(pulse)
        wave = pi.wave_create()

        pi.set_mode(ms1, pigpio.OUTPUT) # MS1
        pi.set_mode(ms2, pigpio.OUTPUT) # MS2
        pi.set_mode(spread, pigpio.OUTPUT) # Spread
        pi.set_mode(uart1, pigpio.OUTPUT) # UART1
        pi.set_mode(uart2, pigpio.OUTPUT) # UART2
        pi.set_mode(en, pigpio.OUTPUT) # EN
        pi.set_mode(step, pigpio.OUTPUT) # Step
        pi.set_mode(dir, pigpio.OUTPUT) # Direction

        spread_setter = False #False (StealthChop --> works better for standstill)

        if microstep_resolution == 8:
            ms1_setter = False
            ms2_setter = False
        elif microstep_resolution == 16:
            ms1_setter = True
            ms2_setter = True
        elif microstep_resolution == 32:
            ms1_setter = True
            ms2_setter = False
        elif microstep_resolution == 64:
            ms1_setter = False
            ms2_setter = True
        else:
            raise ValueError ("Microstep resolution must be: 8, 16, 32 or 64")

        pi.write(ms1, ms1_setter)
        pi.write(ms2, ms2_setter)
        pi.write(spread, spread_setter)
        pi.write(uart1, 0)
        pi.write(uart2, 0)
        pi.write(en, 1)

        self.motor_status = False
        self.step = step
        self.dir = dir
        self.en = en
        self.speed = speed
        self.pi = pi
        self.wave = wave
        self.spread = spread


    def status(self) -> bool:
        #returns the status of the motor: True - enabled, False - disabled
        return self.motor_status

    def enable(self) -> None:
        self.pi.write(self.en, 0)
        self.motor_status = True

    def disable(self) -> None:
        self.pi.write(self.en, 1)
        self.motor_status = False

    def turn_right(self) -> None:
        # starts the motor turning right. Only stops when stop is called
        # program doesn't wait while moving
        self.pi.write(self.dir, self.__CLOCKWISE)
        self.pi.wave_send_repeat(self.wave)


    def turn_left(self) -> None:
        # starts the motor turning left. Only stops when stop is called
        # program doesn't wait while moving
        self.pi.write(self.dir, self.__ANTI_CLOCKWISE)
        self.pi.wave_send_repeat(self.wave)

    def turn_right_for(self, steps) -> None:
        # turns the motor right for the given number of steps
        self.pi.write(self.dir, self.__CLOCKWISE)

        max_steps_per_chain = 65_000

        number_of_chains = steps // max_steps_per_chain
        modulo = steps % max_steps_per_chain

        chain = []
        x = max_steps_per_chain & 255
        y = (max_steps_per_chain >> 8) #& 255
        for i in range(number_of_chains):
            chain += (255, 0, self.wave, 255, 1, x, y)

        x_1 = modulo & 255
        y_1 = (modulo >> 8) #& 255
        chain += (255, 0, self.wave, 255, 1, x_1, y_1)
        self.pi.wave_chain(chain)
        while self.pi.wave_tx_busy():
            time.sleep(0.1)

    def turn_left_for(self, steps) -> None:
        # turns the motor left for the given numer of steps
        self.pi.write(self.dir, self.__ANTI_CLOCKWISE)
        max_steps_per_chain = 65_000

        number_of_chains = steps // max_steps_per_chain
        modulo = steps % max_steps_per_chain

        chain = []
        x = max_steps_per_chain & 255
        y = (max_steps_per_chain >> 8) #& 255
        for i in range(number_of_chains):
            chain += (255, 0, self.wave, 255, 1, x, y)

        x_1 = modulo & 255
        y_1 = (modulo >> 8) #& 255
        chain += (255, 0, self.wave, 255, 1, x_1, y_1)
        self.pi.wave_chain(chain)
        while self.pi.wave_tx_busy():
            time.sleep(0.1)
    
    def change_speed(self, new_speed):
        delay = int((0.5 * 10**6)/new_speed)

        if new_speed == Axis._Axis__VELOCITY_MOVING_CALIBRATE_FAST:
            self.spread_setter = True #True (SpreadCycle) --> works better for higher speeds
        else:
            self.spread_setter = False #False (StealthChop) --> eliminates motor noise and is better at standstill

        self.pi.write(self.spread, self.spread_setter)

        pulse = []
        pulse.append(pigpio.pulse(1<<self.step, 0,       delay))
        pulse.append(pigpio.pulse(0,       1<<self.step, delay))
        self.pi.wave_add_generic(pulse)
        self.wave = self.pi.wave_create()
        
    def stop(self) -> None:
        # stops the motor when startet with turn_left or turn_right
        self.pi.wave_tx_stop()
        # self.pi.wave_delete(self.wave)
