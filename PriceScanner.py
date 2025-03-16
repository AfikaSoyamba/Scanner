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
else:
    raise FileNotFoundError("❌ Tesseract OCR not found! Install it and add it to PATH.")

# ✅ Initialize session state for total price, scanned items, and image
if 'total_price' not in st.session_state:
    st.session_state.total_price = 0.0
if 'scanned_items' not in st.session_state:
    st.session_state.scanned_items = []
if 'pending_price' not in st.session_state:
    st.session_state.pending_price = None
if 'last_image' not in st.session_state:
    st.session_state.last_image = None

# 🟢 Apply custom styles
st.markdown(
    """
    <style>
        body { background-color: #f8f9fa; }
        .stButton>button { width: 100%; font-size: 20px; padding: 10px; }
        .stTextInput>div>div>input { font-size: 18px; text-align: center; }
        .price-card { background: white; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
        .total-box { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .scan-box { text-align: center; padding: 20px; border-radius: 10px; background: #007BFF; color: white; font-size: 20px; }
        .scan-box:hover { background: #0056b3; }
    </style>
    """,
    unsafe_allow_html=True
)

# 📌 HEADER DESIGN
st.markdown("<h1 style='text-align: center; color: #007BFF;'>🛒 SkenaMali</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: #555;'>Scan shelf prices and track your grocery total in Rands</p>", unsafe_allow_html=True)

# 📸 SCAN PRICE LABEL
st.markdown("<div class='scan-box'>📷 Take a picture of the price label</div>", unsafe_allow_html=True)
img_file = st.camera_input("")

if img_file is not None:
    # Open and display the captured image (temporarily)
    image = Image.open(img_file)
    st.session_state.last_image = image  # Save the last image for clarity
    st.image(image, caption="📸 Scanned Image", use_container_width=True)

    # Extract text using Tesseract OCR
    recognized_text = pytesseract.image_to_string(image)
    st.markdown("<h3 style='color: #007BFF;'>📝 Recognized Text</h3>", unsafe_allow_html=True)
    st.text(recognized_text)

    # ✅ Extract price in Rand (Rxx.xx format)
    match = re.search(r'R\s?(\d{1,4}(\.\d{1,2})?)', recognized_text)

    # ✅ Extract product name (Assume first non-price text is product)
    lines = recognized_text.split("\n")
    product_name = ""
    for line in lines:
        if not re.search(r'R\s?(\d{1,4}(\.\d{1,2})?)', line) and len(line.strip()) > 2:
            product_name = line.strip()
            break  # Stop after finding the first valid product name

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

    # ✅ Clear the last image after processing
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
