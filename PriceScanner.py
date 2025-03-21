import streamlit as st
import time
import re
import pytesseract
from PIL import Image
from pyzbar.pyzbar import decode
import requests
from dataclasses import dataclass
from typing import Optional

# Data Classes for shopping items and loyalty cards
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
    image: Optional[str] = None

# Real OCR implementation using pytesseract
def perform_ocr(image_file) -> str:
    img = Image.open(image_file)
    text = pytesseract.image_to_string(img)
    return text

# Real barcode scanning using pyzbar
def scan_barcode_from_image(image_file) -> Optional[str]:
    img = Image.open(image_file)
    decoded_objects = decode(img)
    if decoded_objects:
        return decoded_objects[0].data.decode("utf-8")
    return None

# Fetch product info using the Open Food Facts API
def get_product_info(barcode: str) -> Optional[dict]:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data.get("product", {})
                name = product.get("product_name", "Unknown Product")
                # Price information is generally not available; default to 0.
                price = 0.0
                return {"name": name, "price": price}
    except Exception as e:
        st.error(f"Error fetching product info: {e}")
    return None

def main():
    st.title("Flashka - Real Price Scanner & Shopping List")
    
    # Initialize session state
    for key in ["is_scanning", "is_scanning_barcode", "shopping_list", "loyalty_cards",
                "is_add_manually_modal_visible", "new_item_name", "new_item_price", "scanned_item",
                "is_add_confirmation_modal_visible", "is_fetching_product_info", "scanned_barcode",
                "is_edit_mode", "editing_item", "is_add_card_modal_visible", "new_card_name", "new_card_number",
                "expanded_card_id", "show_tutorial"]:
        if key not in st.session_state:
            if key in ["shopping_list", "loyalty_cards"]:
                st.session_state[key] = []
            elif key in ["is_scanning", "is_scanning_barcode", "is_add_manually_modal_visible",
                         "is_add_confirmation_modal_visible", "is_fetching_product_info",
                         "is_edit_mode", "is_add_card_modal_visible"]:
                st.session_state[key] = False
            elif key in ["new_item_name", "new_item_price", "new_card_name", "new_card_number"]:
                st.session_state[key] = ""
            elif key == "expanded_card_id":
                st.session_state[key] = None
            elif key == "show_tutorial":
                st.session_state[key] = True
            elif key in ["scanned_item", "scanned_barcode"]:
                st.session_state[key] = None

    # --- Helper Functions ---
    def add_item_to_shopping_list(item: ShoppingItem) -> None:
        existing_item_index = next(
            (index for index, list_item in enumerate(st.session_state.shopping_list)
             if list_item.name == item.name), -1
        )
        if existing_item_index > -1:
            st.session_state.shopping_list[existing_item_index].quantity += item.quantity
        else:
            st.session_state.shopping_list.append(item)

    def delete_item_from_shopping_list(item_id: str) -> None:
        st.session_state.shopping_list = [
            item for item in st.session_state.shopping_list if item.id != item_id
        ]

    def toggle_item_purchased(item_id: str) -> None:
        st.session_state.shopping_list = [
            item if item.id != item_id else ShoppingItem(
                id=item.id,
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                purchased=not item.purchased,
                image_url=item.image_url
            )
            for item in st.session_state.shopping_list
        ]

    def add_loyalty_card(card: LoyaltyCard) -> None:
        st.session_state.loyalty_cards.append(card)

    def delete_loyalty_card(card_id: str) -> None:
        st.session_state.loyalty_cards = [
            card for card in st.session_state.loyalty_cards if card.id != card_id
        ]
        if st.session_state.expanded_card_id == card_id:
            st.session_state.expanded_card_id = None

    # --- UI Components ---
    def render_shopping_list() -> None:
        st.subheader("Shopping List")
        total_price = sum(item.price * item.quantity for item in st.session_state.shopping_list)
        st.write(f"Total Price: ${total_price:.2f}")
        for item in st.session_state.shopping_list:
            col1, col2, col3, col4 = st.columns([0.1, 0.6, 0.2, 0.1])
            with col1:
                if st.checkbox("", key=f"purchased-{item.id}", value=item.purchased):
                    toggle_item_purchased(item.id)
            with col2:
                st.write(f"{item.name}  ${item.price:.2f} x {item.quantity}")
            with col3:
                if st.button("Edit", key=f"edit-{item.id}"):
                    st.session_state.editing_item = item
                    st.session_state.new_item_name = item.name
                    st.session_state.new_item_price = str(item.price)
                    st.session_state.is_edit_mode = True
                    st.session_state.is_add_manually_modal_visible = True
            with col4:
                if st.button("Delete", key=f"delete-{item.id}"):
                    delete_item_from_shopping_list(item.id)
                    st.experimental_rerun()

    def render_loyalty_cards() -> None:
        st.subheader("Loyalty Cards")
        for card in st.session_state.loyalty_cards:
            with st.expander(card.name, expanded=(st.session_state.expanded_card_id == card.id)):
                st.write(f"Number: {card.number}")
                if card.barcode:
                    st.write(f"Barcode: {card.barcode}")
                if card.image:
                    st.image(card.image, caption="Card Image", width=300)
                if st.button("Delete Card", key=f"delete-card-{card.id}"):
                    delete_loyalty_card(card.id)
                    st.experimental_rerun()

    # --- Event Handlers ---
    def handle_scan_price():
        st.session_state.is_scanning = True

    def handle_scan_barcode():
        st.session_state.is_scanning_barcode = True

    def handle_add_scanned_item_to_cart() -> None:
        if st.session_state.scanned_item:
            add_item_to_shopping_list(st.session_state.scanned_item)
            st.session_state.scanned_item = None
            st.session_state.is_add_confirmation_modal_visible = False

    def handle_add_manually() -> None:
        if not st.session_state.new_item_name.strip() or not st.session_state.new_item_price.strip():
            st.error("Please enter both item name and price.")
            return
        try:
            price = float(st.session_state.new_item_price.replace(",", "."))
        except ValueError:
            st.error("Invalid price format. Please enter a valid number.")
            return
        if price <= 0:
            st.error("Invalid price. Please enter a value greater than zero.")
            return
        new_item = ShoppingItem(
            id=f"manual-{time.time()}",
            name=st.session_state.new_item_name,
            price=price,
            quantity=1,
            purchased=False,
            image_url=None
        )
        add_item_to_shopping_list(new_item)
        st.session_state.new_item_name = ""
        st.session_state.new_item_price = ""
        st.session_state.is_add_manually_modal_visible = False

    def handle_update_item() -> None:
        if not st.session_state.new_item_name.strip() or not st.session_state.new_item_price.strip():
            st.error("Please enter both item name and price.")
            return
        try:
            price = float(st.session_state.new_item_price.replace(",", "."))
        except ValueError:
            st.error("Invalid price format. Please enter a valid number.")
            return
        if price <= 0:
            st.error("Invalid price. Please enter a value greater than zero.")
            return
        if st.session_state.editing_item:
            st.session_state.shopping_list = [
                item if item.id != st.session_state.editing_item.id else ShoppingItem(
                    id=item.id,
                    name=st.session_state.new_item_name,
                    price=price,
                    quantity=item.quantity,
                    purchased=item.purchased,
                    image_url=item.image_url
                )
                for item in st.session_state.shopping_list
            ]
            st.session_state.editing_item = None
        st.session_state.new_item_name = ""
        st.session_state.new_item_price = ""
        st.session_state.is_edit_mode = False
        st.session_state.is_add_manually_modal_visible = False

    # --- Main UI ---
    if st.session_state.show_tutorial:
        with st.container():
            st.title("Welcome to Flashka!")
            st.write("Flashka helps you scan prices using OCR, manage your shopping list, and store loyalty cards.")
            st.subheader("Tutorial")
            st.write("1. Scan Prices: Capture an image of a price tag using your camera.")
            st.write("2. Scan Barcode: Capture an image of a barcode to retrieve product information.")
            st.write("3. Manage your shopping list and loyalty cards.")
            if st.button("Close Tutorial"):
                st.session_state.show_tutorial = False

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Shopping")
        if st.button("Scan Price"):
            handle_scan_price()
        if st.button("Add Manually"):
            st.session_state.is_add_manually_modal_visible = True
        if st.button("Scan Barcode"):
            handle_scan_barcode()
        render_shopping_list()
    with col2:
        st.subheader("Cards")
        if st.button("Add Card"):
            st.session_state.is_add_card_modal_visible = True
        render_loyalty_cards()

    # --- Camera Inputs for Real OCR and Barcode Scanning ---
    if st.session_state.is_scanning:
        camera_image = st.camera_input("Capture an image for OCR")
        if camera_image is not None:
            ocr_result = perform_ocr(camera_image)
            st.write("OCR Result:", ocr_result)
            price_match = re.search(r"(\d+[,.]\d{2})", ocr_result)
            if price_match:
                price_str = price_match.group(1).replace(",", ".")
                try:
                    price = float(price_str)
                    st.session_state.scanned_item = ShoppingItem(
                        id=f"temp-{time.time()}",
                        name="Scanned Item",
                        price=price,
                        quantity=1,
                        purchased=False,
                        image_url=None
                    )
                    st.session_state.is_add_confirmation_modal_visible = True
                except ValueError:
                    st.error("Invalid price format detected.")
            else:
                st.error("No price found in captured image.")
            st.session_state.is_scanning = False

    if st.session_state.is_scanning_barcode:
        barcode_image = st.camera_input("Capture an image for Barcode scanning")
        if barcode_image is not None:
            barcode_data = scan_barcode_from_image(barcode_image)
            if barcode_data:
                st.write("Barcode detected:", barcode_data)
                st.session_state.scanned_barcode = barcode_data
                st.session_state.is_fetching_product_info = True
                product_info = get_product_info(barcode_data)
                st.session_state.is_fetching_product_info = False
                if product_info:
                    st.session_state.scanned_item = ShoppingItem(
                        id=f"barcode-{barcode_data}",
                        name=product_info["name"],
                        price=product_info["price"],
                        quantity=1,
                        purchased=False,
                        image_url=None
                    )
                    st.session_state.is_add_confirmation_modal_visible = True
                else:
                    st.session_state.scanned_item = ShoppingItem(
                        id=f"barcode-{barcode_data}",
                        name="Product from Barcode",
                        price=0,
                        quantity=1,
                        purchased=False,
                        image_url=None
                    )
                    st.session_state.is_add_confirmation_modal_visible = True
                    st.warning("Product Not Found: You can add it to your list and edit details.")
            else:
                st.error("No barcode detected.")
            st.session_state.is_scanning_barcode = False

    # --- Modals ---
    if st.session_state.is_add_manually_modal_visible:
        with st.form("add_item_form"):
            st.subheader("Edit Item" if st.session_state.is_edit_mode else "Add New Item")
            st.session_state.new_item_name = st.text_input("Item Name", value=st.session_state.new_item_name)
            st.session_state.new_item_price = st.text_input("Price", value=st.session_state.new_item_price)
            if st.session_state.is_edit_mode:
                submitted = st.form_submit_button("Update")
                if submitted:
                    handle_update_item()
            else:
                submitted = st.form_submit_button("Add")
                if submitted:
                    handle_add_manually()
        if st.button("Cancel", key="cancel_manual"):
            st.session_state.is_add_manually_modal_visible = False
            st.session_state.is_edit_mode = False
            st.session_state.new_item_name = ""
            st.session_state.new_item_price = ""

    if st.session_state.is_add_confirmation_modal_visible:
        with st.container():
            st.subheader("Confirm Item")
            if st.session_state.scanned_item:
                st.write(f"Name: {st.session_state.scanned_item.name}")
                st.write(f"Price: ${st.session_state.scanned_item.price:.2f}")
                st.write(f"Quantity: {st.session_state.scanned_item.quantity}")
                if st.button("Confirm", key="confirm_scanned_item"):
                    handle_add_scanned_item_to_cart()
                if st.button("Cancel", key="cancel_scanned_item"):
                    st.session_state.scanned_item = None
                    st.session_state.is_add_confirmation_modal_visible = False

if __name__ == "__main__":
    main()
