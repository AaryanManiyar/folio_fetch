# THIS MUST BE THE VERY FIRST LINE IN YOUR FILE
import streamlit as st
st.set_page_config(layout="wide")

# Now import other libraries
import hashlib
import mysql.connector
from datetime import datetime
import os
from PIL import Image
import database
from dashboard import financial_dashboard

# Initialize session state variables
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'profile_completed' not in st.session_state:
        st.session_state.profile_completed = False
    if 'just_signed_up' not in st.session_state:
        st.session_state.just_signed_up = False
    if 'editing_bank' not in st.session_state:
        st.session_state.editing_bank = None
    if 'editing_mf' not in st.session_state:
        st.session_state.editing_mf = None

# Hash the password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_profile_photo(username, profile_photo):
    """Save uploaded profile photo and return path"""
    if not profile_photo:
        return None
        
    os.makedirs("profile_photos", exist_ok=True)
    profile_photo_path = f"profile_photos/{username}_{profile_photo.name}"
    with open(profile_photo_path, "wb") as f:
        f.write(profile_photo.getbuffer())
    return profile_photo_path

def validate_profile_form(full_name, email, date_of_birth, mobile_number, address):
    """Validate required profile fields"""
    if not all([full_name, email, date_of_birth, mobile_number, address]):
        st.error("Please fill all required fields")
        return False
    return True

def profile_form(username):
    """Display and handle profile completion form"""
    st.title("Complete Your Profile")
    
    with st.form("profile_form"):
        full_name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        date_of_birth = st.date_input("Date of Birth", min_value=datetime(1900, 1, 1))
        pan_card = st.text_input("PAN Card Number", max_chars=10)
        aadhar_card = st.text_input("Aadhar Card Number", max_chars=12)
        mobile_number = st.text_input("Mobile Number", max_chars=10)
        profile_photo = st.file_uploader("Upload Profile Photo", type=['jpg', 'jpeg', 'png'])
        address = st.text_area("Address")
        city = st.text_input("City")
        state = st.text_input("State")
        pincode = st.text_input("Pincode")
        country = st.text_input("Country")
        
        if st.form_submit_button("Save Profile"):
            if not validate_profile_form(full_name, email, date_of_birth, mobile_number, address):
                return
            
            profile_photo_path = save_profile_photo(username, profile_photo)
            
            try:
                with database.get_db_connection() as conn:
                    if conn is None:
                        st.error("Failed to connect to database")
                        return
                        
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO user_profiles (
                                username, full_name, email, gender, date_of_birth,
                                pan_card, aadhar_card, mobile_number, profile_photo_path,
                                address, city, state, pincode, country
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            username, full_name, email, gender, date_of_birth,
                            pan_card, aadhar_card, mobile_number, profile_photo_path,
                            address, city, state, pincode, country
                        ))
                        conn.commit()
                        st.success("Profile saved successfully!")
                        st.session_state.profile_completed = True
                        st.experimental_rerun()
            except Exception as e:
                st.error(f"Error saving profile: {e}")

def view_profile(username):
    """Display user profile information"""
    st.title("Your Profile")
    
    try:
        with database.get_db_connection() as conn:
            if conn is None:
                st.error("Failed to connect to database")
                return
                
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM user_profiles WHERE username = %s", (username,))
                profile = cursor.fetchone()
                
                if not profile:
                    st.warning("Profile not found")
                    return
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if profile['profile_photo_path'] and os.path.exists(profile['profile_photo_path']):
                        st.image(Image.open(profile['profile_photo_path']), caption="Profile Photo", width=200)
                    else:
                        st.warning("No profile photo uploaded")
                
                with col2:
                    st.subheader("Personal Information")
                    st.write(f"**Full Name:** {profile['full_name']}")
                    st.write(f"**Email:** {profile['email']}")
                    st.write(f"**Gender:** {profile['gender']}")
                    st.write(f"**Date of Birth:** {profile['date_of_birth']}")
                    st.write(f"**Mobile:** {profile['mobile_number']}")
                    
                    st.subheader("Identity Information")
                    st.write(f"**PAN Card:** {profile['pan_card']}")
                    st.write(f"**Aadhar Card:** {profile['aadhar_card']}")
                    
                    st.subheader("Address")
                    st.write(profile['address'])
                    st.write(f"{profile['city']}, {profile['state']} - {profile['pincode']}")
                    st.write(profile['country'])
                
                if st.button("Edit Profile"):
                    st.session_state.profile_completed = False
                    st.experimental_rerun()
                    
    except Exception as e:
        st.error(f"Error fetching profile: {e}")

