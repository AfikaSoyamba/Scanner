import streamlit as st
from PIL import Image
import pytesseract
import re
import os
import shutil

# ✅ Automatically detect Tesseract path across different environments
def get_tesseract_path():
    if os.name == "nt":  # Windows
        paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Users\USERNAME\AppData\Local\Tesseract-OCR\tesseract.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    elif os.path.exists("/usr/bin/tesseract"):  # ✅ Streamlit Cloud/Linux
        return "/usr/bin/tesseract"
    elif shutil.which("tesseract"):  # macOS/Linux Auto-Detection
        return shutil.which("tesseract")
    return None

# ✅ Set the detected Tesseract path
tesseract_path = get_tesseract_path()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"✅ Tesseract path set: {tesseract_path}")
else:
    raise FileNotFoundError("❌ Tesseract OCR not found! Install it and add it to PATH.")

# ✅ Initialize session state for total price and scanned items
if 'total_price' not in st.session_state:
    st.session_state.total_price = 0.0
if 'scanned_items' not in st.session_state:
    st.session_state.scanned_items = []
if 'pending_price' not in st.session_state:
    st.session_state.pending_price = None  # Holds price before user confirms

st.title("🛒 **SkenaMali** – Scan Shelf Prices!")
st.markdown("Scan price labels and track your grocery cost in **Rand (R)** before checkout.")

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

# 📌 CONFIRM OR EDIT PRICE
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
    st.write("🛍️ **Scanned Items:**")
    for item in st.session_state.scanned_items:
        st.write(f"- {item}")
