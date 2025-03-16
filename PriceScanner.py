import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
import os
import shutil
import cv2
import numpy as np

# ✅ Automatically detect Tesseract path
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
    pytesseract.pytesseract_cmd = tesseract_path
else:
    raise FileNotFoundError("❌ Tesseract OCR not found! Install it and add it to PATH.")

# ✅ Initialize session state
if 'total_price' not in st.session_state:
    st.session_state.total_price = 0.0
if 'scanned_items' not in st.session_state:
    st.session_state.scanned_items = []
if 'pending_price' not in st.session_state:
    st.session_state.pending_price = None
if 'last_image' not in st.session_state:
    st.session_state.last_image = None

# 📢 **IMPORTANT: Instruct Users to Use the Back Camera**
st.warning("📢 **For best results, switch to the BACK camera and ensure good lighting.**")

# 📸 SCAN PRICE LABEL
st.markdown("<h3 style='color: #007BFF;'>📷 Take a picture of the price label</h3>", unsafe_allow_html=True)
img_file = st.camera_input("Use your **BACK camera** for better accuracy.")

if img_file is not None:
    image = Image.open(img_file)

    # ✅ IMAGE PREPROCESSING FOR BETTER OCR ACCURACY
    def preprocess_image(img):
        img = img.convert("L")  # Convert to grayscale
        img = img.filter(ImageFilter.SHARPEN)  # Sharpen text
        img = ImageEnhance.Contrast(img).enhance(3)  # Increase contrast
        img = ImageEnhance.Brightness(img).enhance(1.2)  # Adjust brightness
        return img

    image = preprocess_image(image)

    # ✅ Use OpenCV to remove noise & improve edge detection
    img_cv = np.array(image)
    img_cv = cv2.GaussianBlur(img_cv, (3, 3), 0)
    img_cv = cv2.adaptiveThreshold(img_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    image = Image.fromarray(img_cv)

    # Extract text using Tesseract OCR with improved settings
    custom_config = "--psm 6 -c tessedit_char_whitelist=0123456789.Rr"
    recognized_text = pytesseract.image_to_string(image, config=custom_config)

    st.subheader("📝 Recognized Text")
    st.text(recognized_text)

    # ✅ Extract price with "R" before the number
    match = re.search(r'R\s?(\d{1,4}(\.\d{1,2})?)', recognized_text)

    # ✅ Extract product name (first line before price)
    lines = recognized_text.split("\n")
    product_name = ""
    for line in lines:
        if "R" not in line and len(line.strip()) > 2:
            product_name = line.strip()
            break

    if match:
        price_str = match.group(1)
        try:
            price = float(price_str)
            st.session_state.pending_price = price
            st.session_state.pending_product = product_name
        except ValueError:
            st.session_state.pending_price = None
            st.session_state.pending_product = None
            st.error("⚠️ Error converting text to a number.")
    else:
        st.session_state.pending_price = None
        st.session_state.pending_product = None
        st.warning("⚠️ No valid price detected. Please enter it manually.")

    # ✅ Clear the last image immediately after processing
    st.session_state.last_image = None

# 📌 CONFIRM OR EDIT PRICE & PRODUCT
if st.session_state.pending_price is not None:
    st.markdown("<h3 style='color: #007BFF;'>🔍 Review & Confirm Product & Price</h3>", unsafe_allow_html=True)

    product_name_input = st.text_input("Product Name:", value=st.session_state.pending_product)
    corrected_price = st.number_input("Confirm or edit detected price:", min_value=0.00, format="%.2f", value=st.session_state.pending_price)

    if st.button("✅ Add to List"):
        st.session_state.total_price += corrected_price
        st.session_state.scanned_items.append(f"{product_name_input} - R{corrected_price:.2f}")
        st.success(f"✅ Added: **{product_name_input}** for **R{corrected_price:.2f}**")
        st.session_state.pending_price = None
        st.session_state.pending_product = None

# 🏷️ DISPLAY TOTAL PRICE
st.markdown("<h3 style='color: #007BFF;'>🏷️ Total</h3>", unsafe_allow_html=True)
st.markdown(f"<div class='total-box'>Total: R{st.session_state.total_price:.2f}</div>", unsafe_allow_html=True)

# 📌 LIST OF SCANNED ITEMS
if st.session_state.scanned_items:
    st.markdown("<h3 style='color: #007BFF;'>🛍️ Scanned Items</h3>", unsafe_allow_html=True)
    for item in st.session_state.scanned_items:
        st.markdown(f"<div class='price-card'>✅ {item}</div>", unsafe_allow_html=True)