def card_details_form(username):
    """Display and handle card details form"""
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
            
            try:
                with database.get_db_connection() as conn:
                    if conn is None:
                        st.error("Failed to connect to database")
                        return
                        
                    with conn.cursor() as cursor:
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
            except Exception as e:
                st.error(f"Error saving card details: {e}")

def view_card_details(username):
    """Display user's card details"""
    try:
        with database.get_db_connection() as conn:
            if conn is None:
                st.error("Failed to connect to database")
                return
                
            with conn.cursor(dictionary=True) as cursor:
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
    except Exception as e:
        st.error(f"Error fetching card details: {e}")

def toggle_card_status(card_id, new_status):
    """Toggle card active status"""
    try:
        with database.get_db_connection() as conn:
            if conn is None:
                st.error("Failed to connect to database")
                return
                
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_cards 
                    SET is_active = %s 
                    WHERE id = %s
                """, (new_status, card_id))
                conn.commit()
                st.success("Card status updated!")
                st.experimental_rerun()
    except Exception as e:
        st.error(f"Error updating card status: {e}")

def delete_card(card_id):
    """Delete a card from database"""
    try:
        with database.get_db_connection() as conn:
            if conn is None:
                st.error("Failed to connect to database")
                return
                
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM user_cards 
                    WHERE id = %s
                """, (card_id,))
                conn.commit()
                st.success("Card deleted successfully!")
                st.experimental_rerun()
    except Exception as e:
        st.error(f"Error deleting card: {e}")

def signup():
    """Handle user signup process"""
    st.title("Sign Up")
    
    new_username = st.text_input("Create Username")
    new_password = st.text_input("Create Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if new_password != confirm_password:
            st.error("Passwords do not match")
            return
            
        try:
            with database.get_db_connection() as conn:
                if conn is None:
                    st.error("Failed to connect to database")
                    return
                    
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO users (username, password) VALUES (%s, %s)", 
                        (new_username, hash_password(new_password)))
                    conn.commit()
                    st.success("User registered successfully!")
                    st.session_state.username = new_username
                    st.session_state.just_signed_up = True
                    st.session_state.logged_in = True
                    st.experimental_rerun()
        except mysql.connector.IntegrityError:
            st.error("Username already exists. Please choose a different username.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

def login():
    """Handle user login process"""
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        try:
            with database.get_db_connection() as conn:
                if conn is None:
                    st.error("Failed to connect to database")
                    return
                    
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT password FROM users WHERE username = %s", 
                        (username,))
                    result = cursor.fetchone()
                    
                    if not result or result['password'] != hash_password(password):
                        st.error("Invalid username or password")
                        return
                        
                    st.success("Logged in successfully!")
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    
                    # Check if profile is completed
                    cursor.execute(
                        "SELECT 1 FROM user_profiles WHERE username = %s", 
                        (username,))
                    st.session_state.profile_completed = cursor.fetchone() is not None
                    st.experimental_rerun()
        except Exception as e:
            st.error(f"An error occurred: {e}")

def main():
    """Main application entry point"""
    init_session_state()
    database.create_database_and_tables()
    
    if not st.session_state.logged_in:
        choice = st.sidebar.selectbox("Choose Action", ["Login", "Sign Up"])
        if choice == "Sign Up":
            signup()
        else:
            login()
    else:
        if st.session_state.just_signed_up or not st.session_state.profile_completed:
            profile_form(st.session_state.username)
        else:
            # Create tabs for different sections
            tab1, tab2, tab3 = st.tabs(["Dashboard", "Profile", "Cards"])
            
            with tab1:
                financial_dashboard(st.session_state.username)
            
            with tab2:
                view_profile(st.session_state.username)
            
            with tab3:
                st.header("💳 Card Management")
                view_card_details(st.session_state.username)
                card_details_form(st.session_state.username)

if __name__ == "__main__":
    main()