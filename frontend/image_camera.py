import subprocess
import logging
from os.path import exists, isfile
from os import remove
from subprocess import TimeoutExpired

IMAGE_TAKE_TIMEOUT_IN_SECS = 60

class ImageCamera():   
    def __init__(
        self,
        max_tries = 3,
        exposure_time = 3,
    ):
        self.exposure_time = exposure_time
        self.max_tries = max_tries

    
    def take_image(self, image_path):
        if exists(image_path) and not isfile(image_path): 
            logging.error(f'Tried to save image as directory. Aborting! ({image_path})')
            return False
        tries = 1 
        image_sucessfully_taken = False
        while tries <= self.max_tries and not image_sucessfully_taken:
            if exists(image_path):
                remove(image_path)
            try:
                result = subprocess.run(
                    ['libcamera-still','-n','-e','png','-t1', f'-o{image_path}'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=IMAGE_TAKE_TIMEOUT_IN_SECS
                )
                logging.debug(result.stdout.decode('utf-8'))
            except TimeoutExpired as e:
                output = e.output.decode('utf-8')
                logging.debug(output)
                if 'Device or resource busy' in output:
                    logging.error('Live camera stream is enabled: Needs to be disabled for image taking to be possible. DISABLE IT!')
                logging.error(f'Could not take image. Retrying (attempt {tries}/{self.max_tries})')
            if exists(image_path):
                image_sucessfully_taken = True
            tries+=1
        if exists(image_path):
            return True
        logging.error(f'Could not take image at path: {image_path} after {self.max_tries} tries.')
        return False

