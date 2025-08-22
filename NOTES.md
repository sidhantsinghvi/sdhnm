# Entomoscope: Comprehensive Codebase Notes

This document explains every file in the repository, how they relate, and how the system works end-to-end. It is intended for developers maintaining or extending the project.

## 1) High-level architecture

- Application type: PyQt5 desktop application targeting Raspberry Pi, with GStreamer live preview, `libcamera-still` capture, GPIO-driven motion and lighting, focus stacking, and ONNX-based image classification.
- Layers:
  - Frontend UI (`frontend/`): Qt widgets, camera preview, user interactions, workflows for capture/stacking/classification, storage management.
  - Backend hardware (`backend/`): GPIO device drivers (motor, endstop switch, fan, light, temperature sensor), linear axis abstraction, hardware pin config.
  - Utilities (`utils/`): helpers for disk space, ints, datetime validation.
  - Data and assets (`files/`, `Models/`): Qt Designer UI, icons, and ONNX models.
  - Entrypoint (`main.py`): program startup.

At runtime, the UI orchestrates hardware via the backend drivers, acquires images using `libcamera-still` and the live feed via GStreamer, organizes captured data into a directory hierarchy, optionally fuses stacks into a single sharp image, and runs ONNX models for outlier detection and classification.

## 2) Lifecycle and data flow (startup → shutdown)

1. Start: `main.py` creates a Qt application and loads the `Ui` class with the `.ui` file.
2. UI initialization:
   - Wires all buttons, checkboxes, lists, tree view, galleries, and camera widget.
   - Instantiates hardware: `Light`, `Motor`, `Switch`, wraps them as a linear `Axis`.
   - Starts a USB drive watcher to detect removable storage mount/unmount under `/media/...`.
   - Creates or selects a working directory under either local or USB storage.
   - Sets up the live video preview via GStreamer to render inside a Qt widget.
3. User actions drive workflows:
   - Enable stepper → axis references to endstop → motion buttons become active.
   - Focus in/out → moves linear axis by a configured step.
   - Autofocus → temporarily pauses live preview → GStreamer `appsink` measures Laplacian sharpness while scanning → axis moves back to best position → live preview resumes.
   - Take single image → pauses preview → calls `libcamera-still` to capture PNG → resumes preview.
   - Take stack → collects multiple images while moving axis between captures.
   - Fuse stacks (optional) → `Stacker` background thread finds new stacks and runs `Stacking` algorithm to produce `Stacked_*.png` outputs.
   - Classify (optional) → runs ONNX models to detect outliers then predict class.
   - Storage management → explorer lists folders; copy local→USB; delete local storage; update disk usage labels.
4. Shutdown: UI exposes a shutdown button that disables motor and issues `sudo shutdown -h now`.

## 3) Filesystem and data layout

- Local and USB roots use symlinks for shorter paths:
  - `globals.LOCAL_DIR` symlinks to `globals.VOLUME_DIR` (e.g., `/mnt/ssd/`).
  - `globals.USB_DIR` symlinks to the selected USB mount path under `globals.USB_MOUNT_DIRECTORY`.
- Working directory: `<root>/<WORKING_DIR>` where `<root>` is local or USB symlink and `WORKING_DIR='Entomoscope_Images'`.
- Session directories: timestamped folders (format in `globals.DIRECTORY_NAMING_FORMAT`).
- Specimen folders: `Specimen_XXX` per individual.
- Raw images for a specimen: `<session>/Specimen_XXX/RAW_Data/<Specimen_XXX_YYY>/<Specimen_XXX_YYY_ZZZ.png>`
- Stacked outputs are placed next to the specimen folder: `<session>/Specimen_XXX/Stacked_<Specimen_XXX_YYY>.png`

---

## 4) Top-level files

### `main.py`
- Creates a Qt `QApplication` and loads the main window (`Ui`) with `files/untitled.ui`.
- Instantiates `FanController` (thread) but the `start()` is commented out.
- Deletes `~/l` and `~/u` symlinks on startup (cleanup for device symlinks used later by the UI).
- Important: Imports `Entomoscope.frontend...` modules using the package name `Entomoscope`. Ensure your folder/package is named `Entomoscope` or `PYTHONPATH` is set appropriately.

### `globals.py`
- Application-wide constants and defaults:
  - Camera: `CAMERA_NAME` (used by GStreamer `libcamerasrc`).
  - UI: icon sizes, checkbox styles.
  - Stacking/Autofocus params: kernel sizes, Laplacian settings, RANSAC thresholds, number of stacks, offsets, etc.
  - Filesystem: `WORKING_DIR`, directory naming format, symlink targets: `VOLUME_DIR`, `LOCAL_DIR`, `USB_DIR`.
  - Global variable updated at runtime: `SHARPNESS` during autofocus.

