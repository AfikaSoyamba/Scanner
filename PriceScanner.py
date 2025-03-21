import streamlit as st
import time
import re
import pytesseract
from PIL import Image
from pyzbar.pyzbar import decode
import requests
import sqlite3
import hashlib
from dataclasses import dataclass
from typing import Optional
import numpy as np
import cv2

# Database initialization
def init_db():
    conn = sqlite3.connect('flashka.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS shopping_list
                 (id TEXT PRIMARY KEY, name TEXT, price REAL, quantity INTEGER, purchased INTEGER, image_url TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loyalty_cards
                 (id TEXT PRIMARY KEY, name TEXT, number TEXT, barcode TEXT, image BLOB)''')
    conn.commit()
    conn.close()
init_db()

# Security functions
def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()

# Data Classes
@dataclass
class ShoppingItem:
    id: str
    name: str
    price: float
    quantity: int
    purchased: bool
    image_url: Optional[str] = None

@dataclass
class LoyaltyCard:
    id: str
    name: str
    number: str
    barcode: Optional[str] = None
    image: Optional[bytes] = None

# Enhanced OCR with preprocessing
def perform_ocr(image_file) -> str:
    img = Image.open(image_file)
    img = np.array(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(thresh)
    return text

# Improved barcode scanning
def scan_barcode_from_image(image_file) -> Optional[str]:
    img = Image.open(image_file)
    img = img.convert('RGB')
    decoded_objects = decode(img)
    if decoded_objects:
        return decoded_objects[0].data.decode("utf-8")
    return None

# Product info lookup with error handling
def get_product_info(barcode: str) -> Optional[dict]:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == 1:
            product = data.get("product", {})
            return {
                "name": product.get("product_name", "Unknown Product"),
                "price": 0.0  # Price not available in API
            }
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: {str(e)}")
    except ValueError as e:
        st.error(f"Data Parsing Error: {str(e)}")
    return None

# Database operations
def load_data():
    conn = sqlite3.connect('flashka.db')
    shopping_list = [ShoppingItem(*row) for row in conn.execute('SELECT * FROM shopping_list')]
    loyalty_cards = [LoyaltyCard(*row) for row in conn.execute('SELECT * FROM loyalty_cards')]
    conn.close()
    return shopping_list, loyalty_cards

def save_shopping_list(items):
    conn = sqlite3.connect('flashka.db')
    conn.execute('DELETE FROM shopping_list')
    conn.executemany('INSERT INTO shopping_list VALUES (?, ?, ?, ?, ?, ?)', 
                    [(i.id, i.name, i.price, i.quantity, i.purchased, i.image_url) for i in items])
    conn.commit()
    conn.close()

def save_loyalty_cards(cards):
    conn = sqlite3.connect('flashka.db')
    conn.execute('DELETE FROM loyalty_cards')
    conn.executemany('INSERT INTO loyalty_cards VALUES (?, ?, ?, ?, ?)', 
                    [(c.id, c.name, hash_data(c.number), c.barcode, c.image) for c in cards])
    conn.commit()
    conn.close()

# Main app
def main():
    st.set_page_config(page_title="Flashka - Smart Shopping Assistant", page_icon="🛒", layout="wide")
    st.title("Flashka - Smart Shopping Assistant")

    # Load data from database
    if 'shopping_list' not in st.session_state:
        st.session_state.shopping_list, st.session_state.loyalty_cards = load_data()

    # Initialize session state variables
    for key in ["is_scanning", "is_scanning_barcode", "is_add_manually_modal_visible",
                "is_add_confirmation_modal_visible", "is_fetching_product_info", "is_edit_mode",
                "is_add_card_modal_visible", "expanded_card_id", "show_tutorial"]:
        if key not in st.session_state:
            st.session_state[key] = False

    for key in ["new_item_name", "new_item_price", "new_card_name", "new_card_number"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    if 'editing_item' not in st.session_state:
        st.session_state.editing_item = None

    if 'scanned_item' not in st.session_state:
        st.session_state.scanned_item = None

    # --- UI Components ---
    def render_shopping_list():
        st.subheader("Shopping List")
        total_price = sum(item.price * item.quantity for item in st.session_state.shopping_list if not item.purchased)
        st.markdown(f"**Total Price: ${total_price:.2f}**")
        
        for item in st.session_state.shopping_list:
            col1, col2, col3, col4 = st.columns([0.1, 0.6, 0.2, 0.1])
            with col1:
                if st.checkbox("", key=f"purchased-{item.id}", value=item.purchased):
                    toggle_item_purchased(item.id)
            with col2:
                if item.purchased:
                    st.markdown(f"~~{item.name}~~  ${item.price:.2f} x {item.quantity}")
                else:
                    st.write(f"{item.name}  ${item.price:.2f} x {item.quantity}")
            with col3:
                st.button("Edit", key=f"edit-{item.id}", on_click=lambda id=item.id: edit_item(id))
            with col4:
                st.button("Delete", key=f"delete-{item.id}", on_click=lambda id=item.id: delete_item(id))

    def render_loyalty_cards():
        st.subheader("Loyalty Cards")
        for card in st.session_state.loyalty_cards:
            with st.expander(card.name, expanded=(st.session_state.expanded_card_id == card.id)):
                st.write(f"Number: {'*' * 12}{card.number[-4:]}")
                if card.barcode:
                    st.code(card.barcode, language="text")
                if card.image:
                    st.image(card.image, caption="Card Image", width=300)
                st.button("Delete Card", key=f"delete-card-{card.id}", 
                         on_click=lambda id=card.id: delete_loyalty_card(id))

    # --- Event Handlers ---
    def add_item_to_shopping_list(item):
        existing = next((i for i in st.session_state.shopping_list if i.name == item.name), None)
        if existing:
            existing.quantity += item.quantity
        else:
            st.session_state.shopping_list.append(item)
        save_shopping_list(st.session_state.shopping_list)

    def delete_item(item_id):
        st.session_state.shopping_list = [i for i in st.session_state.shopping_list if i.id != item_id]
        save_shopping_list(st.session_state.shopping_list)
        st.experimental_rerun()

    def toggle_item_purchased(item_id):
        item = next(i for i in st.session_state.shopping_list if i.id == item_id)
        item.purchased = not item.purchased
        save_shopping_list(st.session_state.shopping_list)
        st.experimental_rerun()

    def edit_item(item_id):
        item = next(i for i in st.session_state.shopping_list if i.id == item_id)
        st.session_state.editing_item = item
        st.session_state.new_item_name = item.name
        st.session_state.new_item_price = str(item.price)
        st.session_state.is_edit_mode = True
        st.session_state.is_add_manually_modal_visible = True

    def add_loyalty_card(card):
        st.session_state.loyalty_cards.append(card)
        save_loyalty_cards(st.session_state.loyalty_cards)

    def delete_loyalty_card(card_id):
        st.session_state.loyalty_cards = [c for c in st.session_state.loyalty_cards if c.id != card_id]
        save_loyalty_cards(st.session_state.loyalty_cards)
        if st.session_state.expanded_card_id == card_id:
            st.session_state.expanded_card_id = None
        st.experimental_rerun()

    # --- Main UI ---
    if st.session_state.show_tutorial:
        with st.container():
            st.title("Welcome to Flashka!")
            st.write("Your smart shopping companion with:")
            st.markdown("""
            - ✅ Price scanning via OCR
            - 📦 Barcode product lookup
            - 🛒 Shopping list management
            - 🏷️ Loyalty card storage
            - 🔒 Secure data storage
            """)
            if st.button("Close Tutorial"):
                st.session_state.show_tutorial = False

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Shopping Actions")
        st.button("Scan Price 📸", on_click=lambda: st.session_state.update(is_scanning=True))
        st.button("Add Manually ✍️", on_click=lambda: st.session_state.update(is_add_manually_modal_visible=True))
        st.button("Scan Barcode 🧾", on_click=lambda: st.session_state.update(is_scanning_barcode=True))

        render_shopping_list()

    with col2:
        st.subheader("Loyalty Cards")
        st.button("Add Card 📇", on_click=lambda: st.session_state.update(is_add_card_modal_visible=True))
        render_loyalty_cards()

    # --- Camera Inputs ---
    if st.session_state.is_scanning:
        with st.container():
            st.subheader("Price Scanner")
            camera_image = st.camera_input("Capture price tag")
            if camera_image:
                ocr_text = perform_ocr(camera_image)
                price_match = re.search(r'(\d+[\.,]\d{2})', ocr_text)
                if price_match:
                    price = float(price_match.group(1).replace(',', '.'))
                    st.session_state.scanned_item = ShoppingItem(
                        id=str(time.time()),
                        name="Scanned Item",
                        price=price,
                        quantity=1,
                        purchased=False
                    )
                    st.session_state.is_add_confirmation_modal_visible = True
                else:
                    st.error("No valid price found")
                st.session_state.is_scanning = False

    if st.session_state.is_scanning_barcode:
        with st.container():
            st.subheader("Barcode Scanner")
            barcode_image = st.camera_input("Capture barcode")
            if barcode_image:
                barcode = scan_barcode_from_image(barcode_image)
                if barcode:
                    product = get_product_info(barcode)
                    if product:
                        st.session_state.scanned_item = ShoppingItem(
                            id=barcode,
                            name=product['name'],
                            price=product['price'],
                            quantity=1,
                            purchased=False
                        )
                    else:
                        st.session_state.scanned_item = ShoppingItem(
                            id=barcode,
                            name="Unknown Product",
                            price=0.0,
                            quantity=1,
                            purchased=False
                        )
                    st.session_state.is_add_confirmation_modal_visible = True
                else:
                    st.error("No barcode detected")
                st.session_state.is_scanning_barcode = False

    # --- Modals ---
    if st.session_state.is_add_manually_modal_visible:
        with st.form("add_item_form"):
            st.subheader("Edit Item" if st.session_state.is_edit_mode else "Add New Item")
            name = st.text_input("Item Name", value=st.session_state.new_item_name)
            price = st.text_input("Price", value=st.session_state.new_item_price)
            
            if st.form_submit_button("Update" if st.session_state.is_edit_mode else "Add"):
                if not name or not price:
                    st.error("Please fill all fields")
                else:
                    try:
                        price_val = float(price.replace(',', '.'))
                        if st.session_state.is_edit_mode:
                            index = next(i for i, item in enumerate(st.session_state.shopping_list) 
                                        if item.id == st.session_state.editing_item.id)
                            st.session_state.shopping_list[index].name = name
                            st.session_state.shopping_list[index].price = price_val
                        else:
                            new_item = ShoppingItem(
                                id=str(time.time()),
                                name=name,
                                price=price_val,
                                quantity=1,
                                purchased=False
                            )
                            add_item_to_shopping_list(new_item)
                        st.session_state.is_add_manually_modal_visible = False
                        st.session_state.is_edit_mode = False
                        st.experimental_rerun()
                    except ValueError:
                        st.error("Invalid price format")

    if st.session_state.is_add_confirmation_modal_visible:
        with st.container():
            st.subheader("Confirm Item")
            item = st.session_state.scanned_item
            st.write(f"**Name:** {item.name}")
            st.write(f"**Price:** ${item.price:.2f}")
            st.write(f"**Quantity:** {item.quantity}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Add to List"):
                    add_item_to_shopping_list(item)
                    st.session_state.scanned_item = None
                    st.session_state.is_add_confirmation_modal_visible = False
                    st.experimental_rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.scanned_item = None
                    st.session_state.is_add_confirmation_modal_visible = False

    if st.session_state.is_add_card_modal_visible:
        with st.form("add_card_form"):
            st.subheader("Add Loyalty Card")
            name = st.text_input("Card Name")
            number = st.text_input("Card Number")
            image = st.file_uploader("Upload Card Image", type=["jpg", "png"])
            barcode = st.text_input("Barcode (Optional)")
            
            if st.form_submit_button("Save Card"):
                if not name or not number:
                    st.error("Please fill required fields")
                else:
                    new_card = LoyaltyCard(
                        id=str(time.time()),
                        name=name,
                        number=number,
                        barcode=barcode,
                        image=image.getvalue() if image else None
                    )
                    add_loyalty_card(new_card)
                    st.session_state.is_add_card_modal_visible = False
                    st.experimental_rerun()

if __name__ == "__main__":
    main()
