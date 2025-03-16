import streamlit as st
from PIL import Image
import pytesseract
import re
import os
import speech_recognition as sr

# Ensure Tesseract is installed and set the correct path if needed
if os.name == "nt":  # Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize session state for total price and scanned items
if 'total_price' not in st.session_state:
    st.session_state.total_price = 0.0
if 'scanned_items' not in st.session_state:
    st.session_state.scanned_items = []
if 'pending_price' not in st.session_state:
    st.session_state.pending_price = None  # Holds price before user confirms

st.title("🛒 **SkenaMali** – Scan or Speak Prices!")
st.markdown("Scan price labels **or** use your **voice** to track your grocery cost in **Rand (R)** before checkout.")

# 📸 SCAN PRICE LABEL
img_file = st.camera_input("📷 Take a picture of the price label")

if img_file is not None:
    # Open and display the captured image
    image = Image.open(img_file)
    st.image(image, caption="📸 Captured Image", use_container_width=True)

    # Extract text using Tesseract OCR
    recognized_text = pytesseract.image_to_string(image)
    st.subheader("📝 Recognized Text:")
    st.text(recognized_text)

    # Use regex to extract price values (R99.99, 99.99, etc.)
    match = re.search(r'R?\s?(\d{1,4}(\.\d{1,2})?)', recognized_text)

    if match:
        price_str = match.group(1)  # Extract only the numeric value
        try:
            price = float(price_str)
            st.session_state.pending_price = price  # Store extracted price for user confirmation
        except ValueError:
            st.session_state.pending_price = None
            st.error("⚠️ Error converting the recognized text to a valid number.")
    else:
        st.session_state.pending_price = None
        st.warning("⚠️ No valid price detected. Please enter it manually.")

# 🎤 VOICE INPUT FOR PRICE
st.subheader("🎙️ Speak an Item & Price")
st.markdown("Say the **item name** and **price**, e.g., _'Milk 22.50'_. The system will add it automatically.")

if st.button("🎤 Start Voice Input"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Speak the item name and price.")
        try:
            audio = recognizer.listen(source, timeout=5)  # Capture voice input
            voice_text = recognizer.recognize_google(audio)  # Convert speech to text
            st.success(f"🗣️ You said: **{voice_text}**")

            # Extract price and item name
            match = re.search(r'(\d{1,4}(\.\d{1,2})?)', voice_text)  # Detect price
            if match:
                price = float(match.group(1))
                item_name = re.sub(r'\d{1,4}(\.\d{1,2})?', '', voice_text).strip()  # Remove price from text
                st.session_state.total_price += price
                st.session_state.scanned_items.append(f"{item_name} - R{price:.2f}")
                st.success(f"✅ Added: **{item_name}** for **R{price:.2f}**")
            else:
                st.warning("⚠️ No valid price detected. Please try again.")

        except sr.UnknownValueError:
            st.error("⚠️ Sorry, I couldn't understand. Please try again.")
        except sr.RequestError:
            st.error("⚠️ Error connecting to the speech service. Try again later.")

# 📌 CONFIRM OR EDIT PRICE (for Scanned Input)
if st.session_state.pending_price is not None:
    st.markdown("## 🔍 Review & Confirm Price")
    corrected_price = st.number_input(
        "Confirm or edit the detected price:", 
        min_value=0.00, 
        format="%.2f", 
        value=st.session_state.pending_price
    )
    
    if st.button("✅ Add to Total"):
        st.session_state.total_price += corrected_price
        st.session_state.scanned_items.append(f"R{corrected_price:.2f}")
        st.success(f"✅ Price **R{corrected_price:.2f}** added to your total.")
        st.session_state.pending_price = None  # Clear pending price after confirmation

# 🏷️ DISPLAY TOTAL PRICE
st.markdown("## 🏷️ **Running Total**")
st.write(f"**Total Price:** **R{st.session_state.total_price:.2f}**")

if st.session_state.scanned_items:
    st.write("🛍️ **Scanned & Spoken Items:**")
    for item in st.session_state.scanned_items:
        st.write(f"- {item}")

