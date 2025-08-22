from curses import raw
from fnmatch import fnmatch, filter
import os
import time
import logging
from pathlib import Path
from glob import glob
from sys import path
import time
import numpy as np
import datetime
import re
from turtle import down
import shutil
from Entomoscope.backend.components.axis import Axis
from Entomoscope.backend.devices.fan import Fan
from Entomoscope.backend.devices.motor import Motor
from Entomoscope.backend.devices.switch import Switch
from Entomoscope.backend.devices.temperature_sensor import TemperaureSensor
from Entomoscope.frontend.controller.stacker import Stacker
from Entomoscope.frontend.focus_widget import FocusWidget

from Entomoscope.frontend.controller.usb_device_watcher import UsbDrivesWatcher
from Entomoscope.frontend.image_camera import ImageCamera
from Entomoscope.frontend.video_widget import VideoWidget
from Entomoscope.utils.get_free_space import get_free_space_in_gb
from Entomoscope.utils.validate_datetime import is_date_valid
from Entomoscope.utils.is_int import is_int
logging.basicConfig(level=logging.INFO)
from PyQt5 import uic
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QPushButton, QCheckBox, QPlainTextEdit, QLabel, QMainWindow, QApplication, QStyledItemDelegate, QFileDialog, QListWidget, \
    QListWidgetItem, QTreeView, QScroller, QSplashScreen, QFileDialog, QScrollArea, QSizePolicy, qApp, QGridLayout, QSpacerItem
from PyQt5.QtGui import QPalette, QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QWidget
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from time import sleep
import onnxruntime
import cv2

import Entomoscope.backend.configuration as configuration
from Entomoscope.backend.devices.light import Light
import Entomoscope.globals as globals


class StyledItemDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.text = option.fontMetrics.elidedText(
            index.data(), QtCore.Qt.ElideRight, globals.ICON_SIZE
        )

class QImageViewer(QWidget):

    """Class which enables to show taken images in fullscreen-mode"""
    def __init__(self, img_path):
        super().__init__()

        # create QLabel which contains the Pixmap (image)
        self.imageLabel = QLabel()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setPixmap(QPixmap(img_path[0]))
        self.scaleFactor = 1.0

        # create QScrollArea which allows to move the image from left to right and vice versa
        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea.setMinimumHeight(1100)
        self.scrollArea.setMinimumWidth(1900)
        self.scrollArea.setVisible(False)
        QScroller.grabGesture(self.scrollArea.viewport(), QScroller.LeftMouseButtonGesture)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # create a QGridLayout which contains all the QWidgets and arranges them
        grid = QGridLayout(self)

        self.zoomInButton = QPushButton()
        self.zoomInButton.setText('+')
        self.zoomInButton.setFont(QFont('Noto Sans Sinhala', 40, QFont.Bold))
        self.zoomInButton.setMinimumHeight(75)
        self.zoomInButton.setMinimumWidth(75)
        self.zoomInButton.clicked.connect(self.zoomIn)

        self.zoomOutButton = QPushButton()
        self.zoomOutButton.setText('-')
        self.zoomOutButton.setFont(QFont('Noto Sans Sinhala', 40, QFont.Bold))
        self.zoomOutButton.setMinimumHeight(75)
        self.zoomOutButton.setMinimumWidth(75)
        self.zoomOutButton.clicked.connect(self.zoomOut)

        # create a possibility to show the taken image in its original size (4065x3040 px)
        self.normalSizeButton = QPushButton()
        self.normalSizeButton.setText('Normal Size')
        self.normalSizeButton.setFont(QFont('Noto Sans Sinhala', 20))
        self.normalSizeButton.setMinimumHeight(75)
        self.normalSizeButton.setMinimumWidth(75)
        self.normalSizeButton.clicked.connect(self.normalSize)

        # create QPushButton which allows the user to return to the QMainWindow (Viewer Tab)
        self.exitButton = QPushButton()
        self.exitButton.setText('Exit Fullscreen')
        self.exitButton.setFont(QFont('Noto Sans Sinhala', 20))
        self.exitButton.setMinimumHeight(75)
        self.exitButton.setMinimumWidth(75)
        self.exitButton.clicked.connect(self.close)

        # Alignment of widgets/items within the grid layout
        self.verticalSpacer = QSpacerItem(10,1)
        grid.addWidget(self.scrollArea, 0, 0, 1, 5, QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        grid.addItem(self.verticalSpacer, 1, 0, QtCore.Qt.AlignCenter  | QtCore.Qt.AlignBottom)
        grid.addWidget(self.zoomInButton, 1, 1, QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        grid.addWidget(self.normalSizeButton, 1, 2, QtCore.Qt.AlignCenter  | QtCore.Qt.AlignBottom)
        grid.addWidget(self.zoomOutButton, 1, 3, QtCore.Qt.AlignLeft  | QtCore.Qt.AlignBottom)
        grid.addWidget(self.exitButton, 1, 4, QtCore.Qt.AlignRight  | QtCore.Qt.AlignBottom)

        self.setWindowTitle('Image Viewer')
        self.setGeometry(QtCore.QRect(0, 0, 1800, 1080))

        self.scrollArea.setVisible(True)

    def zoomIn(self):
        """Zoom in function, rescales image"""
        self.scaleImage(1.25)
        self.scaleFactor < 3.0

    def zoomOut(self):
        """Zoom out function, rescales image"""
        self.scaleImage(0.8)
        self.scaleFactor > 0.333

    def normalSize(self):
        """Function which rescales the image to its original size (4065x3040 px)"""
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def scaleImage(self, factor):
        """Function which resizes the image with a given factor and adjusts the scrollbars likewise"""
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

    def adjustScrollBar(self, scrollBar, factor):
        """Function which adjusts the scrollbars fitting to the choosen scale factor"""
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))

