# README.md

## Entomoscope – Standalone (Pi GPIO) and Plugin (Arduino/CNC) Modes

This README shows how to run the original Standalone build and how to customize for a Plugin build with an Arduino + CNC shield.

### Features (common)
- Live preview (GStreamer `libcamerasrc`), still capture (`libcamera-still`)
- Motorized focus control and autofocus
- Stacked image fusion
- ONNX classification (outlier + class)
- Storage management and USB detection

---

## 1) Choose your mode

- Standalone: Raspberry Pi drives motor/light/fan/switch via GPIO.
- Plugin: Arduino (with GRBL or custom firmware) drives motion (and possibly lighting); Raspberry Pi communicates over USB serial.

Select mode at runtime (recommended):
- Env var: `ENTOMOSCOPE_MODE=standalone` or `ENTOMOSCOPE_MODE=plugin`
- Or set a flag in a config module (e.g., `globals.py`) if you prefer.

---

## 2) Hardware requirements

Standalone
- Raspberry Pi with camera compatible with `libcamera`
- Stepper driver wired to Pi GPIO; endstop switch to GPIO
- LED light, fan on GPIO
- Optional 1‑Wire temperature sensor

Plugin
- Arduino + CNC shield (GRBL or custom firmware)
- Endstops wired to CNC shield
- Optional LED dimmer (PWM or serial via Arduino)
- Raspberry Pi still used for camera, UI, stacking, classification

---

## 3) Software prerequisites (both)

- Raspberry Pi OS (Bullseye or newer), Python 3.9+
- GStreamer with `libcamerasrc`, libcamera (`libcamera-still`)
- pigpio daemon (Standalone), `pyserial` (Plugin)
- Python deps:
pip install PyQt5 onnxruntime opencv-python watchdog gpiozero numpy pillow

- GStreamer Python bindings:
sudo apt install python3-gi gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0 gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad

