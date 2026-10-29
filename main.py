import os
import sys
import cv2
import numpy as np
import pynput
from screeninfo import get_monitors
import keyboard
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --- 1. DISPLAY BOUNDS (MIRRORED MODE) ---
primary_monitor = get_monitors()[0]
SCREEN_WIDTH = primary_monitor.width
SCREEN_HEIGHT = primary_monitor.height

print(f"Mirrored Display Target Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}\n")

# --- 2. MEDIAPIPE TASKS SETUP ---
MODEL_PATH = 'hand_landmarker.task'
if not os.path.exists(MODEL_PATH):
    print(f"Error: Could not find '{MODEL_PATH}' in script directory.")
    print("Download from: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task")
    sys.exit(1)

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
detector = vision.HandLandmarker.create_from_options(options)

# --- 3. INPUT CONTROL & PRESENTER HOOK ---
mouse = pynput.mouse.Controller()
Button = pynput.mouse.Button

PRESENTER_KEY = 'down'
is_dragging = False

def on_key_event(e):
    global is_dragging
    if e.name == PRESENTER_KEY:
        if e.event_type == keyboard.KEY_DOWN and not is_dragging:
            mouse.press(Button.left)
            is_dragging = True
            print("[Touch State] DRAGGING (Mouse Down)")
        elif e.event_type == keyboard.KEY_UP and is_dragging:
            mouse.release(Button.left)
            is_dragging = False
            print("[Touch State] HOVERING (Mouse Up)")
        return False  # Suppress native DOWN key from scrolling slides

keyboard.hook_key(PRESENTER_KEY, on_key_event, suppress=True)

# --- 4. CALIBRATION FUNCTIONS & CALLBACKS ---
calibration_points = []
transform_matrix = None

screen_pts = np.float32([
    [0, 0],                         # Top-Left
    [SCREEN_WIDTH, 0],             # Top-Right
    [SCREEN_WIDTH, SCREEN_HEIGHT], # Bottom-Right
    [0, SCREEN_HEIGHT]             # Bottom-Left
])

def order_points(pts):
    """
    Sorts 4 clicked points automatically into order:
    [Top-Left, Top-Right, Bottom-Right, Bottom-Left]
    """
    rect = np.zeros((4, 2), dtype="float32")
    pts = np.array(pts, dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]      # Top-Left
    rect[2] = pts[np.argmax(s)]      # Bottom-Right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]   # Top-Right
    rect[3] = pts[np.argmax(diff)]   # Bottom-Left

    return rect

def update_transform_matrix():
    global transform_matrix
    if len(calibration_points) == 4:
        ordered_cam_pts = order_points(calibration_points)
        transform_matrix = cv2.getPerspectiveTransform(ordered_cam_pts, screen_pts)
        print("4-Corner Perspective Calibration Applied Successfully!")

def mouse_click_event(event, x, y, flags, param):
    global calibration_points
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(calibration_points) < 4:
            calibration_points.append([x, y])
            print(f"Point {len(calibration_points)} added: ({x}, {y})")
            if len(calibration_points) == 4:
                update_transform_matrix()

# --- 5. SMOOTHING FILTER PARAMETERS ---
prev_target_x, prev_target_y = None, None
SMOOTHING_ALPHA = 0.2  # Lower value = smoother motion (0.1 to 0.3 recommended)
DEADZONE_PIXELS = 3    # Ignores tiny sub-3px camera jitter when holding stationary

# --- 6. CAMERA INIT & WINDOW SETUP ---
CAMERA_INDEX = 0  # 1 or 2 for external Logitech Brio 500; 0 for laptop webcam
cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    print(f"Camera index {CAMERA_INDEX} unavailable. Fallback to default index 0...")
    cap = cv2.VideoCapture(0)

# Force 1280x720 Resolution @ 60 FPS
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 60)

# Verify applied settings
actual_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
actual_fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Webcam initialized at: {int(actual_w)}x{int(actual_h)} @ {int(actual_fps)} FPS")