class ClickableLabel(QLabel):
    """Class whose parent class is QLabel. It extends QLabel class with the clicked-signal-event."""
    clicked = pyqtSignal()

    def __init__(self, parent):
        super(ClickableLabel, self).__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class Ui(QMainWindow):
    INDEX_TO_CLASS_PRED = [
    'Hymenoptera_Ichneumonidae',
    'Diptera_Psychodidae',
    'Diptera_Dolichopodidae',
    'Diptera_Sciaridae',
    'Diptera_Chironomidae',
    'Diptera_Phoridae',
    'Diptera_Calyptrate',
    'Diptera_Acalyptrate',
    'Hymenoptera_Braconidae',
    'Hemiptera_Cicadellidae',
    'Diptera_Cecidomyiidae',
    'Hymenoptera_Diapriidae',
    'Diptera_Empididae_&_Hybotidae',
    'Diptera_Mycetophilidae_&_Keroplatidae'
    ]
    

    def toggleFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def __init__(
        self,
        ui_file:str,
        num_of_stacks_default:int = 5,
        stack_step_size_default:int = 500
    ):
        super(Ui, self).__init__()
        uic.loadUi(ui_file, self)

        self.num_of_stacks_default = num_of_stacks_default
        self.stack_step_size_default = stack_step_size_default
        self.focus_out = self.findChild(QPushButton,'focus_in')
        self.focus_in = self.findChild(QPushButton,'focus_out')
        self.stepper_enabled = self.findChild(QCheckBox,'stepper_enabled_checkbox')
        self.stepper_enabled.setStyleSheet(globals.BIG_CHECKBOX_STYLE)
        self.autofocus = self.findChild(QPushButton,'autofocus_button')
        self.shutdown= self.findChild(QPushButton,'shutdown_button')
        self.classify = self.findChild(QPushButton,'classify_button')
        self.classification_result = self.findChild(QPlainTextEdit,'classification_result_text')

        self.light_enabled = self.findChild(QCheckBox,'light_enabled_checkbox')
        self.light_enabled.setStyleSheet(globals.BIG_CHECKBOX_STYLE)
        
        self.take_image = self.findChild(QPushButton,'take_image')
        self.take_stack = self.findChild(QPushButton,'take_stack')
        self.num_of_stacks_up = self.findChild(QPushButton,'num_stacks_up')
        self.num_of_stacks_down = self.findChild(QPushButton,'num_stacks_down')
        self.num_of_stacks = self.findChild(QLabel,'num_of_stacks')
        self.stack_step_size_up = self.findChild(QPushButton,'stack_step_size_up')
        self.stack_step_size_down = self.findChild(QPushButton,'stack_step_size_down')
        self.stack_step_size = self.findChild(QLabel,'stack_step_size')
        self.fuse_stacks = self.findChild(QCheckBox,'fuse_stacks')
        self.fuse_stacks.setStyleSheet(globals.BIG_CHECKBOX_STYLE)
        
        self.new_directory = self.findChild(QPushButton,'new_directory_button')
        self.new_insect = self.findChild(QPushButton,'new_insect_button')
        self.reduce_specimen = self.findChild(QPushButton,'reduce_specimen_button')
        self.increase_specimen = self.findChild(QPushButton, 'increase_specimen_button')
        self.browse_dir = self.findChild(QPushButton,'browse_dir')
        self.current_dir_text = self.findChild(QPlainTextEdit,'current_dir_text')
        self.current_specimen_text = self.findChild(QPlainTextEdit,'current_specimen_text')
        self.number_of_specimen_text = self.findChild(QLabel,'number_of_specimen_label')
        self.current_device_selection = self.findChild(QListWidget,'current_device_selection')
        self.status_text = self.findChild(QLabel,'status_text')
        
        self.insert_usb_text = self.findChild(QLabel,'insert_usb_text')
        self.insert_usb_icon = self.findChild(QLabel,'insert_usb_icon')

        self.explorer = self.findChild(QTreeView, 'explorer')
        self.gallery_stacked = self.findChild(QListWidget, 'gallery_stacked')
        self.bigimg = self.findChild(ClickableLabel, 'bigimg')
        self.splash = self.findChild(QSplashScreen, 'splash')
        self.gallery = self.findChild(QListWidget, 'gallery')
        self.img_name = self.findChild(QLabel, 'img_name')
        self.copy_local_to_usb_btn = self.findChild(QPushButton, 'copy_local_to_usb_btn')
        self.delete_local_drive_btn = self.findChild(QPushButton, 'delete_button')
        self.free_space_local = self.findChild(QLabel,'free_space_local')
        self.free_space_usb = self.findChild(QLabel,'free_space_usb')
        
        self.center_camera = self.findChild(VideoWidget,'center_camera')
        self.image_camera = ImageCamera()

        self.hw_light = Light(configuration.LIGHT_PIN)
        self.motor_stepper = Motor(
                    configuration.MS1_PIN,
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
        self.endstop_switch = Switch(configuration.AXES_STOP_SWITCH_PIN)
        self.linear_axis = Axis(
                    self.motor_stepper,
                        self.endstop_switch,
                        configuration.MIC_RESOLUTION,
                        configuration.STEPS_PER_REVOLUTION,
                        configuration.DISTANCE_PER_REVOLUTION,
                        configuration.AXIS_LENGTH,
                        configuration.BOTTOM_GAP,
                        configuration.TOP_GAP,
        )

        self.clickable_elements = [
            self.focus_in,
            self.focus_out,
            self.stepper_enabled,
            self.light_enabled,
            self.new_directory,
            self.browse_dir,
            self.take_image,
            self.take_stack,
            self.num_of_stacks_down,
            self.num_of_stacks_up,
            self.stack_step_size_up,
            self.stack_step_size_down,
            self.fuse_stacks,
            self.classify,
            self.increase_specimen,
            self.reduce_specimen,

        ]
        
        if None in [
            self.focus_in,
            self.focus_out,
            self.stepper_enabled,
            self.light_enabled,
            self.take_image,
            self.take_stack,
            self.num_of_stacks_up,
            self.num_of_stacks_down,
            self.num_of_stacks,
            self.stack_step_size_up,
            self.stack_step_size_down,
            self.stack_step_size,
            self.fuse_stacks,
            self.new_directory, 
            self.browse_dir,
            self.current_dir_text,
            self.current_specimen_text,
            self.current_device_selection,
            self.insert_usb_text, 
            self.insert_usb_icon,
            self.explorer,
            self.gallery_stacked,
            self.bigimg,
            self.gallery,
            self.img_name,
            self.copy_local_to_usb_btn,
            self.reduce_specimen,
            self.increase_specimen,
            self.shutdown
        ]:
            logging.error('Cant find all UI elements! Aborting')
            raise ValueError

        self.stacker = None

        # Create explorer-like QTreeView widget
        self.model = QFileSystemModel()
        dirPath = globals.LOCAL_DIR + '/' + globals.WORKING_DIR
        if self.is_blank(dirPath):
            QMainWindow.hide()
            print('Chosen file is empty')
        self.model.setRootPath(dirPath)
        self.explorer.setModel(self.model)
        self.explorer.setRootIndex(self.model.index(dirPath))
        self.explorer.setColumnWidth(0, 320)

        # Attach events to buttons
        self.focus_in.clicked.connect(self.focus_in_clicked)
        self.focus_out.clicked.connect(self.focus_out_clicked)
        self.autofocus.clicked.connect(self.autofocus_clicked)
        self.shutdown.clicked.connect(self.shutdown_clicked)
        self.classify.clicked.connect(self.classify_clicked)

        self.stepper_enabled.clicked.connect(self.stepper_enabled_clicked)
        self.light_enabled.clicked.connect(self.light_enabled_clicked)
        self.take_image.clicked.connect(self.take_image_clicked)
        self.take_stack.clicked.connect(self.take_stack_clicked)
        self.num_of_stacks_up.clicked.connect(self.num_of_stacks_up_clicked)
        self.num_of_stacks_down.clicked.connect(self.num_of_stacks_down_clicked)
        self.stack_step_size_up.clicked.connect(self.stack_step_size_up_clicked)
        self.stack_step_size_down.clicked.connect(self.stack_step_size_down_clicked)
        self.current_device_selection.selectionModel().selectionChanged.connect(self.selected_device_changed)
        self.fuse_stacks.clicked.connect(self.fuse_stacks_clicked)

        self.new_directory.clicked.connect(self.new_directory_clicked)
        self.new_insect.clicked.connect(self.new_insect_clicked)
        self.reduce_specimen.clicked.connect(self.reduce_specimen_clicked)
        self.increase_specimen.clicked.connect(self.increase_specimen_clicked)
        self.browse_dir.clicked.connect(self.browse_dir_clicked)

        self.bigimg.clicked.connect(self.img_fullscreen)

        self.explorer.clicked.connect(self.file_clicked)
        self.timer_loading_stacked = QtCore.QTimer(interval=50, timeout=self.load_image_stacked)
        self.timer_loading = QtCore.QTimer(interval=50, timeout=self.load_image)
        self.img_iterator_stacked = None
        self.img_iterator = None
        self.gallery_stacked.itemClicked.connect(self.update_img_stacked)
        self.gallery_stacked.itemClicked.connect(self.start_loading)
        self.gallery_stacked.itemClicked.connect(self.show_img_name_stacked)
        self.gallery.itemClicked.connect(self.update_img)
        self.gallery.itemClicked.connect(self.show_img_name)
        self.copy_local_to_usb_btn.clicked.connect(self.copy_image_folders_to_usb)
        self.delete_local_drive_btn.clicked.connect(self.delete_local_drive)

        # Enable easy touch-scrolling
        QScroller.grabGesture(self.gallery_stacked.viewport(), QScroller.LeftMouseButtonGesture)
        QScroller.grabGesture(self.gallery.viewport(), QScroller.LeftMouseButtonGesture)
        QScroller.grabGesture(self.explorer.viewport(), QScroller.LeftMouseButtonGesture)

        self.set_num_of_stacks_label(num_of_stacks_default)

        self.usb_drive_watcher = UsbDrivesWatcher(self.add_available_device, self.remove_available_device)

        self.img_name.setText('')
        self.free_space_usb.setText(f'')
        self.classification_result.clear()
        self.classification_result.insertPlainText('- classification result -')
        self.showFullScreen()
        self.show()

        # Invoke device changed to init selected device
        self.selected_device = None
        # root dir
        self.working_dir = None
        # dir in which images are saved
        self.current_target_dir = None
        self.current_specimen = None
        self.selected_device_changed(None,None)
        self.set_current_specimen(self.get_biggest_specimen_number())

        self.msg_box = None
        self.usb_plugged_in = False
        self.update_free_space_labels()

    @QtCore.pyqtSlot()
    def load_image_stacked(self):
        """Function which loads the stacked images found in the directory clicked in the explorer widget into the stacked gallery as items"""
        try:
            filename = next(self.img_iterator_stacked)
        except StopIteration:
            self.timer_loading_stacked.stop()
        else:
            name = os.path.basename(filename)
            item = QListWidgetItem(name)
            item.setIcon(QtGui.QIcon(filename))
            item.setSizeHint(QtCore.QSize(210,200))
            self.gallery_stacked.addItem(item)

    def load_image(self):
        """Function which loads the images fitting to the clicked stacked image in the stacked gallery into the allery as items"""
        try:
            filename = next(self.img_iterator)
        except StopIteration:
            self.timer_loading.stop()
        else:
            name = os.path.basename(filename)
            item = QListWidgetItem(name)
            item.setIcon(QtGui.QIcon(filename))
            self.gallery.addItem(item)

    def load_images_stacked(self):
        """Function which loads the stacked images in an item form with the image name in the stacked gallery"""
        if os.path.isdir(pathSelectedDirectory) and (not self.is_blank(pathSelectedDirectory)):
            self.show_message_box('Loading Images of Directory ...')
            foldersSelectedDirectory = glob(os.path.join(pathSelectedDirectory, globals.SPECIMENS_PREFIX + '*')) 

            for i in range(0, len(foldersSelectedDirectory)):
                if os.listdir(foldersSelectedDirectory[i]):

                    RAW_data_folder = glob(os.path.join(foldersSelectedDirectory[i], globals.RAW_DATA_DIR_NAME))
                    specimen_folders = os.listdir(RAW_data_folder[0])
                    count_specimen_folders = len(specimen_folders)
                    stacked_images_paths = glob(os.path.join(foldersSelectedDirectory[i],'Stacked_*'))
                    stacked_images_names = []
                    single_images_names = set()
                    
                    for img_path in stacked_images_paths:
                            stacked_images_names.append(re.sub('Stacked_', '', re.sub('.png', '', re.split('/', img_path)[7])))

                    if count_specimen_folders > len(stacked_images_paths):
                        for specimen in specimen_folders:
                            if specimen not in stacked_images_names:
                                single_images_names.add(specimen)
                        for single_image_name in single_images_names:
                            single_images_paths = os.path.join(RAW_data_folder[0], single_image_name)
                            item_stacked = QtCore.QDirIterator(single_images_paths, ['*000.png'], QtCore.QDir.Files, QtCore.QDirIterator.Subdirectories, ) 
                            while item_stacked.hasNext():
                                yield item_stacked.next()

                    if len(stacked_images_paths) == 1:
                        item_stacked = QtCore.QDirIterator(foldersSelectedDirectory[i], ['Stacked_*'], QtCore.QDir.Files, QtCore.QDirIterator.Subdirectories, )
                        while item_stacked.hasNext():
                            yield item_stacked.next()

                    else: 
                        for specimen in stacked_images_names:
                            item_stacked = QtCore.QDirIterator(foldersSelectedDirectory[i], ['Stacked_' + specimen + '.png'], QtCore.QDir.Files, QtCore.QDirIterator.Subdirectories, )
                            while item_stacked.hasNext():
                                yield item_stacked.next()

                else:
                    print('Chosen file does not contain any folders with images')
            self.hide_message_box()

        else:
            QMainWindow.hide()
            print('Folder is no directory')

    def load_images(self):
        """Function which loads the images in an item form with the image name in the gallery"""
        if os.path.isdir(pathSelectedDirectory) and (not self.is_blank(pathSelectedDirectory)):
            self.show_message_box('Loading Stacks ...')
            itemName = self.gallery_stacked.selectedItems()[0].text()
            if 'Stacked' in itemName:
                itemNumber = re.sub('.png','',(re.sub('Stacked_','', itemName))) 
                SpecimenNumber = re.split('_', itemNumber)[0] + '_' + re.split('_', itemNumber)[1]
                foldersSelectedDirectory = glob(os.path.join(pathSelectedDirectory, SpecimenNumber, globals.RAW_DATA_DIR_NAME, itemNumber))
                item = QtCore.QDirIterator(foldersSelectedDirectory[0], QtCore.QDir.Files, QtCore.QDirIterator.Subdirectories, )
                while item.hasNext(): 
                    filename = item.next()
                    yield filename
            else:
                itemNumber = re.split('_',re.sub('.png','',itemName))
                SpecimenNumber = itemNumber[0] + '_' + itemNumber[1]
                SpecimenFolder = SpecimenNumber + '_' + itemNumber[2]
                foldersSelectedDirectory = glob(os.path.join(pathSelectedDirectory, SpecimenNumber, globals.RAW_DATA_DIR_NAME, SpecimenFolder))
                item = QtCore.QDirIterator(foldersSelectedDirectory[0], QtCore.QDir.Files,
                                        QtCore.QDirIterator.Subdirectories, )
                while item.hasNext():
                    filename = item.next()
                    yield filename
            self.hide_message_box()
        else:
            QMainWindow.hide()
            print('Folder is no directory')

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F11:
            self.toggleFullScreen()

    def focus_in_clicked(self):
        logging.info('Focus in Clicked')
        try:
            self.linear_axis.move_down_for(globals.FOCUS_STEP_SIZE)
        except ValueError as e:
            print(e)

    def focus_out_clicked(self):
        logging.info('Focus out Clicked')
        try:
            self.linear_axis.move_up_for(globals.FOCUS_STEP_SIZE)
        except ValueError as e:
            print(e)

    def do_autofocus(self):
        step_size = globals.STEP_SIZE
        sharpness_threshold = 3
        max_tries = 10
        sharpnesses = []
        self.center_camera.pause_pipeline()
        time.sleep(2.0)
        focus_widget = FocusWidget()
        focus_widget.start_pipeline()
        try:
            self.linear_axis.move_to(0)
            while globals.SHARPNESS == -1:
                pass
            while self.linear_axis.highest_position() >= self.linear_axis.get_position():
                self.linear_axis.move_up_for(step_size)
                sharpnesses.append(globals.SHARPNESS)
                print(globals.SHARPNESS)
                if len(sharpnesses) > 5 and abs(sharpnesses[0] - sharpnesses[-1]) > sharpness_threshold and (sharpnesses[-1] < sharpnesses[-2]) and (sharpnesses[-1] < sharpnesses[-3]):
                    break
        except Exception as e:
            logging.error(e)
        focus_widget.pause_pipeline()
        time.sleep(2.0)
        try:
            self.center_camera.start_pipeline()
        except:
            self.center_camera.start_pipeline()
        num_steps = abs((len(sharpnesses)) - np.argmax(np.array(sharpnesses)) + 1)
        tries=0
        while tries < max_tries:
            try:
                self.linear_axis.move_down_for(num_steps*step_size)
                break
            except ValueError:
                num_steps-=1
        globals.SHARPNESS = -1

    def autofocus_clicked(self):
        logging.info('Autofocus Clicked')
        self.show_message_box('Autofocus ...')
        self.do_autofocus()
        self.hide_message_box()

    def stepper_enabled_clicked(self):
        logging.info('Stepper Enabled Clicked')
        if self.stepper_enabled.isChecked():
            logging.info('Stepper Enabled Checked')
            self.motor_stepper.enable()
            self.reference_axis()
            self.focus_in.setEnabled(True)
            self.focus_out.setEnabled(True)
            self.autofocus.setEnabled(True)
            self.take_stack.setEnabled(True)
            self.num_of_stacks_up.setEnabled(True)
            self.num_of_stacks_down.setEnabled(True)
            self.stack_step_size_up.setEnabled(True)
            self.stack_step_size_down.setEnabled(True)
        else:
            logging.info('Stepper Enabled Unchecked')
            self.motor_stepper.disable()
            self.focus_in.setEnabled(False)
            self.focus_out.setEnabled(False)
            self.autofocus.setEnabled(False)
            self.take_stack.setEnabled(False)
            self.num_of_stacks_up.setEnabled(False)
            self.num_of_stacks_down.setEnabled(False)
            self.stack_step_size_up.setEnabled(False)
            self.stack_step_size_down.setEnabled(False)

    def light_enabled_clicked(self):
        logging.info('Light Enabled Clicked')
        if self.light_enabled.isChecked():
            logging.info('Light Enabled Checked')
            self.hw_light.light_on()
        else:
            logging.info('Light Enabled Unchecked')
            self.hw_light.light_off()

    def shutdown_clicked(self):
        self.motor_stepper.disable()
        self.show_message_box('Shutting down now. Goodbye :)')
        time.sleep(1)

        os.system("sudo shutdown -h now")

    def create_new_dir_for_images(self):
        img_path = os.path.join(self.current_target_dir,self.current_specimen,globals.RAW_DATA_DIR_NAME)
        Path(img_path).mkdir(parents=True, exist_ok=True)
        dirs_for_specimen = next(os.walk(img_path))[1]
        if len(dirs_for_specimen) == 0:
            # if no dir exist make the first one
            img_number = f'{self.current_specimen}_000'
        else:
            biggest_number = sorted([int(x.split(f'{self.current_specimen}_')[1]) for x in next(os.walk(img_path))[1] if is_int(x.split(f'{self.current_specimen}_')[1])])[-1]
            img_number = f'{self.current_specimen}_{biggest_number + 1:03d}'
        Path(os.path.join(img_path,img_number)).mkdir(parents=True, exist_ok=True)
        return os.path.join(img_path,img_number), img_number

    def take_image_clicked(self):
        logging.info('Take image Clicked')
        self.show_message_box('Taking Image ...')
        save_dir, img_number = self.create_new_dir_for_images()
        self.center_camera.pause_pipeline()
        success = self.image_camera.take_image(os.path.join(save_dir,f'{img_number}_000.png'))
        self.center_camera.start_pipeline()
        self.update_free_space_labels()
        self.hide_message_box()

    def take_stack_clicked(self):
        logging.info('Take stack Clicked')
        self.show_message_box('Taking Stack ...')
        stack_step_size = int(self.stack_step_size.text())
        position_before_stacks = self.linear_axis.get_position()
        # move down slightly
        try:
            self.linear_axis.move_down_for(stack_step_size)
        except Exception as e:
            print(e)
        save_dir, img_number = self.create_new_dir_for_images()
        self.center_camera.pause_pipeline()
        for i in range(int(self.num_of_stacks.text())):
            success = self.image_camera.take_image(os.path.join(save_dir,f'{img_number}_{i:03d}.png')) 
            self.linear_axis.move_up_for(stack_step_size)
        self.center_camera.start_pipeline()
        self.linear_axis.move_to(position_before_stacks,True)
        self.update_free_space_labels()
        self.hide_message_box()

    def new_directory_clicked(self):
        logging.info('New Directory Clicked')
        directory = time.strftime(globals.DIRECTORY_NAMING_FORMAT)
        Path(os.path.join(self.working_dir,directory)).mkdir(parents=True, exist_ok=True)
        self.update_directory()
        self.set_current_specimen(self.get_biggest_specimen_number())

    def browse_dir_clicked(self):
        logging.info('Browse Dir Clicked')
        dialog = QFileDialog()
        selected_dir = dialog.getExistingDirectory(self, 'Select an directory to save the images',self.working_dir)
        if not is_date_valid(selected_dir.split('/')[-1],globals.DIRECTORY_NAMING_FORMAT):
            logging.error(f'Invalid directory selected: {selected_dir}. ignoring.')
        base_dir = selected_dir.replace(selected_dir.split('/')[-1],'')
        if self.working_dir[-1] != '/': # determine if working dir has trailing /
            if base_dir.lower()[:-1] != self.working_dir.lower():
                logging.error(f'Wrong directory. Dont do that! {selected_dir}')
                return 
        else:
            if base_dir.lower() != self.working_dir.lower():
                logging.error(f'Wrong directory. Dont do that! {selected_dir}')
                return
        self.set_current_directory(selected_dir)
        self.set_current_specimen(self.get_biggest_specimen_number())

    def new_insect_clicked(self):
        logging.info('New Insect Clicked')
        current_specimen = next(os.walk(self.current_target_dir))[1]
        
        if len(current_specimen) == 0:
            # No Specimen yet
            self.set_current_specimen(0)
            return
        # There exist specimen, new one should be old biggest number +1
        self.set_current_specimen(self.get_biggest_specimen_number()+1)
    
    def reduce_specimen_clicked(self):
        if int(self.current_specimen[-3:])-1 < 0:
            pass
        else:
            self.set_current_specimen(int(self.current_specimen[-3:])-1)

    def increase_specimen_clicked(self):
        if int(self.current_specimen[-3:])+1 > self.get_biggest_specimen_number():
            pass
        else:
            self.set_current_specimen(int(self.current_specimen[-3:])+1)


    def print_classification_result(self, result):
        self.classification_result.clear()
        time.sleep(0.5)
        self.classification_result.insertPlainText(result)

    def get_model_predictions(self, path_to_onnx, input_x):
        logging.info('Getting Model Predictions')
        ort_session = onnxruntime.InferenceSession(path_to_onnx, providers=["CPUExecutionProvider"])
        # compute ONNX Runtime output prediction
        ort_inputs = {ort_session.get_inputs()[0].name: input_x.astype(np.float32)}
        ort_outs = ort_session.run(None, ort_inputs)
        return ort_outs[0]

    def classify_clicked(self):
        logging.info('Classify image Clicked')
        self.show_message_box('Taking Image ...')
        save_dir, img_number = self.create_new_dir_for_images()
        self.center_camera.pause_pipeline()
        self.image_camera.take_image(os.path.join(save_dir,f'{img_number}_000.png'))
        time.sleep(2.5)
        self.hide_message_box()
        try:
            self.center_camera.start_pipeline()
        except:
            self.center_camera.start_pipeline()
        self.update_free_space_labels()
        self.show_message_box('Loading image to image processor ...')
        specimen_to_classify = cv2.imread('{0}/{1}_000.png'.format(save_dir, img_number))
        if specimen_to_classify is None:
            raise(Exception('Input image not found!'))
        specimen_to_classify = specimen_to_classify / 255
        specimen_to_classify = cv2.resize(specimen_to_classify,(512,512))
        specimen_to_classify = np.expand_dims(specimen_to_classify, 0)
        specimen_to_classify = np.transpose(specimen_to_classify,(0,3,1,2))
        self.hide_message_box()
        self.show_message_box('Starting outlier detection ...')
        y_outlier_prob = self.get_model_predictions('./entomoscope-software/Entomoscope/Models/model_outlier_detection.onnx', specimen_to_classify)
        self.hide_message_box()
        if y_outlier_prob[0] > 0.5:
            self.print_classification_result('other')
            print(f'Outlier Prob.: {y_outlier_prob[0]}')
            self.hide_message_box()
        else:
            self.show_message_box('Starting specimen classification ...')
            y_classifcation = self.get_model_predictions('./entomoscope-software/Entomoscope/Models/model.onnx', specimen_to_classify)
            class_str = self.INDEX_TO_CLASS_PRED[np.argmax(y_classifcation)]
            self.print_classification_result(class_str)
            print(f'Outlier Prob.: {y_outlier_prob[0]}, Predicted Numerical Class: {np.argmax(y_classifcation)} (Prob. {np.max(y_classifcation):.2f})')
            print(class_str)
            self.hide_message_box()
        

    def get_biggest_specimen_number(self):
        current_specimen = next(os.walk(self.current_target_dir))[1]
        if len(current_specimen) == 0:
            # if there is no specimen, simulate click to get one
            self.new_insect_clicked()
            current_specimen = next(os.walk(self.current_target_dir))[1]
        largest_specimen_number = sorted([int(x.split(globals.SPECIMENS_PREFIX)[1]) for x in current_specimen])[-1]
        return largest_specimen_number

    def num_of_stacks_up_clicked(self):
        logging.info('Num of stacks up clicked')
        self.increase_num_of_stacks()

    def num_of_stacks_down_clicked(self):
        logging.info('Num Stacks down clicked')
        self.decrease_num_of_stacks()

    def increase_num_of_stacks(self):
        try:
            current_num_of_stacks = int(self.num_of_stacks.text())
            self.set_num_of_stacks_label(f'{current_num_of_stacks+1}')
        except ValueError:
            logging.error(f'Invalid value in increase_num_of_stacks for num_of_stacks: {self.num_of_stacks.text()}')
            logging.error(f'Setting to default value ({self.num_of_stacks_default})')

    def decrease_num_of_stacks(self):
        try:
            current_num_of_stacks = int(self.num_of_stacks.text())
            self.set_num_of_stacks_label(f'{current_num_of_stacks-1}')
        except ValueError:
            logging.error(f'Invalid value in decrease_num_of_stacks for num_of_stacks: {self.num_of_stacks.text()}')
            logging.error(f'Setting to default value ({self.num_of_stacks_default})')

    def set_num_of_stacks_label(self,num_of_stacks):
        if int(num_of_stacks) >= globals.MIN_NUM_OF_STACKS and int(num_of_stacks) <= globals.MAX_NUM_OF_STACKS:
            self.num_of_stacks.setText(f'{num_of_stacks}')

    def stack_step_size_up_clicked(self):
        logging.info('Stack step size up clicked')
        self.increase_stack_step_size()

    def stack_step_size_down_clicked(self):
        logging.info('Stack step size down clicked')
        self.decrease_stack_step_size()

    def increase_stack_step_size(self):
        try:
            current_stack_step_size = int(self.stack_step_size.text())
            self.set_stack_step_size_label(f'{current_stack_step_size+25}')
            globals.FOCUS_STEP_SIZE = int(self.stack_step_size.text())
        except ValueError:
            logging.error(f'Invalid value in increase_stack_step_size for stack_step_size: {self.stack_step_size.text()}')
            logging.error(f'Setting to default value ({self.stack_step_size_default})')

    def decrease_stack_step_size(self):
        try:
            current_stack_step_size = int(self.stack_step_size.text())
            self.set_stack_step_size_label(f'{current_stack_step_size-25}')
            globals.FOCUS_STEP_SIZE = int(self.stack_step_size.text())
        except ValueError:
            logging.error(f'Invalid value in increase_stack_step_size for stack_step_size: {self.stack_step_size.text()}')
            logging.error(f'Setting to default value ({self.stack_step_size_default})')

    def set_stack_step_size_label(self,stack_step_size):
            if int(stack_step_size) >= globals.MIN_STACK_STEP_SIZE and int(stack_step_size) <= globals.MAX_STACK_STEP_SIZE: 
                self.stack_step_size.setText(f'{stack_step_size}')

    def update_directory(self):
        # create working dir if it is not existing
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)
        existing_directories = glob(os.path.join(self.working_dir,'*'))
        if len(existing_directories) == 0:
            # simulate new dir click
            self.new_directory_clicked()
            existing_directories = glob(os.path.join(self.working_dir,'*'))
        timestamps = []
        for dir in existing_directories:
            dir_name = dir.split('/')[-1]
            if is_date_valid(dir_name,globals.DIRECTORY_NAMING_FORMAT):
                timestamps.append(datetime.datetime.strptime(dir_name, globals.DIRECTORY_NAMING_FORMAT).timestamp())
            else:
                # Invalid dir is ignored (-1 is surley not the last timestamp)
                timestamps.append(-1)
        argmax = timestamps.index(max(timestamps))
        self.set_current_directory(existing_directories[argmax])
        self.set_current_specimen(self.get_biggest_specimen_number())

    def set_current_directory(self, directory):
        self.current_target_dir = directory
        self.current_dir_text.clear()
        self.current_dir_text.insertPlainText(directory.split('/')[-1])
        logging.info(f'New Directory for images: {self.current_target_dir}')
        global pathSelectedDirectory 
        pathSelectedDirectory = self.current_target_dir
        print('SET CURRENT DIRECTORY: ' + pathSelectedDirectory)

    def set_current_specimen(self, specimen_number):
        self.current_specimen = f'{globals.SPECIMENS_PREFIX}{specimen_number:03d}'
        Path(os.path.join(self.current_target_dir,self.current_specimen)).mkdir(parents=True, exist_ok=True)
        self.current_specimen_text.clear()
        self.current_specimen_text.insertPlainText(self.current_specimen.split(globals.SPECIMENS_PREFIX)[1])
        logging.info(f'New Specimen : {self.current_specimen}')

    def selected_device_changed(self,selected,deselcted):
        if len(self.current_device_selection.selectedItems()) > 1:
            logging.error('Multiple Source Devices selected. Invalid.')
            return
        if len(self.current_device_selection.selectedItems()) < 1:
            logging.error('No Source Devices selected. Invalid.') 
            return
        self.selected_device = self.current_device_selection.selectedItems()[0].text()
        if self.selected_device == 'Local Device':
            if os.path.exists(globals.LOCAL_DIR):
                if os.path.islink(globals.LOCAL_DIR):
                    os.unlink( globals.LOCAL_DIR)
                elif os.path.isdir( globals.LOCAL_DIR):
                    stream = os.popen(f'rm -rf {globals.LOCAL_DIR}')
                    output = stream.read()
                    logging.info(output)
                else:
                    os.remove( globals.LOCAL_DIR)
            os.symlink(globals.VOLUME_DIR, globals.LOCAL_DIR)
            self.selected_device = globals.LOCAL_DIR

        else:
            try:
                os.symlink(self.selected_device,globals.USB_DIR)
                self.selected_device = globals.USB_DIR
            except:
                self.selected_device = globals.USB_DIR
        logging.info(f'Selected Device: {self.selected_device}')
        # symlinkt to be sure filename will not be too long
        self.working_dir = os.path.join(self.selected_device,globals.WORKING_DIR)
        # Change RootPath of explorer
        self.model.setRootPath(self.working_dir)
        self.explorer.setModel(self.model)
        self.explorer.setRootIndex(self.model.index(self.working_dir))
        self.update_directory()
        self.update_usb_message()
        self.update_explorer()
        if self.stacker is not None:
            self.stacker.set_working_dir(self.working_dir)

    def add_available_device(self,new_device):
        self.current_device_selection.addItem(str(new_device))
        self.update_usb_message()
        self.update_free_space_labels()

    def remove_available_device(self,removed_device):
        for i in range(self.current_device_selection.count()):
            item = self.current_device_selection.item(i).text()
            if item == removed_device:
                self.current_device_selection.takeItem(i)
                self.update_usb_message()
                self.update_free_space_labels()
                return
        logging.error(f'Tried to remove non-existing item from available devices list {removed_device}')

    def update_usb_message(self):
        # If we only have one device and this device is the local drive, we want to show a message that saving the image
        # on the local storage is discouraged.
        if (self.current_device_selection.count() < 2 and self.current_device_selection.item(0).text() == 'Local Device'):
            self.insert_usb_text.setVisible(True)
            self.insert_usb_icon.setVisible(True)
            self.copy_local_to_usb_btn.setEnabled(False)
            self.usb_plugged_in = False
        elif (self.current_device_selection.count() == 2 and self.current_device_selection.selectedItems()[0].text() != 'Local Device'):
            self.insert_usb_text.setVisible(False)
            self.insert_usb_icon.setVisible(False)
            self.copy_local_to_usb_btn.setEnabled(True)
            self.usb_plugged_in = True
        else:
            self.insert_usb_text.setVisible(False)
            self.insert_usb_icon.setVisible(False)
            self.copy_local_to_usb_btn.setEnabled(False)
            self.usb_plugged_in = True


    def copy_image_folders_to_usb(self):
            self.show_message_box('Copying Images to USB ...')
            # If an USB stick is plugged in and the copy button is clicked, image folders will be copied from local device to USB memory.
            for file_name in os.listdir(os.path.join(globals.LOCAL_DIR, globals.WORKING_DIR)):
                source = os.path.join(globals.LOCAL_DIR, globals.WORKING_DIR, file_name)
                destination = os.path.join(globals.USB_DIR, globals.WORKING_DIR, file_name)
                shutil.copytree(source, destination, symlinks=True, dirs_exist_ok=True)
            self.hide_message_box()

    def update_free_space_labels(self):
        try:
            l_toal,l_used,l_free = get_free_space_in_gb(globals.LOCAL_DIR)
            self.free_space_local.setText(f'Local: {l_used}GB of {l_toal}GB Used')
        except Exception as e:
            logging.info(e)

    def delete_local_drive(self):
        logging.info('Delete Local Drive Clicked')
        msg = QMessageBox()
        msg.setWindowTitle("Delete Local Drive")
        msg.setText("This Action will delete all files on your local drive. Do you want to continue?")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        clicked_button = msg.exec_()
        if clicked_button == QMessageBox.Ok:
            self.show_message_box('Deleting Files ...')
            logging.info('Deleting eveything from local disk')
            for root, dirs, files in os.walk(os.path.realpath(globals.LOCAL_DIR)):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
            self.bigimg.clear()
            self.gallery.clear()
            self.gallery_stacked.clear()
            self.img_name.clear()
            self.selected_device_changed(None,None)
            self.update_free_space_labels()
            self.hide_message_box()

    def reference_axis(self):
        self.show_message_box('Referencing Axis ...')
        self.linear_axis.reference()
        self.hide_message_box()

    def file_clicked(self, clicked_file):
        """Function which identifies the path of the clicked directory in the explorer and starts the loading process of the images within the clicked directory"""
        # file from treeView (explorer) is chosen
        # Get path of file in order to load the images in gallery_stacked
        if self.model.isDir(clicked_file):
            global pathSelectedDirectory
            pathSelectedDirectory = self.model.filePath(clicked_file)
            if os.path.exists(pathSelectedDirectory) and (not self.is_blank(pathSelectedDirectory)):
                # check if chosen directory/folder contains files
                if not os.listdir(pathSelectedDirectory):
                    print('Chosen file is empty')
                else:
                    self.start_loading_stacked()
                    self.gallery.clear()
            else:
                QMainWindow.hide()
                print('Chosen file is no directory')

    def start_loading_stacked(self): 
        """Function which loads stacked images from clicked directory and stops timer for loading process"""
        if self.timer_loading_stacked.isActive():
            self.timer_loading_stacked.stop()
        self.img_iterator_stacked = self.load_images_stacked() 
        self.gallery_stacked.clear()
        self.timer_loading_stacked.start()

    def start_loading(self):
        """Function which loads images from clicked directory and stops timer for loading process"""
        if self.timer_loading.isActive():
            self.timer_loading.stop()
        self.img_iterator = self.load_images()
        self.gallery.clear()
        self.timer_loading.start()

    def update_img_stacked(self):
        """Function which updates the big image with clicked stacked image (item) in stacked gallery"""
        # Update big image with clicked image (item) in listWidget
        # Get selected directory path
        if os.path.isdir(pathSelectedDirectory) and (not self.is_blank(pathSelectedDirectory)):
            # Append item path
            itemName = self.gallery_stacked.selectedItems()[0].text()
            global itemPath
            if 'Stacked' in itemName:
                itemNumber = re.sub('.png','',(re.sub('Stacked_','', itemName)))
                SpecimenNumber = re.split('_', itemNumber)[0] + '_' + re.split('_', itemNumber)[1]
                itemPath = glob(os.path.join(pathSelectedDirectory, SpecimenNumber + '/' + itemName))
            else:
                itemNumber = re.split('_',re.sub('.png','',itemName))
                SpecimenNumber = itemNumber[0] + '_' + itemNumber[1]
                SpecimenFolder = SpecimenNumber + '_' + itemNumber[2]
                itemPath = glob(os.path.join(pathSelectedDirectory, SpecimenNumber, globals.RAW_DATA_DIR_NAME, SpecimenFolder, itemName))
            # Change pixmap in big image
            if os.path.isfile(itemPath[0]):
                pixmap = QtGui.QPixmap(itemPath[0])
                self.bigimg.setPixmap(pixmap)
            else:
                print('Item is not a file')

    def update_img(self):
        """Function which updates the big image with clicked image (item) in gallery"""
        # Update big image with clicked image (item) in listWidget
        # Get selected directory path
        if os.path.isdir(pathSelectedDirectory) and (not self.is_blank(pathSelectedDirectory)):
            # Append item path
            itemName = self.gallery.selectedItems()[0].text()
            itemNumber = re.split('_',re.sub('.png','',itemName))
            SpecimenNumber = itemNumber[0] + '_' + itemNumber[1]
            SpecimenFolder = SpecimenNumber + '_' + itemNumber[2]
            global itemPath
            itemPath = glob(os.path.join(pathSelectedDirectory, SpecimenNumber, globals.RAW_DATA_DIR_NAME, SpecimenFolder, itemName))

            # Change pixmap in big image
            if os.path.isfile(itemPath[0]):
                pixmap = QtGui.QPixmap(itemPath[0])
                self.bigimg.setPixmap(pixmap)
            else:
                print('Item is not a file')

    def is_blank(self, string):
        """Function that checks if a string is blank"""
        if string and string.strip():
            # string is not None AND string is not empty or blank
            return False
        # string is None OR string is empty or blank
        return True

    def show_message_box(self, text):
        self.msgBox = QMessageBox(parent=self)
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setText(f"<font size = 10 color = red ><b> {text} </b></font>")
        self.msgBox.setStandardButtons(QMessageBox.NoButton)
        self.msgBox.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | ~QtCore.Qt.WindowMinimizeButtonHint)
        self.msgBox.show()
        QApplication.processEvents()

    def hide_message_box(self):
        if self.msgBox == None:
            return
        self.msgBox.done(1)

    def img_fullscreen(self):
        """Function that triggers fullscreen-mode of taken image"""
        self.fullscreen_img = QImageViewer(itemPath)
        self.fullscreen_img.showFullScreen()

    def show_img_name_stacked(self):
        """Function that shows the name of the clicked stacked image in stacked gallery as a label in the GUI"""
        self.img_name.setText(self.gallery_stacked.selectedItems()[0].text())
    
    def show_img_name(self):
        """Function that shows the name of the clicked image in gallery as a label in the GUI"""
        self.img_name.setText(self.gallery.selectedItems()[0].text())

    def fuse_stacks_clicked(self):
        logging.info('Fuse Stacks Clicked')
        if self.fuse_stacks.isChecked():
            logging.info('Fuse Stacks Checked')
            self.stacker = Stacker(self.working_dir)
            self.stacker.start()
        else:
            logging.info('Fuse Stacks Unchecked')
            self.stacker.interrupt()
    
    def update_explorer(self):
        if self.current_device_selection.selectedItems()[0].text() != 'Local Device':
            dirPath = globals.USB_DIR + '/' + globals.WORKING_DIR
        else:
            dirPath = globals.LOCAL_DIR + '/' + globals.WORKING_DIR
        if self.is_blank(dirPath):
            QMainWindow.hide()
            print('Chosen file is empty')
        self.model.setRootPath(dirPath)
        self.explorer.setModel(self.model)
        self.explorer.setRootIndex(self.model.index(dirPath))
