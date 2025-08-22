import sys
from PyQt5.QtWidgets import QApplication
from Entomoscope.frontend.controller.fan_controller import FanController
from Entomoscope.frontend.ui import Ui
import os
import logging

stream = os.popen('rm -rf ~/l')
output = stream.read()
logging.info(output)
stream = os.popen('rm -rf ~/u')
output = stream.read()
logging.info(output)

fan_controller = FanController()
# fan_controller.start()

app = QApplication(sys.argv)
window = Ui('/home/entomoscope/entomoscope-software/Entomoscope/files/untitled.ui')
app.exec_()
