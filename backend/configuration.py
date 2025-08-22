### Fan Setup ##################################################################

# Sets the GPIO pin for the fan
FAN_PIN = 18

### Temperture Sensor Setup ####################################################

# Sets the GPIO pin fpr the temperture sensor
TEMP_SENSOR_PIN = 4

### Light Setup ################################################################


LIGHT_PIN = 19

### Motor Setup ################################################################

# Sets the GPIO pin for MS1
MS1_PIN = 23

# Sets the GPIO pin for MS2
MS2_PIN = 24

# Sets the GPIO pin for Spread
SPREAD_PIN = 15

# Sets the GPIO pin for UART1
UART1_PIN = 14

# Sets the GPIO pin for UART2
UART2_PIN = 5

# Sets the GPIO pin for EN
EN_PIN = 22

# Sets the GPIO pin for Step
STEP_PIN = 13

# Sets the GPIO pin for Direction
DIRECTION_PIN = 6

# Sets the Microstepresolution: Steps per microstep (8, 16, 32, 64)
MIC_RESOLUTION = 16

# Sets the speed of the motor in steps per second
MOTOR_SPEED = 16_000

# The number of Fullsteps the motor takes to turn by 360°
STEPS_PER_REVOLUTION = 200

### Axis Setup #################################################################

# Distance per revolution ratio of the used axis in the unit of micrometer
DISTANCE_PER_REVOLUTION = 500

# Lenght of the used linear axis in the unito of micrometer
AXIS_LENGTH = 22_500

# Defines the gap in between the endstop switch and the defined zero position
# Usable length of the axis is reduced by this value
BOTTOM_GAP = 1_000

# Defines the gap in between the maximum top positon of the axis an the
# reacheable maximum position.
# Usable length of the axis is reduced by this value
TOP_GAP = 1_000

# Sets the GPIO pin for the first (axis) stop switch
AXES_STOP_SWITCH_PIN = 17

