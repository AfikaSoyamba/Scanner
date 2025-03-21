import streamlit as st
import random
import time
from dataclasses import dataclass
from typing import List, Optional
import re  # Import the regular expression module


# Mock OCR and other functions for demonstration
def mock_ocr(image_path: str) -> Optional[str]:
    """Simulates OCR processing and returns extracted text."""
    time.sleep(0.5)  # Simulate processing delay

    # Mock OCR result based on a predefined image path
    if image_path == 'mockImagePath1':
        return 'Milk 2.50'
    elif image_path == 'mockImagePath2':
        return 'Bread 1.80'
    elif image_path == 'mockImagePath3':
        return 'Eggs 3.20'
    elif image_path == 'mockImagePath4':
        return 'Apple Juice 4.00'
    elif image_path == 'mockImagePath5':
        return 'Chicken Breast 12.50'
    elif image_path == 'mockImagePath6':
        return 'Pasta 1.20'
    elif image_path == 'mockImagePath7':
        return 'Rice 2.00'
    elif image_path == 'mockImagePath8':
        return 'Tomato Sauce 2.50'
    elif image_path == 'mockImagePath9':
        return 'Cheddar Cheese 6.00'
    elif image_path == 'mockImagePath10':
        return 'Ground Beef 8.00'
    else:
        # Return a random result for demonstration
        products = [
            'Milk 2.50',
            'Bread 1.80',
            'Eggs 3.20',
            'Coffee 7.99',
            'Cereal 4.50',
            'Yogurt 2.00',
            'Butter 3.50',
            'Sugar 1.00',
            'Salt 0.80',
            'Pepper 1.20',
            'Orange Juice 3.00',
            'Apple 0.50',
            'Banana 0.40',
            'Grapes 2.00',
            'Watermelon 4.00',
            'Potato Chips 2.50',
            'Chocolate Bar 1.50',
            'Ice Cream 5.00',
            'Cookies 3.00',
            'Soda 1.00'
        ]
        return random.choice(products)
    return None

def mock_barcode_scan() -> str:
    """Simulates a barcode scan and returns the barcode data."""
    time.sleep(0.5)
    return '123456789012'  # Example barcode data

def mock_add_to_shopping_list(item: 'ShoppingItem') -> None:
    """Simulates adding an item to the shopping list."""
    time.sleep(0.3)
    print('Adding to shopping list:', item)

def mock_save_loyalty_card(card: 'LoyaltyCard') -> None:
    """Simulates saving a loyalty card."""
    time.sleep(0.3)
    print('Saving loyalty card:', card)

def mock_get_product_info(barcode: str) -> Optional[dict]:
    """Simulates fetching product info from a database or API."""
    time.sleep(0.5)
    if barcode == '123456789012':
        return {'name': 'Generic Product', 'price': 9.99}
    elif barcode == '987654321098':
        return {'name': 'Brand Name Product', 'price': 19.99}
    else:
        return None  # Product not found

@dataclass
class ShoppingItem:
    """Represents an item in the shopping list."""
    id: str
    name: str
    price: float
    quantity: int
    purchased: bool
    image_url: Optional[str] = None

@dataclass
class LoyaltyCard:
    """Represents a loyalty card."""
    id: str
    name: str
    number: str
    barcode: Optional[str] = None
    image: Optional[str] = None

