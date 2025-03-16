import streamlit as st
from PIL import Image
import pytesseract
import re
import os

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

st.title("🛒 Grocery Price Scanner (Rand)")
st.markdown("Scan shelf price labels and track your grocery cost in **South African Rand (R)** before checkout.")

# Capture image using Streamlit's camera input
img_file = st.camera_input("Take a picture of the price label")

if img_file is not None:
    # Open and display the captured image
    image = Image.open(img_file)
    st.image(image, caption="Captured Image", use_container_width=True)

    # Extract text using Tesseract OCR
    recognized_text = pytesseract.image_to_string(image)
    st.subheader("Recognized Text:")
    st.text(recognized_text)

    # Use regex to extract price values in Rands (supporting formats like R99.99, 99.99, etc.)
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

# If a price was extracted, allow the user to confirm or edit it
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

# Display the running total and list of scanned prices
st.markdown("## 🏷️ Running Total")
st.write(f"**Total Price:** **R{st.session_state.total_price:.2f}**")

if st.session_state.scanned_items:
    st.write("Scanned Prices:", st.session_state.scanned_items)
