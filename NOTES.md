# Entomoscope: Comprehensive Codebase Notes

This document explains every file in the repository, how they relate, and how the system works end-to-end. It is intended for developers maintaining or extending the project.


TL;DR:

It’s a Raspberry Pi app to take clear insect photos.

It moves/auto-focuses a motorized stage to get sharp images.

It stacks multiple shots into one sharper picture.

It can label the insect using built‑in AI models.

It manages saving/copying images (to USB), and controls the light and fan.


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

## 3) File-by-file notes (Standalone)

Top-level
- `main.py`: Starts PyQt app and loads `Ui`. Cleans `~/l` and `~/u` symlinks. Fan controller optionally started.
- `globals.py`: App constants: camera name, UI styles, stacking/autofocus params, directory naming, symlink paths.
- `__init__.py`: Re-exports `backend`, `frontend`, `globals`.

Frontend
- `frontend/ui.py`: Main window. Wires controls, creates `Light`, `Motor`, `Switch`, wraps in `Axis`; autofocus routine using `FocusWidget`; take image/stack; start `Stacker`; classification; storage UI and USB handling.
- `frontend/video_widget.py`: GStreamer widget rendering live preview into Qt.
- `frontend/focus_widget.py`: GStreamer appsink to compute Laplacian sharpness for autofocus.
- `frontend/image_camera.py`: Takes stills with `libcamera-still`.
- `frontend/controller/stacking.py`: Aligns stack with ECC, Laplacian compositing.
- `frontend/controller/stacker.py`: Background scanner to produce `Stacked_*.png`.
- `frontend/controller/fan_controller.py`: Temp‑based fan control (Pi + 1‑Wire + gpiozero).
- `frontend/controller/usb_device_watcher.py`: Watches `/media/entomoscope` for USBs.

Backend: GPIO devices and axis
- `backend/configuration.py`: Pins, microstepping, speeds, axis distances/gaps.
- `backend/components/axis.py`: Referencing via endstop, range/units conversion, move/position helpers. Calls `Motor` and `Switch`.
- `backend/devices/motor.py`: pigpio waveforms, enable/disable, continuous and finite steps, `change_speed`.
- `backend/devices/switch.py`: RPi.GPIO input.
- `backend/devices/fan.py`, `light.py`: RPi.GPIO outputs (fan has PWM option).
- `backend/devices/temperature_sensor.py`: Reads 1‑Wire temp sensor.
- `backend/System.py`: Bring‑up script.
- `backend/resolution.txt`: Microstep → µm resolution notes.

Utils, Assets, Models
- `utils/*`: disk space, date validation, int check.
- `files/untitled.ui`, `files/imgs/*`, and additional ONNX.
- `Models/*`: ONNX models for classification.

Known caveats (Standalone)
- `Axis.enable_axis()` calls `self.motor.enable` (missing parentheses) — fix to `self.motor.enable()`.
- UI variable names for focus buttons look swapped (`focus_in`/`focus_out` binding).
- Hard‑coded ONNX paths in `ui.py` — prefer relative `./Models/…`.

---

## 4) Plugin mode: what changes in code

New dependencies
- `pyserial` (e.g., `pip install pyserial`)
- Arduino firmware:
  - Option A: GRBL (speaks G‑code, homing `$H`, jogs `G0 Z…`, steps/mm via `$102`).
  - Option B: Custom firmware (define your simple ASCII protocol, e.g., `HOME`, `MOVE +1234`, `MOVE -500`, `POS?`).

Device drivers (backend) – replace GPIO with serial
- Add: `backend/devices/arduino_serial.py`
  - Opens `/dev/ttyACM0` (configurable), 115200 baud (typical).
  - Line‑based `write_command(...)` and `read_reply(...)`, with timeouts and error handling.
- Add one of:
  - `backend/devices/grbl_motor.py` (wrap GRBL): methods `home()`, `move_to(mm)`, `move_rel(mm)`, `get_pos_mm()`, `set_zero()`. Translate µm↔mm. Endstops handled by GRBL.
  - or `backend/devices/arduino_motor.py` (custom proto): send `MOVE`/`HOME` commands; keep track of position if firmware reports it.
- Optional lighting/fan:
  - If LED dimmer is on Arduino: `backend/devices/arduino_light.py` (commands like `LIGHT ON`, `LIGHT PWM 128`).
  - Otherwise keep existing `light.py` on Pi GPIO.

Axis component (backend/components/axis.py)
- Keep the axis interface (reference, move_up_for, move_down_for, move_to).
- Internally swap to call the new serial motor driver.
  - `reference()` → call GRBL `$H` (home) or firmware `HOME`.
  - `move_*`/`move_to` → issue G‑code `G0 Z…` or custom `MOVE …`.
  - Positioning:
    - With GRBL: read position with `?`/status (or track after setting `G92 Z0`).
    - With custom: firmware should return current steps/position.

