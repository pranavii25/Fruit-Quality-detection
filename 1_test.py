import streamlit as st
import tensorflow as tf
import cv2
import numpy as np
from PIL import Image
import serial
import time

SERIAL_PORT = "COM7"
BAUD_RATE = 9600

# ---------- SERIAL INIT (ONCE) ----------
if "esp32" not in st.session_state:
    try:
        st.session_state.esp32 = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        st.session_state.serial_ok = True
    except Exception as e:
        st.session_state.serial_ok = False
        st.session_state.serial_error = str(e)

st.title("🍎 Fruit Quality Detection with ESP32")

if st.session_state.serial_ok:
    st.success("✅ ESP32 Connected via Serial")
else:
    st.error(f"❌ ESP32 NOT Connected: {st.session_state.serial_error}")

# ---------- LOAD MODEL ----------
@st.cache_resource
def load_model():
    return tf.keras.models.load_model("fruit_quality_model.h5")

model = load_model()

CLASS_MAP = {0: "Fresh", 1: "Rotten"}

# ---------- IMAGE UPLOAD ----------
uploaded_file = st.file_uploader(
    "Upload Fruit Image",
    type=["jpg", "jpeg", "png"]
)

# ---------- PREDICTION BLOCK ----------
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", width=300)

    img = np.array(image)
    img = cv2.resize(img, (224, 224))
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

    # ---------- DISPLAY ----------
    st.subheader("🔍 Prediction Result")
    st.write(f"Quality : {quality}")
    st.write(f"Confidence : {confidence:.2f}%")
    st.write(f"Shelf Life (Days) : {days}")
    st.write(f"Status : {status}")

    # ---------- SEND TO ESP32 (ONLY HERE) ----------
    if st.session_state.serial_ok:
        data_packet = f"{quality},{confidence:.2f},{days},{status}\n"
        st.session_state.esp32.write(data_packet.encode())
        st.info("📤 Data Sent to ESP32")
        st.code(data_packet)
