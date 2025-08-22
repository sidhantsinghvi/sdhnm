from threading import Thread
import logging
from gpiozero import CPUTemperature
import time
from Entomoscope.frontend.controller.stacking import Stacking
import Entomoscope.globals as globals
import Entomoscope.backend.configuration as configuration
from Entomoscope.backend.devices.fan import Fan
from Entomoscope.backend.devices.temperature_sensor import TemperaureSensor
from glob import glob
import os
from pathlib import Path
import cv2
import shutil

class Stacker(Thread):
    def __init__(self,working_dir):
        super(Stacker, self).__init__()
        self.working_dir = working_dir
        self.interrupted = False
        self.stacking_algorithm = Stacking()

    def run(self):
        logging.info(f'Starting stacking')
        while not self.interrupted:
            candidates = []
            working_dir = glob(os.path.join(self.working_dir,'*'))
            for dirr in working_dir:
                foldersSelectedDirectory = glob(os.path.join(dirr, globals.SPECIMENS_PREFIX + '*'))
                for folder in foldersSelectedDirectory:
                    curr = [x[0] for x in os.walk(os.path.join(folder,globals.RAW_DATA_DIR_NAME))]
                    for cur in curr:
                        if not cur.split('/')[-1] == globals.RAW_DATA_DIR_NAME:
                            candidates.append([folder,cur])
            for candidate in candidates:
                if len(os.listdir(candidate[1])) > 1:
                    folder, stack_dir = candidate
                    stacked_img_name = f'{folder}/Stacked_{stack_dir.split("/")[-1]}.png'
                    if os.path.exists(stacked_img_name) and Path(stacked_img_name).is_file():
                        continue
                    # do stacking
                    if os.listdir(stack_dir):
                        image_names = os.listdir(stack_dir)
                        individual_image_paths = []
                        for i in range (0, len(image_names)):
                            individual_image_paths.append(os.path.join(stack_dir, image_names[i]))
                        individual_images = []
                        for image_path in individual_image_paths:
                            individual_images.append(cv2.imread(image_path))
                        if len(individual_images) > 1:
                            stacked_image = self.stacking_algorithm.do_stacking(individual_images)
                        else:
                            stacked_image = individual_images[0]
                        cv2.imwrite(stacked_img_name,stacked_image)
                        logging.info(f'Wrote stacked Image {stacked_img_name}')

        logging.info(f'Stopped stacking')

    def interrupt(self):
        self.interrupted = True

    def set_working_dir(self,working_dir):
        self.working_dir = working_dir