import streamlit as st
import tensorflow as tf
import cv2
import numpy as np
from PIL import Image
import serial
import time

# ---------------- CONFIG ----------------
SERIAL_PORT = "COM7"       # change if needed
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
    "Select Input Method",
    ["📁 Upload Image", "📷 Live Camera"],
    horizontal=True
)

# ---------------- PREDICTION FUNCTION ----------------
def predict_and_send(image_np):
    img = cv2.resize(image_np, (IMG_SIZE, IMG_SIZE))
    img = img / 255.0
    img = np.expand_dims(img, axis=0)

    pred = model.predict(img)[0][0]

    if pred >= 0.5:
        predicted_class = 1
        confidence = pred * 100
    else:
        predicted_class = 0
        confidence = (1 - pred) * 100

    quality = CLASS_MAP[predicted_class]

    if quality == "Fresh":
        days = "5-7"
        status = "SAFE"
        st.success("🍏 Fruit is Fresh")
    else:
        days = "0"
        status = "NOT_EATABLE"
        st.error("🍎 Fruit is Rotten")

    st.subheader("🔍 Prediction Result")
    st.write(f"Quality : {quality}")
    st.write(f"Confidence : {confidence:.2f}%")
    st.write(f"Shelf Life : {days}")
    st.write(f"Status : {status}")

    # Send to ESP32
    if st.session_state.serial_ok:
        data_packet = f"{quality},{confidence:.2f},{days},{status}\n"
        st.session_state.esp32.write(data_packet.encode())
        st.info("📤 Data Sent to ESP32")

# ---------------- UPLOAD MODE ----------------
if mode == "📁 Upload Image":
    uploaded_file = st.file_uploader(
        "Upload Fruit Image",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        image_np = np.array(image)

        st.image(image, caption="Uploaded Image", width=300)
        predict_and_send(image_np)

# ---------------- LIVE CAMERA MODE ----------------
elif mode == "📷 Live Camera":
    camera_image = st.camera_input("Capture Image from Camera")

    if camera_image is not None:
        image = Image.open(camera_image)
        image_np = np.array(image)

        st.image(image, caption="Captured Image", width=300)
        predict_and_send(image_np)