### `__init__.py` (root)
- Re-exports `backend`, `frontend`, and `globals` for package import convenience.

---

## 5) Backend (hardware layer)

### `backend/configuration.py`
- Hardware pin mappings and mechanical constants:
  - Fan, temperature sensor, light pins.
  - Motor driver pins (MS1, MS2, SPREAD, UART1/2, EN, STEP, DIRECTION).
  - Motor behavior: microstep resolution, speed, steps per revolution.
  - Axis parameters: distance per revolution (µm), physical length, top/bottom safety gaps, endstop switch pin.

### `backend/components/axis.py`
- Abstraction for a linear axis with a stepper motor and a limit switch.
- Key capabilities:
  - `reference()`: Enables axis, drives toward endstop fast until engaged, backs off slowly until released, sets zero at `gap_bottom` offset, marks “referenced”.
  - Movement by distance (µm) or microsteps: `move_up_for`, `move_down_for`, with range checks; `move_to` absolute position.
  - Position helpers: `highest_position()`, `middle_position()`, `get_position()`.
  - Range/units utils: convert µm↔microsteps, enforce travel limits based on mechanical size and gaps.
- Depends on a `Motor` object and a `Switch` object.

### `backend/devices/motor.py`
- Stepper motor control using the `pigpio` daemon waveforms:
  - Configures pins using `pigpio` and builds a square-wave step train as a “wave”.
  - Continuous turns: `turn_right`, `turn_left` (repeat wave until stopped).
  - Finite movement: `turn_right_for(steps)`, `turn_left_for(steps)` using `wave_chain`, chunked for >65k steps.
  - `change_speed(new_speed)`: regenerates the waveform with new delay; toggles spread mode for high speeds.
  - `enable()`/`disable()` control the EN pin.

### `backend/devices/fan.py`
- Fan control using RPi.GPIO with optional PWM speed control via `GPIO.PWM`.
- On/off and `fan_at_speed(duty_cycle)` (percent).

### `backend/devices/light.py`
- Simple GPIO output for illumination LED.

### `backend/devices/switch.py`
- Digital input wrapper for an endstop switch with `get_status()` returning boolean state.

### `backend/devices/temperature_sensor.py`
- Reads a 1‑Wire temperature sensor (e.g., DS18B20):
  - Auto-loads kernel modules `w1-gpio` and `w1-therm` if needed.
  - Parses `/sys/bus/w1/devices/*/w1_slave` to Celsius.

### `backend/System.py`
- A standalone bring-up/example script: constructs devices, references axis, moves it, toggles fan. Useful for hardware testing.

### `backend/resolution.txt`
- Notes calculating microstep resolutions and µm/step for various microstepping settings.

### `backend/__init__.py`, `backend/components/__init__.py`, `backend/devices/__init__.py`
- Convenience re-exports; not much logic.

---

## 6) Frontend (application/UI layer)

### `frontend/ui.py` (Main window controller)
- Loads `files/untitled.ui` and binds UI elements (buttons, labels, lists, tree view, splash, galleries, etc.).
- Embeds a live video widget (`VideoWidget`) and an image capture wrapper (`ImageCamera`).
- Instantiates hardware and motion stack: `Light`, `Motor`, `Switch`, `Axis` using values from `backend/configuration.py`.
- Drives workflows via button handlers:
  - Stepper enable: enables the motor driver and immediately references the axis; toggles availability of related controls.
  - Focus in/out: moves the axis by `globals.FOCUS_STEP_SIZE`.
  - Autofocus: pauses live preview; starts `FocusWidget` pipeline receiving `appsink` frames; moves axis while sampling Laplacian variances; returns to peak sharpness; resumes preview.
  - Take image: creates a new RAW folder for the current specimen; pauses preview; calls `ImageCamera.take_image`; resumes; updates free space.
  - Take stack: similar but captures N images, moving between shots; restores previous position.
  - Fuse stacks (checkbox): starts/stops `Stacker` background thread that scans for new stacks and produces `Stacked_*.png` via `Stacking`.
  - Classify: captures a fresh image, preprocesses to NCHW float32, runs `model_outlier_detection.onnx` then `model.onnx` via `onnxruntime` CPU provider, updates the classification textbox.
  - Storage: browse to select a session, create a new session, manage specimens, copy Local→USB (tree copy), delete local drive (recursive), update disk usage labels.
  - File explorer and galleries: populate stacked/single image lists, clicking updates the main `bigimg` pixmap; supports fullscreen viewer with zoom controls.
