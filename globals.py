
USB_MOUNT_DIRECTORY = "/media/entomoscope"
BIG_CHECKBOX_STYLE = "QCheckBox::indicator {width :80px;height : 80px;}"
CAMERA_NAME = "/base/soc/i2c0mux/i2c@1/imx477@1a"
ICON_SIZE = 100
MIN_NUM_OF_STACKS = 2
MAX_NUM_OF_STACKS = 10
MIN_STACK_STEP_SIZE = 0
MAX_STACK_STEP_SIZE = 1500
WORKING_DIR = 'Entomoscope_Images'
DIRECTORY_NAMING_FORMAT = "%Y-%m-%d-%H-%M-%S"
CURRENT_IMAGE = None
SPECIMENS_PREFIX = 'Specimen_'
NUMBER_OF_SPECIMEN_TEXT_SUFFIX = 'Specimen Images Taken in Current Directory'
RAW_DATA_DIR_NAME = 'RAW_Data'
SHARPNESS = -1
MIN_RUNTIME_FOR_FAN_IN_SEC = 30
VOLUME_DIR = '/mnt/ssd/'
LOCAL_DIR = '/home/entomoscope/l'
USB_DIR = '/home/entomoscope/u'



# Stacking

# Kernel Size for LaPlacian
# Type: int
# Unit: Pixels
KERNEL_SIZE = 5

# Kernel Size for Gaussian Filter
# Type: int
# Unit: Pixels
BLUR_SIZE = 5

# Parameter for Distance between Key Features
# Type: List[float]
# Unit: -
DISTANCE_VALUES = [0.4, 0.5, 0.6, 0.7]

# Threshold Value for RANSAC
# Type: float
# Unit: -
RANSAC_REPROJ_THRESHOLD_VALUE = 2.0

# Number of Matches
# Type: int
# Unit: -
NUMBER_MATCHES = 64

# Number of Stacks
# Type: int
# Unit: -
NUMBER_OF_STACKS = 5

# Standard Deviation for Gaussian Filter
# Type: int
# Unit: -
SIGMA_X = 0

# Highest Pixel Value
# Type: int
# Unit: Pixels
HIGHEST_PIXEL_VALUE = 255

# Offset for Images
# Type: int
# Units: Pixels
OFFSET = 50

IMAGE_WIDTH = 50
IMAGE_HEIGHT = 50

# Step size for autofocus
# Type: int
# Units: Steps
STEP_SIZE = 400

# Step size for stacks
# Type: int
# Units: Steps
STACK_STEP_SIZE = 500 #ggf. kleiner in 10er/25er Schritte

# Step size for moving the focus
# Type: int
# Units: Steps
FOCUS_STEP_SIZE = 125