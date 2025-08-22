# Entomoscope

A Raspberry Pi-based imaging system with a PyQt5 UI, GStreamer live preview, `libcamera-still` capture, GPIO-controlled linear axis, focus stacking, and ONNX-based specimen classification.

## Features

- Live camera preview embedded in the UI (GStreamer `libcamerasrc` → `glimagesink`)
- Automated axis referencing and focus controls (stepper + endstop switch)
- Autofocus using Laplacian sharpness via appsink frames
- Single-shot and stacked image capture (using `libcamera-still`)
- Background focus stacking to produce `Stacked_*.png`
- ONNX Runtime classification (outlier detection + class prediction)
- USB storage detection, copying, and local drive management

## Hardware requirements

- Raspberry Pi (with camera compatible with `libcamera`)
- Stepper motor driver supported by `pigpio` (e.g., TMCM2209 breakout)
- Linear axis with endstop switch
- Light (LED) and fan controlled via GPIO
- 1‑Wire temperature sensor (optional)

Pins and mechanical parameters are configured in `backend/configuration.py`.

## Software prerequisites

- OS: Raspberry Pi OS (Bullseye or newer recommended)
- Python 3.9+
- System packages:
  - GStreamer with `libcamerasrc` and development headers
  - pigpio daemon (`sudo apt install pigpio` and `sudo systemctl enable --now pigpiod`)
  - libcamera (`libcamera-still` CLI)
  - 1‑Wire modules for temperature sensor (`w1-gpio`, `w1-therm`) if used

## Python dependencies

Install via pip (suggested virtualenv):

```
pip install PyQt5 onnxruntime opencv-python watchdog gpiozero numpy pillow
```

Additionally, for GStreamer Python bindings and GL sink support you may need:

```
sudo apt install python3-gi gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0 gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad
```

And the Raspberry Pi GPIO libraries:

```
pip install RPi.GPIO pigpio
```

## Repository structure

- `frontend/`: UI controller (`ui.py`), GStreamer camera widget, focus widget, image capture wrapper, stacking controller, fan controller, USB watcher
- `backend/`: GPIO device drivers (motor, switch, fan, light, temperature), linear axis abstraction, pin/mechanical config
- `utils/`: helpers for disk space, datetime, integer checking
- `files/`: Qt `.ui` layout and icons; additional ONNX model
- `Models/`: ONNX models used by classification
- `globals.py`: global constants and UI/stacking defaults
- `main.py`: entrypoint

## Running the app

1) Ensure `pigpiod` is running:
```
sudo systemctl enable --now pigpiod
```

2) Launch the UI (from the repo root):
```
python3 main.py
```

If your package name differs or you install as a package, you can also run as a module (ensure `Entomoscope` is importable):
```
python3 -m Entomoscope.main
```

The main window will load `files/untitled.ui` and start the live preview. Use the controls to reference the axis, move focus, take images/stacks, start stacking, and classify.

## Usage overview

- Stepper Enabled: Enables driver, references axis to endstop, enables motion and stacking controls.
- Focus In/Out: Moves the axis by the configured step size (`globals.FOCUS_STEP_SIZE`).
- Autofocus: Pauses live preview, scans for best sharpness, returns to max sharpness position.
- Take Image: Creates a new RAW folder for the current specimen and captures a PNG still.
- Take Stack: Captures N images (configurable) while stepping the axis.
- Fuse Stacks: When checked, starts a background `Stacker` that fuses new stacks into `Stacked_*.png`.
- Classify: Captures a fresh image and runs ONNX outlier detection and classification; result shown in the UI.
- Storage: Select Local or USB device, create new session directories, copy Local→USB, delete Local drive.

## Data layout

```
<root>/<WORKING_DIR>/<YYYY-mm-dd-HH-MM-SS>/
  Specimen_XXX/
    RAW_Data/
      Specimen_XXX_YYY/
        Specimen_XXX_YYY_ZZZ.png
  Stacked_Specimen_XXX_YYY.png
```

`<root>` is the selected device symlink (`globals.LOCAL_DIR` or `globals.USB_DIR`).

## Models

Place ONNX models in `Models/`. The UI expects:
- `Models/model_outlier_detection.onnx`
- `Models/model.onnx`

Update paths in `frontend/ui.py` if relocating models.

## Troubleshooting

- Live preview fails: verify GStreamer plugins and `libcamerasrc`; consider replacing `glimagesink` with another sink if OpenGL not available.
- "Device or resource busy" on capture: ensure live preview is paused during `libcamera-still` (the UI handles this automatically).
- Motor not moving: confirm `pigpiod` is running; check wiring and `backend/configuration.py`; ensure `Axis.enable_axis()` effectively calls `motor.enable()`.
- USB not detected: ensure `/media/entomoscope` exists and udev rules mount devices there; verify `watchdog` installed.
- Classification errors: verify ONNX Runtime installed and models exist at configured paths; ensure input preprocessing shape matches model.

## Safety

- Deletion operations are destructive: copying Local→USB and deleting Local drive permanently remove files on the local storage path defined in `globals.py`. Double-check paths before use.

## License

TBD

## Contributing

- See `NOTES.md` for a detailed code walkthrough and architecture notes.
- Please open issues/PRs for fixes and enhancements.