from distutils.log import ERROR
from unittest.loader import VALID_MODULE_NAME
import RPi.GPIO as GPIO
from time import sleep
#import Entomoscope.backend.configuration as configuration

class Axis():

    # Unit: Steps per second
    __VELOCITY_MOVING_CALIBRATE_FAST = 18_500
    __VELOCITY_MOVING_CALIBRATE_SLOW = 2_000
    __CURRENT_POSITION_STEPS = 0
    __IS_REFERENCED = False

    def __init__(self,
    motor,
    switch,
    mic_step_res,
    steps_per_rev,
    distance_per_rev,
    size,
    gap_bottom,
    gap_top,
) -> None:
        """
        Constructs an axis with the given motor.

        The switch is used, for referencing.

        distance_per_rev is the ratio of distance that the axis moves per motor
        revolution. Unit: micrometer/rev

        The size gives the lenght of the axis. Unit: micrometer

        gap_bottom is the distance that is defined between the endstop switch
        and the moving object to avoid hitting the endstop when moving the axis.
        Unit: micrometer

        gap_top is the distance between the max length and the moving object.
        Unit: micrometer

        """
        mic_steps_per_rev = steps_per_rev * mic_step_res
        dist_per_mic_step = distance_per_rev / mic_steps_per_rev
        
        
        self.dist_per_mic_step = dist_per_mic_step
        self.motor = motor
        self.switch = switch
        self.size = size
        self.gap_bottom = gap_bottom
        self.gap_top = gap_top



    def reference(self) -> None:
        """ References the axis by moving to the endstop.
        Zero point is defined as the endstop position plus gap_bottom."""

        self.enable_axis()

        # moving velocity is increased to enable fast referencing.
        self.motor.change_speed(self.__VELOCITY_MOVING_CALIBRATE_FAST)
        self.motor.turn_left()
        while True:
            if self.switch.get_status():
                self.motor.stop()
                break
        # time needed to change the hardware generated PWM signal.
        sleep(0.5)
        # moving velocity is reduced to increase accuracy while moving up.
        self.motor.change_speed(self.__VELOCITY_MOVING_CALIBRATE_SLOW)
        self.motor.turn_right()
        while True:
            if not self.switch.get_status():
                self.motor.stop()
                break
        # Motor speed is reset to value definded in the configuration file.
        self.motor.change_speed(8_000) # TODO: CHANGE
        self.__CURRENT_POSITION_STEPS = 0
        self.motor.turn_right_for(int(self.gap_bottom / self.dist_per_mic_step))
        self.__IS_REFERENCED = True

    def move_up_for(self, distance, kind = False) -> None:
        """
        Moves the Axis up by a given distance
        kind defines the type that is used.
        False - micrometer (default)
        True - Microsteps

        Converts micrometers to microsteps, to define a absolute current position,
        using micrometers can lead to positions that are not reacheable due to
        the minimum resolution of the motor and linear axis combination.
        """
        if not self.__IS_REFERENCED:
            raise ERROR ("Axis can't be moved when not referenced!")
        if not kind:
            dist_step = self._micrometer_to_mic_steps(distance)
        else:
            dist_step = distance
        
        if self._in_range(dist_step, 'up'):
            self.motor.turn_right_for(dist_step)
            self._current_position(dist_step, 'up')

        
    def move_down_for(self, distance, kind = False) -> None:
        """
        Moves the Axis by a given distance
        kind defines the type that is used.
        False - micrometer (default)
        True - Microsteps

        Converts micrometers to microsteps, to define a absolute current position,
        using micrometers can lead to positions that are not reacheable due to
        the minimum resolution of the motor and linear axis combination.
        """
        if not self.__IS_REFERENCED:
            raise ERROR ("Axis can't be moved when not referenced!")
        if not kind:
            dist_step = self._micrometer_to_mic_steps(distance)
        else:
            dist_step = distance
        
        if self._in_range(dist_step, 'down'):
            self.motor.turn_left_for(dist_step)
            self._current_position(dist_step, 'down')
            print(self.__CURRENT_POSITION_STEPS)


    def move_to(self, position, kind= False):
        """
        Moves the Axis to a given position relative to the zeropoint.
        kind defines the type that is used.
        False - micrometer (default)
        True - Microsteps

        Converts micrometers to microsteps, to define a absolute current position,
        using micrometers can lead to positions that are not reacheable due to
        the minimum resolution of the motor and linear axis combination.
        """
        if not self.__IS_REFERENCED:
            raise ERROR ("Axis can't be moved when not referenced!")
        if not kind:
            pos_step = position / self.dist_per_mic_step
        else:
            pos_step = position
        if self._in_range(position, position = True):
            if pos_step > self.__CURRENT_POSITION_STEPS:
                steps_up = int(pos_step - self.__CURRENT_POSITION_STEPS)
                self.motor.turn_right_for(steps_up)
                self._current_position(steps_up, 'up')

            elif pos_step < self.__CURRENT_POSITION_STEPS:
                steps_down = self.__CURRENT_POSITION_STEPS - int(pos_step)
                self.motor.turn_left_for(steps_down)
                self._current_position(steps_down, 'down')




    def highest_position(self) -> int:
        return (round((self.size / self.dist_per_mic_step) -
        (self.gap_top/self.dist_per_mic_step)))
    
    def middle_position(self) -> int:
        return round(self.highest_position()/2)

    def get_position(self):
        return self.__CURRENT_POSITION_STEPS
    
    def is_referenced(self):
        return self.__IS_REFERENCED
    
    def disable_axis(self):
        self.motor.disable()
        self.__IS_REFERENCED = False
    
    def enable_axis(self):
        self.motor.enable

    def _current_position(self, value, direction) -> int:
        """Changes the value of the current position"""
        if direction != 'up' and direction != 'down':
            raise SyntaxError ("direction must be 'up' or 'down'")

        elif direction == 'down':
            self.__CURRENT_POSITION_STEPS = self.__CURRENT_POSITION_STEPS - value

        elif direction == 'up':
            self.__CURRENT_POSITION_STEPS = self.__CURRENT_POSITION_STEPS + value

    def _mic_steps_to_micrometer(self, mic_steps) -> float:
        """
        Converts microsteps in micrometer depending on th motor and axis.
        Converts results of the type float to int by rounding to the next full
        number.
        """
        return round(self.dist_per_mic_step * mic_steps)

    def _micrometer_to_mic_steps(self, micrometer) -> int:
        """
        Converts micrometer in microsteps depending on th motor and axis
        Converts results of the type float to int by rounding to the next full
        number.
        """
        return round(micrometer / self.dist_per_mic_step)

    def _in_range(self, value, direction = '', position = False) -> bool:
        if not position:
            if direction != 'up' and direction != 'down':
                raise SyntaxError ("direction must be 'up' or 'down'")
            elif direction == 'down' and self.__CURRENT_POSITION_STEPS - value < 0:
                    raise ValueError ("Value exceeds axis minimum position")
            elif direction == 'up' and self.__CURRENT_POSITION_STEPS + value > self.highest_position():
                    raise ValueError ("Value exceeds axis maximum position")
            else:
                return True
        elif position:
            if value < 0:
                raise ValueError ("The position of the axis can't be negaive")
            elif value > self.highest_position():
                raise ValueError ("Value exceeds axis maximum position")
            else:
                return True





