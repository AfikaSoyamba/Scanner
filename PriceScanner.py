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


def preprocess_image_for_prices(img):
    """
    Preprocess the image specifically for recognizing prices with 'R' symbols.
    """
    # Convert to grayscale
    img = img.convert("L")
    
    # Resize for consistency (optional)
    img = img.resize((1280, 720))
    
    # Sharpen and enhance contrast/brightness
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(3.0)  # Stronger contrast for better separation
    img = ImageEnhance.Brightness(img).enhance(1.5)  # Brighten the image
    
    # Convert to OpenCV format
    img_cv = np.array(img)
    
    # Apply Gaussian blur and adaptive thresholding
    img_cv = cv2.GaussianBlur(img_cv, (5, 5), 0)
    img_cv = cv2.adaptiveThreshold(img_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Morphological operations to clean up noise
    kernel = np.ones((3, 3), np.uint8)
    img_cv = cv2.morphologyEx(img_cv, cv2.MORPH_CLOSE, kernel)
    
    return Image.fromarray(img_cv)


def extract_price_with_r(text):
    """
    Extract prices starting with 'R' using regex.
    Handles formats like "R123.45", "R 123.45", "R1,234.56".
    """
    # Regex to match prices with 'R' prefix
    price_match = re.search(r'R\s?([\d,]+(\.\d{1,2})?)', text)
    if price_match:
        price_str = price_match.group(1).replace(",", "")  # Remove commas
        try:
            return float(price_str)
        except ValueError:
            return None
    return None


def crop_to_safe_area(image, safe_area_ratio=0.6):
    """
    Crop the image to a central "safe area" defined by a ratio of the original image size.
    """
    width, height = image.size
    safe_width = int(width * safe_area_ratio)
    safe_height = int(height * safe_area_ratio)
    
    left = (width - safe_width) // 2
    top = (height - safe_height) // 2
    right = left + safe_width
    bottom = top + safe_height
    
    return image.crop((left, top, right, bottom))


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

# 📢 Instruct users to use the back camera and position the label in the safe area
st.warning("📢 **For best results:**")
st.markdown("""
- Use the BACK camera.
- Position the price label within the **SAFE AREA** (centered rectangle).
- Ensure good lighting and avoid shadows.
""")

# 📸 SCAN PRICE LABEL
st.markdown("<h3 style='color: #007BFF;'>📷 Take a picture of the price label</h3>", unsafe_allow_html=True)
img_file = st.camera_input("Use your **BACK camera** for better accuracy.")

if img_file is not None:
    try:
        # Load the image
        image = Image.open(img_file)

        # Display the full image for debugging
        st.subheader("🖼️ Full Captured Image")
        st.image(image, caption="Full Captured Image", use_column_width=True)

        # Crop the image to the safe area
        safe_area_ratio = 0.6  # Safe area covers 60% of the image
        cropped_image = crop_to_safe_area(image, safe_area_ratio)

        # Display the cropped image
        st.subheader("🖼️ Cropped Image (Safe Area)")
        st.image(cropped_image, caption="Cropped Image (Safe Area)", use_column_width=True)

        # Preprocess the cropped image for price recognition
        preprocessed_image = preprocess_image_for_prices(cropped_image)

        # Display the preprocessed image
        st.subheader("🖼️ Preprocessed Image")
        st.image(preprocessed_image, caption="Preprocessed Image", use_column_width=True)

        # Extract text using Tesseract OCR (optimized for prices with 'R')
        custom_config = "--psm 6 -c tessedit_char_whitelist=0123456789.Rr,"
        recognized_text = pytesseract.image_to_string(preprocessed_image, config=custom_config)

        st.subheader("📝 Recognized Text")
        st.text(recognized_text)

        if not recognized_text.strip():
            st.warning("⚠️ No text detected. Please try again with better positioning or lighting.")
        else:
            # Extract price with 'R' symbol
            price = extract_price_with_r(recognized_text)

            if price is not None:
                st.session_state.pending_price = price
                st.success(f"✅ Detected price: R{price:.2f}")
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
