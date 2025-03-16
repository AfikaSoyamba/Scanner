import streamlit as st
from PIL import Image
import pytesseract
import re

# Initialize session state for total price and scanned items
if 'total_price' not in st.session_state:
    st.session_state.total_price = 0.0
if 'scanned_items' not in st.session_state:
    st.session_state.scanned_items = []

st.title("Price Scanner App")
st.markdown("Capture a displayed price using your camera. The app extracts the price and updates your running total.")

# Capture image using Streamlit's camera input
img_file = st.camera_input("Take a picture of the price label")

if img_file is not None:
    # Open and display the captured image
    image = Image.open(img_file)
    st.image(image, caption="Captured Image", use_column_width=True)
    
    # Extract text using Tesseract OCR
    recognized_text = pytesseract.image_to_string(image)
    st.write("Recognized Text:")
    st.text(recognized_text)
    
    # Use regex to extract a price value from the recognized text
    match = re.search(r'\d+(\.\d{1,2})?', recognized_text)
    if match:
        price_str = match.group(0)
        try:
            price = float(price_str)
            st.session_state.total_price += price
            st.session_state.scanned_items.append(price)
            st.success(f"Price ${price:.2f} added to your total.")
        except ValueError:
            st.error("Error converting the recognized text to a valid number.")
    else:
        st.error("No valid price found in the captured image.")

# Display the running total and list of scanned prices
st.markdown("## Running Total")
st.write(f"Total Price: ${st.session_state.total_price:.2f}")
if st.session_state.scanned_items:
    st.write("Scanned Prices:", st.session_state.scanned_items)