def main():
    """Main function to run the Flashka app using Streamlit."""
    st.title('Flashka - Price Scanner & Shopping List')

    # Initialize session state
    if 'camera_permission' not in st.session_state:
        st.session_state.camera_permission = 'authorized'
    if 'camera_type' not in st.session_state:
        st.session_state.camera_type = 'back'
    if 'is_scanning' not in st.session_state:
        st.session_state.is_scanning = False
    if 'shopping_list' not in st.session_state:
        st.session_state.shopping_list = []
    if 'loyalty_cards' not in st.session_state:
        st.session_state.loyalty_cards = []
    if 'is_add_manually_modal_visible' not in st.session_state:
        st.session_state.is_add_manually_modal_visible = False
    if 'new_item_name' not in st.session_state:
        st.session_state.new_item_name = ''
    if 'new_item_price' not in st.session_state:
        st.session_state.new_item_price = ''
    if 'new_card_name' not in st.session_state:
        st.session_state.new_card_name = ''
    if 'new_card_number' not in st.session_state:
        st.session_state.new_card_number = ''
    if 'is_add_card_manually_modal_visible' not in st.session_state:
        st.session_state.is_add_card_manually_modal_visible = False
    if 'scanned_item' not in st.session_state:
        st.session_state.scanned_item = None
    if 'is_add_confirmation_modal_visible' not in st.session_state:
        st.session_state.is_add_confirmation_modal_visible = False
    if 'is_scanning_barcode' not in st.session_state:
        st.session_state.is_scanning_barcode = False
    if 'is_barcode_mode' not in st.session_state:
        st.session_state.is_barcode_mode = False
    if 'scanned_barcode' not in st.session_state:
        st.session_state.scanned_barcode = None
    if 'is_fetching_product_info' not in st.session_state:
        st.session_state.is_fetching_product_info = False
    if 'is_edit_mode' not in st.session_state:
        st.session_state.is_edit_mode = False
    if 'editing_item' not in st.session_state:
        st.session_state.editing_item = None
    if 'is_add_card_modal_visible' not in st.session_state:
        st.session_state.is_add_card_modal_visible = False
    if 'selected_card_type' not in st.session_state:
        st.session_state.selected_card_type = None
    if 'show_settings' not in st.session_state:
        st.session_state.show_settings = False
    if 'ocr_engine' not in st.session_state:
        st.session_state.ocr_engine = 'tesseract'
    if 'image_quality' not in st.session_state:
        st.session_state.image_quality = 'high'
    if 'show_tutorial' not in st.session_state:
        st.session_state.show_tutorial = True
    if 'expanded_card_id' not in st.session_state:
        st.session_state.expanded_card_id = None

    # --- Helper Functions ---
    def add_item_to_shopping_list(item: ShoppingItem) -> None:
        """Adds an item to the shopping list or updates quantity if it exists."""
        existing_item_index = next(
            (index for index, list_item in enumerate(st.session_state.shopping_list) if list_item.name == item.name), -1
        )
        if existing_item_index > -1:
            updated_list = list(st.session_state.shopping_list)
            updated_list[existing_item_index].quantity += item.quantity
            st.session_state.shopping_list = updated_list
        else:
            st.session_state.shopping_list.append(item)
        mock_add_to_shopping_list(item)

    def delete_item_from_shopping_list(item_id: str) -> None:
        """Deletes an item from the shopping list."""
        st.session_state.shopping_list = [
            item for item in st.session_state.shopping_list if item.id != item_id
        ]

    def toggle_item_purchased(item_id: str) -> None:
        """Toggles the purchased status of an item in the shopping list."""
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
        """Adds a loyalty card to the list."""
        st.session_state.loyalty_cards.append(card)
        mock_save_loyalty_card(card)

    def delete_loyalty_card(card_id: str) -> None:
        """Deletes a loyalty card from the list."""
        st.session_state.loyalty_cards = [
            card for card in st.session_state.loyalty_cards if card.id != card_id
        ]
        if st.session_state.expanded_card_id == card_id:
            st.session_state.expanded_card_id = None

    # --- UI Components ---
    def render_shopping_list() -> None:
        """Renders the shopping list."""
        st.subheader('Shopping List')
        total_price = sum(item.price * item.quantity for item in st.session_state.shopping_list)
        st.write(f"Total Price: ${total_price:.2f}")

        for item in st.session_state.shopping_list:
            col1, col2, col3, col4 = st.columns([0.1, 0.6, 0.2, 0.1])
            with col1:
                if st.checkbox('', key=f"purchased-{item.id}", value=item.purchased):
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
                if st.button('Delete', key=f"delete-{item.id}"):
                    delete_item_from_shopping_list(item.id)
                    st.experimental_rerun()

    def render_loyalty_cards() -> None:
        """Renders the loyalty cards."""
        st.subheader('Loyalty Cards')
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
    def handle_scan_button_press() -> None:
        """Handles the scan button press."""
        st.session_state.is_scanning = True
        st.session_state.is_barcode_mode = False
        st.session_state.scanned_item = None
        st.session_state.scanned_barcode = None

        # Simulate OCR and handle result
        image_path = 'mockImagePath1'
        ocr_result = mock_ocr(image_path)
        if ocr_result:
            price_match = re.search(r'(\d+[,.]\d{2})', ocr_result)
            if price_match:
                price_str = price_match.group(1).replace(',', '.')
                try:
                    price = float(price_str)
                    st.session_state.scanned_item = ShoppingItem(
                        id=f'temp-{time.time()}',
                        name='Scanned Item',
                        price=price,
                        quantity=1,
                        purchased=False,
                        image_url=None
                    )
                    st.session_state.is_add_confirmation_modal_visible = True
                except ValueError:
                    st.error("Invalid price format detected.")
            else:
                st.error("No price found in scanned text.")
        else:
            st.error("Could not extract text. Please try again.")
        st.session_state.is_scanning = False

    def handle_barcode_button_press() -> None:
        """Handles the barcode button press."""
        st.session_state.is_scanning = False
        st.session_state.is_scanning_barcode = True
        st.session_state.is_barcode_mode = True
        st.session_state.scanned_item = None
        st.session_state.scanned_barcode = None

        # Simulate barcode scan and handle result
        barcode_data = mock_barcode_scan()
        st.session_state.scanned_barcode = barcode_data

        # Fetch product info
        st.session_state.is_fetching_product_info = True
        product_info = mock_get_product_info(barcode_data)
        st.session_state.is_fetching_product_info = False

        if product_info:
            st.session_state.scanned_item = ShoppingItem(
                id=f'barcode-{barcode_data}',
                name=product_info['name'],
                price=product_info['price'],
                quantity=1,
                purchased=False,
                image_url=None
            )
            st.session_state.is_add_confirmation_modal_visible = True
        else:
            st.session_state.scanned_item = ShoppingItem(
                id=f'barcode-{barcode_data}',
                name='Product from Barcode',
                price=0,
                quantity=1,
                purchased=False,
                image_url=None
            )
            st.session_state.is_add_confirmation_modal_visible = True
            st.warning("Product Not Found: Product information not found. You can add it to your list and edit the details.")
        st.session_state.is_scanning_barcode = False

    def handle_add_scanned_item_to_cart() -> None:
        """Handles adding the scanned item to the shopping list."""
        if st.session_state.scanned_item:
            add_item_to_shopping_list(st.session_state.scanned_item)
            st.session_state.scanned_item = None
            st.session_state.is_add_confirmation_modal_visible = False

    def handle_add_manually() -> None:
        """Handles adding an item manually."""
        if not st.session_state.new_item_name.strip() or not st.session_state.new_item_price.strip():
            st.error('Please enter both item name and price.')
            return
        try:
            price = float(st.session_state.new_item_price.replace(',', '.'))
        except ValueError:
            st.error('Invalid price format. Please enter a valid number.')
            return
        if price <= 0:
            st.error('Invalid price. Please enter a value greater than zero.')
            return

        new_item = ShoppingItem(
            id=f'manual-{time.time()}',
            name=st.session_state.new_item_name,
            price=price,
            quantity=1,
            purchased=False,
            image_url=None
        )
        add_item_to_shopping_list(new_item)
        st.session_state.new_item_name = ''
        st.session_state.new_item_price = ''
        st.session_state.is_add_manually_modal_visible = False

    def handle_update_item() -> None:
        """Handles updating an edited item."""
        if not st.session_state.new_item_name.strip() or not st.session_state.new_item_price.strip():
            st.error('Please enter both item name and price.')
            return
        try:
            price = float(st.session_state.new_item_price.replace(',', '.'))
        except ValueError:
            st.error('Invalid price format. Please enter a valid number.')
            return
        if price <= 0:
            st.error('Invalid price. Please enter a value greater than zero.')
            return

        if st.session_state.editing_item:
            updated_list = [
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
            st.session_state.shopping_list = updated_list
            st.session_state.editing_item = None
        st.session_state.new_item_name = ''
        st.session_state.new_item_price = ''
        st.session_state.is_edit_mode = False
        st.session_state.is_add_manually_modal_visible = False

    def handle_add_card_manually() -> None:
        """Handles adding a loyalty card manually."""
        if not st.session_state.new_card_name.strip() or not st.session_state.new_card_number.strip():
            st.error('Please enter both card name and number.')
            return
        new_card = LoyaltyCard(
            id=f'manual-card-{time.time()}',
            name=st.session_state.new_card_name,
            number=st.session_state.new_card_number,
            image=None
        )
        add_loyalty_card(new_card)
        st.session_state.new_card_name = ''
        st.session_state.new_card_number = ''
        st.session_state.is_add_card_manually_modal_visible = False
        st.session_state.is_add_card_modal_visible = False
        st.session_state.selected_card_type = None

    def handle_add_card(card_type: str) -> None:
        """Handles the add card button click."""
        st.session_state.selected_card_type = card_type
        st.session_state.is_add_card_modal_visible = True
        if card_type == 'manual':
            st.session_state.is_add_card_manually_modal_visible = True

    def handle_card_scan() -> None:
        """Handles loyalty card scan."""
        if st.session_state.camera_permission != 'authorized':
            st.error('Camera Permission Required: Flashka needs access to your camera to scan cards. Please enable it in your device settings.')
            return

        st.session_state.is_scanning = True
        st.session_state.is_barcode_mode = True
        st.session_state.scanned_barcode = None
        st.session_state.scanned_item = None

        barcode_data = mock_barcode_scan()
        st.session_state.scanned_barcode = barcode_data

        new_card = LoyaltyCard(
            id=f'card-{barcode_data}-{time.time()}',
            name=f'Card from Scan {barcode_data}',
            number=barcode_data,
            barcode=barcode_data,
            image=None
        )

        add_loyalty_card(new_card)
        st.session_state.is_scanning = False
        st.session_state.is_add_card_modal_visible = False
        st.session_state.selected_card_type = None

    def handle_close_tutorial() -> None:
        """Handles closing the tutorial."""
        st.session_state.show_tutorial = False

    # --- Main UI ---
    if st.session_state.show_tutorial:
        with st.container():
            st.title('Welcome to Flashka!')
            st.write('Flashka helps you scan prices, manage your shopping list, and store loyalty cards.')
            st.subheader("Tutorial")
            st.write("1. **Scan Prices:** Use the 'Scan Price' button and point your camera at the price.")
            st.write("2. **View Shopping List:** View the items, their prices, and mark them as purchased.")
            st.write("3. **Manage Loyalty Cards:** Store your loyalty cards by scanning or entering details manually.")
            if st.button("Close Tutorial"):
                handle_close_tutorial()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Shopping')
        if st.button('Scan Price'):
            handle_scan_button_press()
        if st.button('Add Manually'):
            st.session_state.is_add_manually_modal_visible = True
        if st.button('Scan Barcode'):
            handle_barcode_button_press()
        render_shopping_list()

    with col2:
        st.subheader('Cards')
        if st.button('Add Card'):
            handle_add_card('manual')
        render_loyalty_cards()

    # --- Modals ---
    if st.session_state.is_add_manually_modal_visible:
        with st.form("add_item_form"):
            st.subheader("Edit Item" if st.session_state.is_edit_mode else "Add New Item")
            st.session_state.new_item_name = st.text_input('Item Name', value=st.session_state.new_item_name)
            st.session_state.new_item_price = st.text_input('Price', value=st.session_state.new_item_price)
            if st.session_state.is_edit_mode:
                if st.form_submit_button("Update"):
                    handle_update_item()
            else:
                if st.form_submit_button('Add'):
                    handle_add_manually()
        if st.button("Cancel"):
            st.session_state.is_add_manually_modal_visible = False
            st.session_state.is_edit_mode = False
            st.session_state.new_item_name = ''
            st.session_state.new_item_price = ''

    if st.session_state.is_add_confirmation_modal_visible:
        with st.container():
            st.subheader('Confirm Item')
            if st.session_state.scanned_item:
                st.write(f"Name: {st.session_state.scanned_item.name}")
                st.write(f"Price: ${st.session_state.scanned_item.price:.2f}")
                st.write(f"Quantity: {st.session_state.scanned_item.quantity}")
                if st.button("Confirm", key="confirm_scanned_item"):
                    handle_add_scanned_item_to_cart()
                if st.button("Cancel", key="cancel_scanned_item"):
                    st.session_state.scanned_item = None
                    st.session_state.is_add_confirmation_modal_visible = False

if __name__ == '__main__':
    main()
