from time import sleep
import Entomoscope.backend.configuration as configuration
from Entomoscope.backend.devices.fan import Fan
from Entomoscope.backend.devices.switch import Switch

from Entomoscope.backend.devices.motor import Motor
from Entomoscope.backend.components.axis import Axis


if True:
    cooling_fan = Fan(configuration.FAN_PIN)
    endstop_switch = Switch(configuration.AXES_STOP_SWITCH_PIN)

    stepper = Motor(configuration.MS1_PIN,
                    configuration.MS2_PIN,
                    configuration.SPREAD_PIN,
                    configuration.UART1_PIN,
                    configuration.UART2_PIN,
                    configuration.EN_PIN,
                    configuration.STEP_PIN,
                    configuration.DIRECTION_PIN,
                    configuration.MIC_RESOLUTION,
                    configuration.MOTOR_SPEED,
                    )
    linear_axis = Axis(stepper,
                    endstop_switch,
                    configuration.MIC_RESOLUTION,
                    configuration.STEPS_PER_REVOLUTION,
                    configuration.DISTANCE_PER_REVOLUTION,
                    configuration.AXIS_LENGTH,
                    configuration.BOTTOM_GAP,
                    configuration.TOP_GAP,
                    )


    cooling_fan.fan_off()
    cooling_fan.fan_on()


    stepper.enable()

    linear_axis.reference()
    print(linear_axis.highest_position())
    sleep(3)
    linear_axis.move_to(linear_axis.highest_position(), True)
    print(linear_axis.get_position())

    linear_axis.move_to(linear_axis.middle_position(), True)

    linear_axis.disable_axis()