- USB device handling: maintains a list of available storage devices; symlinks `LOCAL_DIR` to `VOLUME_DIR` and `USB_DIR` to the selected USB path; re-roots the explorer to `WORKING_DIR` under the selected device.
- Uses many helpers from `globals.py`, `utils/`, and other frontend modules.

### `frontend/video_widget.py`
- Qt `QWidget` backed by a GStreamer pipeline rendering into an OpenGL sink embedded in the widget window ID.
- Pipeline: `libcamerasrc camera-name="<globals.CAMERA_NAME>" ! videoscale ! videoflip method=counterclockwise ! glimagesink`.
- Handles the `prepare-window-handle` sync-message to bind sink to the Qt window.
- `start_pipeline()`/`pause_pipeline()` control playback.

### `frontend/focus_widget.py`
- GStreamer pipeline with `appsink` to pull frames into Python and compute a Laplacian-variance sharpness metric with OpenCV.
- Updates `globals.SHARPNESS` continuously while running; used by `Ui.do_autofocus()`.
- Pipeline (conceptually): `libcamerasrc ... ! [resize] ! appsink emit-signals=True` where `[resize]` should be a converter/scaler producing a CPU-friendly pixel format.

### `frontend/image_camera.py`
- Captures a single PNG still using `libcamera-still` CLI with retries and timeout, ensuring the output path is a file.
- Logs and detects “device busy” to signal live preview must be paused while capturing.

### `frontend/controller/stacking.py`
- Focus-stacking implementation:
  - Aligns images pairwise using ECC translation (`cv2.findTransformECC`) to mitigate minor shifts between captures.
  - Computes Laplacian maps (after Gaussian blur) and composites per-pixel maxima to pick the sharpest contributor at each pixel location.
  - Returns a stacked image.

### `frontend/controller/stacker.py`
- Background thread scanning the working directory for new RAW image stacks not yet fused; runs `Stacking` and writes `Stacked_<specimen_folder>.png` outputs.
- Skips if a stacked image already exists; logs progress.

### `frontend/controller/fan_controller.py`
- Background thread monitoring CPU and external sensor temperatures; runs fan at 60% duty if thresholds crossed for at least `globals.MIN_RUNTIME_FOR_FAN_IN_SEC`; on stop, turns fan off.

### `frontend/controller/usb_device_watcher.py`
- Watches `globals.USB_MOUNT_DIRECTORY` using `watchdog` for created/deleted directories; calls UI callbacks to update available devices.
- On init, adds currently mounted USB devices (excludes local volume dir).

### `frontend/__init__.py` and `frontend/controller/__init__.py`
- Re-exports for convenience.

---

## 7) Utilities

### `utils/get_free_space.py`
- Wraps `shutil.disk_usage` to return `(total_gib, used_gib, free_gib)` for a given path.

### `utils/is_int.py`
- Predicate returning True if a string can be parsed to `int`.

### `utils/validate_datetime.py`
- Validates whether a string matches a datetime format; logs error on mismatch.

---

## 8) Assets, models, and UI definition

### `files/untitled.ui`
- Qt Designer file defining the window layout and named widgets; `Ui` loads and then looks up elements by object names.

### `files/imgs/*`
- PNG icons used by the UI (add, delete, arrows, brightness, autofocus, classify, USB, etc.).

### `files/segment_insect_tiny_64.onnx`
- An ONNX model artifact not currently referenced in code paths shown here; likely an experimental segmentation model.

### `Models/model_outlier_detection.onnx`, `Models/model.onnx`
- ONNX models loaded in `ui.py` for outlier detection and class prediction.

---

## 9) Integration points and key sequences

- Live preview: `Ui` holds a `VideoWidget` which starts a GStreamer pipeline rendering camera frames into a Qt widget.
- Autofocus: `Ui.do_autofocus()`
  1) Pause live preview.
  2) Start `FocusWidget` (appsink). While moving along the axis in fixed steps, collect `globals.SHARPNESS` samples.
  3) Stop `FocusWidget`, resume preview.
  4) Move axis back down by `num_steps * step_size` to the best sharpness (argmax of measured series).
