# LuminaTouch

**LuminaTouch** is a Python-based computer vision tool that turns any ordinary projector surface or non-touch display into an interactive touch screen. 

It uses your webcam (such as a Logitech Brio 500) to track index finger coordinates using Google MediaPipe Tasks API, and uses your wireless presenter remote's **Down** key to trigger native OS left-clicks and drags—eliminating depth ambiguity and false taps.

---

## Features

- **Zero-Hardware Cost:** Works with off-the-shelf webcams and standard wireless presentation remotes.
- **Precision Drag & Click:** Uses the presenter remote button (`Down` arrow) for reliable OS left-click and drag operations without accidental triggering.
- **Interactive 4-Corner Calibration:** Click the 4 corners of your projected display in the camera feed to crop and align tracking using perspective transformation.
- **Automatic Spatial Sorting:** Calibration automatically sorts clicked points into `[Top-Left, Top-Right, Bottom-Right, Bottom-Left]` regardless of click order.
- **Exponential Moving Average (EMA) Smoothing:** Built-in coordinate smoothing and deadzone filtering to eliminate micro-jitter while maintaining low latency.
- **Key Suppression:** Suppresses native presenter button actions (such as unintended slide scrolling) when pressing the click button.

---

## Hardware & Environment Requirements

- **Operating System:** Windows 10 / 11 (Run PowerShell / Command Prompt as **Administrator** for global keyboard hook suppression).
- **Webcam:** 720p @ 60 FPS recommended (e.g., Logitech Brio 500 set to 80°–90° FOV).
- **Presenter Remote:** Standard USB presenter remote mapped to the `Down` arrow key.
- **Python:** Version 3.9 or higher.

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/LuminaTouch.git](https://github.com/your-username/LuminaTouch.git)
cd LuminaTouch
```
### 2. Install Required Python Packages
```bash
pip install opencv-python mediapipe pynput screeninfo keyboard numpy
```
### 3. Download MediaPipe Model Bundle
Download the official `hand_landmarker.task` file and place it directly in the project root folder:

- **Download**: [hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)

Usage Instructions

1. **Open PowerShell / CMD as Administrator**:
Search for PowerShell in the Windows Start menu, right-click, and select **Run as Administrator**.

2. **Launch the Script:**

```Bash
python touch_pointer.py
```
3. **Calibrate the Screen Area:**

- A window named `Touch Pointer Calibration & Debug` will appear displaying your webcam feed.

- Click the 4 corners of your projected screen in the camera window.

- A yellow boundary line will confirm the calibrated region.

4. **Interaction Controls:**

- **Hovering:** Point your index finger toward the screen. A red dot tracks your movement, moving the OS desktop cursor.

- **Click / Drag:** Press and hold the **Down** button on your presenter remote to engage an OS left-click/drag (indicator turns green). Release the button to release the click.

- **Reset Calibration:** Press `r` in the camera preview window to reset corner points.

- **Quit:** Press `q` in the camera preview window to exit.

## Project Structure
```bash
LuminaTouch/
├── hand_landmarker.task     # Google MediaPipe model file
├── touch_pointer.py         # Main application script
├── README.md                # Project documentation
└── .gitignore               # Ignored files (virtual environments, cache)
```
Recommended Camera Settings
For optimal performance with the **Logitech Brio 500:**

- **Resolution & Frame Rate:** 1280x720 @ 60 FPS

- **Field of View (FOV):** 80° – 90°

- **Lighting & Focus:** Lock exposure and disable Auto-Focus in Logi Tune to prevent frame-rate drops during slide transitions.

## License

Distributed under the MIT License. See `LICENSE` for more information.