Configuration (backend/configuration.py)
- For plugin mode:
  - Remove/ignore unused GPIO motor pins; keep fields only if you continue using Pi GPIO for light/fan.
  - Add serial port and motion parameters:
    - `SERIAL_PORT = "/dev/ttyACM0"`
    - `SERIAL_BAUD = 115200`
    - `STEPS_PER_MM` or direct `MM_PER_REV` if using custom firmware.
  - Axis geometry (distance per revolution, gaps) stays relevant for UI/labels and range validation. With GRBL you can rely more on firmware limits.

UI wiring (frontend/ui.py)
- Introduce a runtime “mode” switch:
  - Env var: `ENTOMOSCOPE_MODE=standalone|plugin`
  - or config flag in `globals.py`, e.g., `MODE = "plugin"`
- On startup choose drivers:
  - Standalone: `Motor`, `Switch`, `Light` (existing).
  - Plugin: construct `GrblMotor` (or `ArduinoMotor`) via `ArduinoSerial`; optional `ArduinoLight`; no local `Switch` (endstops via firmware).
- Reference and motion buttons continue to call `Axis`, which now talks over serial.
- Autofocus, stacking, classification, storage — unchanged.

USB watcher, camera, classification
- Unchanged between modes.

---

## 5) Step‑by‑step migration checklist

1) Hardware
- Assemble the Plugin variant (Arduino + CNC shield + LED dimmer, endstops wired to CNC shield).
- Set GRBL steps/mm for your Z axis (`$102`), soft limits and homing if using GRBL, or flash your custom firmware.

2) Pi software
- `pip install pyserial`
- Keep existing GStreamer/libcamera/OpenCV/ONNX deps.

3) Add plugin drivers (new files)
- `backend/devices/arduino_serial.md` (design doc) and implement `.py` in code.
- `backend/devices/grbl_motor.md` (design doc) and implement `.py` (or `arduino_motor.py`).

4) Update configuration
- Add `SERIAL_PORT`, `SERIAL_BAUD`, motion units (steps/mm or mm travel).
- Keep axis travel/gaps consistent with your mechanical build.

5) Switch mode in UI
- Add a small factory in `frontend/ui.py` to pick Standalone vs Plugin drivers based on env/config.

6) Test sequence
- Connect Arduino, check `/dev/ttyACM0` permissions (`dialout` group).
- Test homing/reference from the UI.
- Test small relative moves, then autofocus.
- Capture single and stacked images, verify `Stacked_*.png` creation.
- Run classification.

7) Lighting/Fan
- If moved to Arduino: implement serial commands and update UI toggle handlers to call Arduino light driver.
- If kept on Pi GPIO: keep current `light.py` and `fan_controller.py`.

---

## 6) Mapping your wiki differences to software

- Electronics Base: “Installing the Arduino”, “Installing the CNC shield”, “Installing the LED dimmer”, “WAGO Clamp Adapter”
  - Software: add serial driver(s), route motion/light over serial, add config for port/baud; GPIO for fan may remain Pi‑side.
- Motor Frame/Mount, Linear Unit, Energy Chain
  - Software: adjust axis range parameters; for GRBL set `$130…$132` (travel limits) and `$102` (steps/mm).
- Camera, Lighting Assembly
  - Software: unchanged capture pipeline; if dimmer via Arduino, add serial light commands.
- “Installing the ENIMAS Software” / “Arduino Code”
  - Software: this repo = Pi side; “Arduino Code” = flash GRBL or custom firmware.

---

## 7) Keep/Change summary per file

Keep unchanged (both modes)
- `frontend/video_widget.py`, `frontend/focus_widget.py`, `frontend/image_camera.py`, `frontend/controller/stacking.py`, `frontend/controller/stacker.py`, `frontend/controller/usb_device_watcher.py`, `utils/*`, `files/*`, `Models/*`.

Change for Plugin mode
- `backend/devices/motor.py` → replace with serial motor driver (`grbl_motor.py` or `arduino_motor.py`).
- `backend/devices/switch.py` → remove or stub (endstops handled in firmware).
- `backend/configuration.py` → add serial config; remove unused motor pin fields.
- `backend/components/axis.py` → route to serial driver; reference via firmware; position queries via firmware or tracked.
- `frontend/ui.py` → driver factory (mode switch), wire light optionally to Arduino.

Optional
- `frontend/controller/fan_controller.py` → keep on Pi, or re‑implement via Arduino commands if fan is moved.

---

## 8) Risks & tips

- Homing consistency: ensure firmware zero matches UI expectation. If using GRBL, call `G92 Z0` after `$H` if you want a local Z=0.
- Units: UI works in µm; GRBL works in mm. Convert reliably and clamp to limits.
- Timeouts: add serial read timeouts and robust error handling.
- Permissions: add `pi` user to `dialout` for `/dev/ttyACM0`.
- Lighting dimmer: PWM ranges differ per dimmer; document expected range (0–255, 0–100%).