- Capture workflows:
  - Single: create a new specimen RAW folder; pause preview; `libcamera-still -n -e png -t 1 -o <path>`; resume; update disk usage.
  - Stack: remember current axis position; move down slightly; loop N times: capture → move up; resume; return to starting position.
- Stacking background job: when enabled via checkbox, `Stacker` scans all session/specimen RAW folders and writes stacked images for any missing outputs.
- Classification: capture a fresh image, preprocess to `float32` NCHW scaled to [0,1], then:
  1) Outlier detector: if prob > 0.5 → “other”.
  2) Else class predictor: pick argmax and label string from `INDEX_TO_CLASS_PRED`.
- USB device handling: a `watchdog` observer reports created/deleted directories under `/media/entomoscope`; UI updates the available devices list and symlinks the selected device to `globals.USB_DIR`.

---

## 10) Known pitfalls and recommendations

- Package import path:
  - `main.py` imports from `Entomoscope.*`. Ensure the repository directory is named `Entomoscope` and you run the app as `python3 -m Entomoscope.main` from the parent directory, or otherwise adjust `PYTHONPATH`/package installation.

- Axis enable bug:
  - `Axis.enable_axis()` currently does `self.motor.enable` without parentheses. It should be `self.motor.enable()` to actually drive the EN pin low. This might prevent movement if the motor driver starts disabled.

- UI button variables swapped:
  - In `ui.py`, `focus_out = findChild('focus_in')` and `focus_in = findChild('focus_out')`. Verify naming in the `.ui` file; consider swapping assignments for clarity.

- USB event filter logic:
  - In `usb_device_watcher.py`, the conditional `if event.is_directory and (event.event_type != 'created' or event.event_type != 'deleted'):` will always be true for directories. It should likely be `and` to pass only non-created/non-deleted events, or better: explicitly handle `if event.event_type == 'created'` and `elif event.event_type == 'deleted'` (as the code already does) and drop the precondition entirely.

- Hard-coded model paths:
  - `ui.py` uses paths like `'./entomoscope-software/Entomoscope/Models/model.onnx'`. Consider using paths relative to this repo root (e.g., `'./Models/model.onnx'`) or package resources for portability.

- GStreamer element naming:
  - `focus_widget.py` uses `resize` in the pipeline. Ensure this element exists or replace with `videoscale ! videoconvert ! video/x-raw,format=BGR,width=...,height=...` as needed.

- `libcamera-still` flags:
  - The invocation uses `-t1`; commonly it is `-t 1`. Confirm parsing. Also `exposure_time` parameter is not applied; consider wiring it to `libcamera-still` flags.

- Destructive actions:
  - `main.py` removes `~/l` and `~/u` symlinks at startup. `Ui.delete_local_drive()` deletes all files under `globals.LOCAL_DIR`. Use with caution and ensure paths are correct.

- Minor stability items:
  - Multiple `QtCore` imports and some static method calls on `QMainWindow` where instance methods might be intended.
  - Global variables like `pathSelectedDirectory` and `itemPath` could be encapsulated for clarity.

---

## 11) Extending the system

- Adding a new classification model:
  - Drop the ONNX into `Models/`, update paths in `ui.py`, and adjust preprocessing shape.
- Headless or different sinks:
  - If OpenGL sink is not available, replace `glimagesink` with a suitable sink (e.g., `ximagesink`, `udpsink`, or `fakesink`) in `video_widget.py`.
- New motion stages:
  - Implement additional axes via more `Motor`/`Switch` instances and extend `Axis` or create new component abstractions.
- Storage destinations:
  - Replace symlink model with mount points or network storage; adjust `globals.VOLUME_DIR` and USB watcher accordingly.

---

## 12) Quick dependency map

- UI → Frontend
  - `Ui` → `VideoWidget`, `ImageCamera`, `FocusWidget`, `Stacker`, `UsbDrivesWatcher`, utils, globals, backend hardware classes.
- Hardware
  - `Axis` → `Motor`, `Switch`
  - `FanController` → `Fan`, `TemperaureSensor`, `gpiozero.CPUTemperature`
- Imaging
  - Live: GStreamer `libcamerasrc` pipeline → `VideoWidget`
  - Still: `libcamera-still` → `ImageCamera`
  - Stacking: OpenCV/PIL → `Stacking` → `Stacker`
  - Classification: `onnxruntime` → models in `Models/`
- Storage
  - USB events: `watchdog` → `UsbDrivesWatcher`
  - Disk space: `shutil.disk_usage` → `get_free_space_in_gb`

This concludes the per-file description and system context. Use this as a reference for debugging, extending, and onboarding new contributors.