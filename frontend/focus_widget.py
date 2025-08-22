
from PyQt5.QtWidgets import  QWidget, QLabel, QApplication
import gi
import logging
import Entomoscope.globals as globals
import cv2

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GObject, GstVideo
from gstreamer import GstContext, GstPipeline, GstApp, Gst, GstVideo
import numpy as np
import gstreamer.utils as utils
GObject.threads_init()
Gst.init(None)


def extract_buffer(sample: Gst.Sample) -> np.ndarray:
    """Extracts Gst.Buffer from Gst.Sample and converts to np.ndarray"""
    buffer = sample.get_buffer()  # Gst.Buffer
    caps_format = sample.get_caps().get_structure(0)  # Gst.Structure
    video_format = GstVideo.VideoFormat.from_string(caps_format.get_value('format'))
    w, h = caps_format.get_value('width'), caps_format.get_value('height')
    c = 3
    dtype = utils.get_np_dtype(video_format)  # np.dtype
    format_info = GstVideo.VideoFormat.get_info(video_format)  # GstVideo.VideoFormatInfo
    array = utils.gst_buffer_to_ndarray(buffer, width=w, height=h, channels=c,dtype=dtype, bpp=format_info.bits, do_copy=True)
    return np.squeeze(array)  # remove single dimension if exists


def calc_focus(image):
	# compute the Laplacian of the image and then return the focus
	# measure, which is simply the variance of the Laplacian
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def on_buffer(sink: GstApp.AppSink, data) -> Gst.FlowReturn:
    """Callback on 'new-sample' signal"""

    sample = sink.emit("pull-sample")  # Gst.Sample

    if isinstance(sample, Gst.Sample):
        array = extract_buffer(sample)
        #array = cv2.resize(array,(512,512))
        globals.SHARPNESS = calc_focus(array)
        return Gst.FlowReturn.OK

    return Gst.FlowReturn.ERROR


class FocusWidget():   
    def __init__(self):
        self.setup_pipeline()

    def setup_pipeline(self):           
        self.pipeline = Gst.Pipeline()
        self.pipeline = f'libcamerasrc camera-name="{globals.CAMERA_NAME}"  ! resize ! appsink emit-signals=True'
        self.pipeline = Gst.parse_launch(self.pipeline)
        self.pipeline.children[0].connect("new-sample", on_buffer, None)
            
    def start_pipeline(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        while self.pipeline.get_state(100).state != Gst.State.PLAYING:
            pass

    def pause_pipeline(self):
        self.pipeline.set_state(Gst.State.NULL)
        while self.pipeline.get_state(100).state != Gst.State.NULL:
            pass