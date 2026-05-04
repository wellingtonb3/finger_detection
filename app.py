import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import math
import warnings

# Silence external library warnings in the OCI console
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf')
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- MEDIAPIPE CONFIGURATION ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Optimized configuration for static photos in the cloud
hands = mp_hands.Hands(
    static_image_mode=True, 
    max_num_hands=1, 
    min_detection_confidence=0.3,
    min_tracking_confidence=0.5
)

# Function to calculate distance between points (essential for any hand angle)
def calculate_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

st.set_page_config(page_title="OCI Gesture Detector", layout="centered")
st.title("📸 Robust Finger Counter")
st.write("The analysis works even if the hand is tilted or horizontal.")

# Capture Interface (Snapshot - does not save to disk)
img_file = st.camera_input("Position your hand and take a photo")

if img_file:
    img = Image.open(img_file)
    img_rgb = np.array(img)
    annotated_image = img_rgb.copy()
    
    # In-memory processing
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the colored skeleton for visual feedback
            mp_drawing.draw_landmarks(
                annotated_image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            # --- DISTANCE-BASED COUNTING LOGIC ---
            fingers = []
            wrist = hand_landmarks.landmark[0]

            # IDs for Index, Middle, Ring, and Pinky fingers
            # (Comparing Tip distance vs Middle Joint distance relative to the wrist)
            finger_ids = [(6, 8), (10, 12), (14, 16), (18, 20)]

            for pip_id, tip_id in finger_ids:
                dist_wrist_pip = calculate_distance(wrist, hand_landmarks.landmark[pip_id])
                dist_wrist_tip = calculate_distance(wrist, hand_landmarks.landmark[tip_id])

                # If the tip is 10% further than the middle joint, the finger is extended
                if dist_wrist_tip > (dist_wrist_pip * 1.1):
                    fingers.append(1)
                else:
                    fingers.append(0)

            # Thumb Logic (Distance between thumb tip and pinky base)
            dist_thumb_tip_pinky_base = calculate_distance(hand_landmarks.landmark[4], hand_landmarks.landmark[17])
            dist_thumb_base_pinky_base = calculate_distance(hand_landmarks.landmark[2], hand_landmarks.landmark[17])

            if dist_thumb_tip_pinky_base > dist_thumb_base_pinky_base:
                fingers.append(1)
            else:
                fingers.append(0)

            total_fingers = fingers.count(1)
            # ---------------------------------------
            
            # Display the result and the annotated image
            st.metric(label="Extended Fingers Detected", value=total_fingers)
            st.image(annotated_image, caption="Visual Analysis Result", use_container_width=True)

    else:
        st.error("No hand detected. Try showing your palm and wrist.")

st.info("Note: System processing via Snapshot. No images were saved on the instance.")