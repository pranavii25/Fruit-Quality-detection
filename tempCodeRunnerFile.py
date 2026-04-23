import streamlit as st
import tensorflow as tf
import cv2
import numpy as np
from PIL import Image
import serial
import time

# ---------------- CONFIG ----------------
SERIAL_PORT = "COM3"
BAUD_RATE = 9600
IMG_SIZE = 224

# ---------------- SERIAL INIT (ONCE) ----------------
if "serial_init" not in st.session_state:
    try:
        st.session_state.esp32 = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        st.session_state.serial_ok = True
    except Exception as e:
        st.session_state.serial_ok = False
        st.session_state.serial_error = str(e)
    st.session_state.serial_init = True

# ---------------- LOAD MODEL ----------------
@st.cache_resource
def load_model():
    return tf.keras.models.load_model("fruit_quality_model.h5")

model = load_model()
CLASS_MAP = {0: "Fresh", 1: "Rotten"}

# ---------------- UI ----------------
st.set_page_config(page_title="Fruit Quality Detection", layout="centered")
st.title("🍎 Fruit Quality Detection (AI + ESP32)")

if st.session_state.serial_ok:
    st.success("✅ ESP32 Connected")
else:
    st.error(f"❌ ESP32 NOT Connected: {st.session_state.serial_error}")

# ---------------- MODE SELECTION ----------------
mode = st.radio(
    "Select Detection Mode",
    [
        "📁 Upload Image",
        "📷 Capture Image",
        "🎥 Real-time Video Stream"
    ],
    horizontal=True
)

# ---------------- PREDICTION FUNCTION ----------------
def predict(image_np, send_serial=True):
    img = cv2.resize(image_np, (IMG_SIZE, IMG_SIZE))
    img = img / 255.0
    img = np.expand_dims(img, axis=0)

    pred = model.predict(img, verbose=0)[0][0]

    if pred >= 0.5:
        predicted_class = 1
        confidence = pred * 100
    else:
        predicted_class = 0
        confidence = (1 - pred) * 100

    quality = CLASS_MAP[predicted_class]

    if quality == "Fresh":
        if confidence > 85:
            days = "5"
            status = "SAFE"
        elif confidence > 70:
            days = "3"
            status = "SAFE"
        else:
            days = "1"
            status = "SAFE"
    else:
        days = "0"
        status = "NOT_EATABLE"

    if send_serial and st.session_state.serial_ok:
        packet = f"{quality},{confidence:.2f},{days},{status}\n"
        st.session_state.esp32.write(packet.encode())

    return quality, confidence, days, status

# ---------------- UPLOAD IMAGE ----------------
if mode == "📁 Upload Image":
    file = st.file_uploader("Upload Fruit Image", ["jpg", "jpeg", "png"])
    if file:
        image = np.array(Image.open(file))
        st.image(image, width=300)

        q, c, d, s = predict(image)
        st.success(f"Quality: {q}")
        st.write(f"Confidence: {c:.2f}%")
        st.write(f"Shelf Life: {d}")
        st.write(f"Status: {s}")

# ---------------- CAMERA CAPTURE ----------------
elif mode == "📷 Capture Image":
    cam_img = st.camera_input("Capture Fruit Image")
    if cam_img:
        image = np.array(Image.open(cam_img))
        st.image(image, width=300)

        q, c, d, s = predict(image)
        st.success(f"Quality: {q}")
        st.write(f"Confidence: {c:.2f}%")
        st.write(f"Shelf Life: {d}")
        st.write(f"Status: {s}")

# ---------------- REAL-TIME STREAM ----------------
elif mode == "🎥 Real-time Video Stream":

    start = st.button("▶ Start Stream")
    stop = st.button("⏹ Stop Stream")

    frame_window = st.image([])
    result_box = st.empty()

    if "run_stream" not in st.session_state:
        st.session_state.run_stream = False

    if start:
        st.session_state.run_stream = True
    if stop:
        st.session_state.run_stream = False

    if st.session_state.run_stream:
        cap = cv2.VideoCapture(0)

        while st.session_state.run_stream:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            q, c, d, s = predict(rgb, send_serial=False)

            cv2.putText(
                frame,
                f"{q} ({c:.1f}%)",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0) if q == "Fresh" else (0, 0, 255),
                2
            )

            frame_window.image(frame, channels="BGR")

            result_box.markdown(
                f"""
                **Quality:** {q}  
                **Confidence:** {c:.2f}%  
                **Shelf Life:** {d}  
                **Status:** {s}
                """
            )

        cap.release()
