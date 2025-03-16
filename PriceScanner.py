import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
import os
import shutil
import cv2
import numpy as np

# ============================
# ✅ Helper Functions
# ============================

def get_tesseract_path():
    """
    Automatically detect and return the Tesseract path based on the operating system.
    """
    if os.name == "nt":  # Windows
        paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Users\USERNAME\AppData\Local\Tesseract-OCR\tesseract.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    elif os.path.exists("/usr/bin/tesseract"):  # Linux
        return "/usr/bin/tesseract"
    elif shutil.which("tesseract"):  # macOS/Linux Auto-Detection
        return shutil.which("tesseract")
    return None


def preprocess_image(img):
    """
    Preprocess the image to improve OCR accuracy.
    Steps: Convert to grayscale, sharpen, enhance contrast/brightness, and apply noise reduction.
    """
    img = img.convert("L")  # Convert to grayscale
    img = img.filter(ImageFilter.SHARPEN)  # Sharpen text
    img = ImageEnhance.Contrast(img).enhance(2.5)  # Increase contrast
    img = ImageEnhance.Brightness(img).enhance(1.2)  # Adjust brightness

    # Use OpenCV for noise reduction and thresholding
    img_cv = np.array(img)
    img_cv = cv2.GaussianBlur(img_cv, (5, 5), 0)
    img_cv = cv2.adaptiveThreshold(img_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return Image.fromarray(img_cv)


def extract_price_and_product(text):
    """
    Extract product name and price from OCR text using regex.
    """
    # Regex to match prices with 'R' prefix
    price_match = re.search(r'R\s?(\d{1,4}(\.\d{1,2})?)', text)
    price = float(price_match.group(1)) if price_match else None

    # Extract product name (first line before price)
    lines = text.split("\n")
    product_name = next((line.strip() for line in lines if "R" not in line and len(line.strip()) > 2), "")

    return product_name, price


# ============================
# ✅ Initialize Session State
# ============================

if 'total_price' not in st.session_state:
    st.session_state.total_price = 0.0
if 'scanned_items' not in st.session_state:
    st.session_state.scanned_items = []
if 'pending_price' not in st.session_state:
    st.session_state.pending_price = None
if 'pending_product' not in st.session_state:
    st.session_state.pending_product = None

# ============================
# ✅ Main App Logic
# ============================

st.title("🛒 Price Scanner App")

# 📢 Instruct users to use the back camera
st.warning("📢 **For best results, use the BACK camera and ensure good lighting.**")

# 📸 SCAN PRICE LABEL
st.markdown("<h3 style='color: #007BFF;'>📷 Take a picture of the price label</h3>", unsafe_allow_html=True)
img_file = st.camera_input("Use your **BACK camera** for better accuracy.")

if img_file is not None:
    try:
        # Load and preprocess the image
        image = Image.open(img_file)
        preprocessed_image = preprocess_image(image)

        # Extract text using Tesseract OCR
        custom_config = "--psm 8 -c tessedit_char_whitelist=0123456789.Rr"
        recognized_text = pytesseract.image_to_string(preprocessed_image, config=custom_config)

        st.subheader("📝 Recognized Text")
        st.text(recognized_text)

        # Extract product name and price
        product_name, price = extract_price_and_product(recognized_text)

        if price is not None:
            st.session_state.pending_price = price
            st.session_state.pending_product = product_name
        else:
            st.warning("⚠️ No valid price detected. Please enter it manually.")
    except Exception as e:
        st.error(f"❌ An error occurred while processing the image: {e}")

# 📌 CONFIRM OR EDIT PRICE & PRODUCT
if st.session_state.pending_price is not None:
    st.markdown("<h3 style='color: #007BFF;'>🔍 Review & Confirm Product & Price</h3>", unsafe_allow_html=True)

    product_name_input = st.text_input("Product Name:", value=st.session_state.pending_product)
    corrected_price = st.number_input(
        "Confirm or edit detected price:", min_value=0.00, format="%.2f", value=st.session_state.pending_price
    )

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

# 🗑️ CLEAR ALL BUTTON
if st.button("🗑️ Clear All"):
    st.session_state.total_price = 0.0
    st.session_state.scanned_items.clear()
    st.session_state.pending_price = None
    st.session_state.pending_product = None
    st.success("✅ Cleared all scanned items and reset total price.")

# ============================
# ✅ Styling with CSS
# ============================

st.markdown("""
<style>
.total-box {
    font-size: 24px;
    font-weight: bold;
    color: #007BFF;
    padding: 10px;
    border-radius: 5px;
    background-color: #f0f8ff;
    text-align: center;
}
.price-card {
    font-size: 18px;
    color: #333;
    padding: 5px 10px;
    margin: 5px 0;
    border-left: 5px solid #007BFF;
    background-color: #f9f9f9;
}
</style>
""", unsafe_allow_html=True)
