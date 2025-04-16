import streamlit as st
from database import get_db_connection
from mysql.connector import Error

def card_details_form(username):
    st.subheader("Add Card Details")
    
    with st.form("card_form"):
        col1, col2 = st.columns(2)
        with col1:
            card_name = st.text_input("Card Name (Optional)")
            card_number = st.text_input("Card Number*", max_chars=16)
            card_classification = st.selectbox("Card Type*", ["Debit", "Credit"])
        with col2:
            card_type = st.selectbox("Network*", ["Visa", "Mastercard", "RuPay", "Amex", "Other"])
            expiry_month = st.selectbox("Expiry Month*", ["01","02","03","04","05","06","07","08","09","10","11","12"])
            expiry_year = st.selectbox("Expiry Year*", [str(y) for y in range(2023, 2040)])
            cvv = st.text_input("CVV*", max_chars=3, type="password")
        
        submitted = st.form_submit_button("Save Card Details")
        
        if submitted:
            if not all([card_number, cvv]):
                st.error("Please fill all required fields (*)")
                return
            
            conn = get_db_connection()
            if conn is not None:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO user_cards (
                            username, card_name, card_number, 
                            card_classification, card_type,
                            expiry_month, expiry_year, cvv
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        username, card_name, card_number, 
                        card_classification, card_type,
                        expiry_month, expiry_year, cvv
                    ))
                    conn.commit()
                    st.success("Card details saved successfully!")
                except Error as e:
                    st.error(f"Error saving card details: {e}")
                finally:
                    cursor.close()
                    conn.close()

def view_card_details(username):
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT id, card_name, card_number, card_classification,
                       card_type, expiry_month, expiry_year, is_active
                FROM user_cards 
                WHERE username = %s
                ORDER BY is_active DESC, card_classification
            """, (username,))
            
            cards = cursor.fetchall()
            
            if cards:
                st.subheader("Your Card Details")
                
                for card in cards:
                    with st.expander(f"{card['card_type']} {card['card_classification']} Card"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Card Name:** {card['card_name'] or 'Not specified'}")
                            st.write(f"**Number:** **** **** **** {card['card_number'][-4:]}")
                            st.write(f"**Status:** {'✅ Active' if card['is_active'] else '❌ Inactive'}")
                        with col2:
                            st.write(f"**Type:** {card['card_type']}")
                            st.write(f"**Expiry:** {card['expiry_month']}/{card['expiry_year']}")
                        
                        # Add toggle and delete buttons
                        col1, col2, _ = st.columns([1,1,2])
                        with col1:
                            if st.button("Toggle Status", key=f"toggle_{card['id']}"):
                                toggle_card_status(card['id'], not card['is_active'])
                        with col2:
                            if st.button("Delete", key=f"delete_{card['id']}"):
                                delete_card(card['id'])
            else:
                st.info("No card details added yet")
        except Error as e:
            st.error(f"Error fetching card details: {e}")
        finally:
            cursor.close()
            conn.close()

def toggle_card_status(card_id, new_status):
    try:
        conn = get_db_connection()
        if conn is not None:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_cards 
                    SET is_active = %s 
                    WHERE id = %s
                """, (new_status, card_id))
                conn.commit()
                st.success("Card status updated!")
                st.experimental_rerun()
    except Error as e:
        st.error(f"Error updating card status: {e}")

def delete_card(card_id):
    try:
        conn = get_db_connection()
        if conn is not None:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM user_cards 
                    WHERE id = %s
                """, (card_id,))
                conn.commit()
                st.success("Card deleted successfully!")
                st.experimental_rerun()
    except Error as e:
        st.error(f"Error deleting card: {e}")