cv2.namedWindow("Touch Pointer Calibration & Debug")
cv2.setMouseCallback("Touch Pointer Calibration & Debug", mouse_click_event)

print("--- INSTRUCTIONS ---")
print("1. Click any 4 corners of your projector screen in the camera view.")
print("2. Press 'r' to reset calibration points.")
print("3. Press 'q' to quit application.\n")

cam_pts = np.float32([[0, 0], [1280, 0], [1280, 720], [0, 720]])
transform_matrix = cv2.getPerspectiveTransform(cam_pts, screen_pts)

INVERT_VERTICAL_AXIS = False

# --- 7. MAIN PROCESSING LOOP ---
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        continue

    # Mirroring disabled per your physical setup
    # frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    detection_result = detector.detect(mp_image)

    finger_x, finger_y = None, None

    if detection_result.hand_landmarks:
        hand_landmarks = detection_result.hand_landmarks[0]
        index_tip = hand_landmarks[8]  # Index fingertip landmark

        finger_x = int(index_tip.x * w)
        finger_y = int(index_tip.y * h)

        color = (0, 255, 0) if is_dragging else (0, 0, 255)
        cv2.circle(frame, (finger_x, finger_y), 10, color, -1)

    if finger_x is not None and finger_y is not None and transform_matrix is not None:
        pts = np.array([[[finger_x, finger_y]]], dtype=np.float32)
        mapped_pts = cv2.perspectiveTransform(pts, transform_matrix)

        raw_x = int(np.clip(mapped_pts[0][0][0], 0, SCREEN_WIDTH))
        calculated_y = int(np.clip(mapped_pts[0][0][1], 0, SCREEN_HEIGHT))

        raw_y = SCREEN_HEIGHT - calculated_y if INVERT_VERTICAL_AXIS else calculated_y

        # --- EXPONENTIAL MOVING AVERAGE (EMA) SMOOTHING ---
        if prev_target_x is None or prev_target_y is None:
            smooth_x, smooth_y = raw_x, raw_y
        else:
            smooth_x = int(prev_target_x + SMOOTHING_ALPHA * (raw_x - prev_target_x))
            smooth_y = int(prev_target_y + SMOOTHING_ALPHA * (raw_y - prev_target_y))

        # Deadzone check: prevent jittering when holding hand stationary
        if prev_target_x is not None and prev_target_y is not None:
            dist = np.hypot(smooth_x - prev_target_x, smooth_y - prev_target_y)
            if dist > DEADZONE_PIXELS:
                mouse.position = (smooth_x, smooth_y)
                prev_target_x, prev_target_y = smooth_x, smooth_y
        else:
            mouse.position = (smooth_x, smooth_y)
            prev_target_x, prev_target_y = smooth_x, smooth_y
    else:
        # Reset filter state when hand leaves webcam frame
        prev_target_x, prev_target_y = None, None

    # --- DRAW CALIBRATION OVERLAY ---
    for idx, pt in enumerate(calibration_points):
        cv2.circle(frame, (pt[0], pt[1]), 8, (255, 0, 0), -1)
        cv2.putText(frame, str(idx + 1), (pt[0] + 10, pt[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    if len(calibration_points) == 4:
        pts_poly = np.array(calibration_points, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts_poly], isClosed=True, color=(0, 255, 255), thickness=2)
    else:
        cv2.putText(frame, f"Click Corner [{len(calibration_points) + 1}/4]", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("Touch Pointer Calibration & Debug", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('r'):
        calibration_points = []
        transform_matrix = cv2.getPerspectiveTransform(cam_pts, screen_pts)
        prev_target_x, prev_target_y = None, None
        print("Calibration points reset. Click 4 corners again.")
    elif key == ord('q'):
        break

# --- CLEANUP ---
if is_dragging:
    mouse.release(Button.left)
keyboard.unhook_all()
cap.release()
cv2.destroyAllWindows()
print("Touch Pointer stopped.")