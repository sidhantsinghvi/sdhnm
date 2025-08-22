from glob import glob
import logging
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import Entomoscope.globals as globals



# This tutorial must be followed for this to work.
# https://andreafortuna.org/2019/06/26/automount-usb-devices-on-linux-using-udev-and-systemd/
class UsbDrivesWatcher:

    def __init__(self, new_device_callback:Callable, removed_device_callback:Callable):
        self.observer = Observer()
        self.new_device_callback = new_device_callback
        self.removed_device_callable = removed_device_callback

        # add already connected devices to selection
        for x in glob(f'{globals.USB_MOUNT_DIRECTORY}/*/'):
            if x != globals.VOLUME_DIR:
                # Ignore local directory
                self.new_device_callback(x[:-1])

        self.run()

    def run(self):
        event_handler = Handler(self.new_device_callback, self.removed_device_callable)
        self.observer.schedule(event_handler, globals.USB_MOUNT_DIRECTORY, recursive=False)
        self.observer.start()

class Handler(FileSystemEventHandler):


    def __init__(self, new_device_callback:Callable, removed_device_callback:Callable) -> None:
        super().__init__()
        self.new_device_callback = new_device_callback
        self.removed_device_callback = removed_device_callback

    def on_any_event(self, event):
        # We only care about created or deleted directories
        if event.is_directory and (event.event_type != 'created' or event.event_type != 'deleted'):
            if event.event_type == 'created':
                logging.info(f'New USB device: {event.src_path}')
                if event.src_path != globals.VOLUME_DIR:
                    self.new_device_callback(event.src_path)

            elif event.event_type == 'deleted':
                logging.info(f'Removed USB device: {event.src_path}')
                if event.src_path != globals.VOLUME_DIR:
                    self.removed_device_callback(event.src_path)