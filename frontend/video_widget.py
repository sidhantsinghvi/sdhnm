
from PyQt5.QtWidgets import  QWidget, QLabel, QApplication
import gi
import logging
import Entomoscope.globals as globals

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GObject, GstVideo
GObject.threads_init()
Gst.init(None)

class VideoWidget(QWidget):   
    def __init__(self, parent):
        super(VideoWidget, self).__init__(parent)
        self.windowId = self.winId()
        self.setup_pipeline()
        self.start_pipeline()

    def setup_pipeline(self):           
        self.pipeline = Gst.Pipeline()
        self.pipeline = f'libcamerasrc camera-name="{globals.CAMERA_NAME}" ! videoscale ! videoflip method=counterclockwise ! glimagesink'
        self.pipeline = Gst.parse_launch(self.pipeline)
        bus =  self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.on_sync_message)

    def on_sync_message(self, bus, msg):
        message_name = msg.get_structure().get_name()
        if message_name == 'prepare-window-handle':
            win_id = self.windowId
            assert win_id
            imagesink = msg.src
            imagesink.set_window_handle(win_id)
            
    def start_pipeline(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        while self.pipeline.get_state(100).state != Gst.State.PLAYING:
            pass

    def pause_pipeline(self):
        self.pipeline.set_state(Gst.State.NULL)
        while self.pipeline.get_state(100).state != Gst.State.NULL:
            pass