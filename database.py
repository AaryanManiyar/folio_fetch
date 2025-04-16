# database.py
import mysql.connector
from mysql.connector import Error
import streamlit as st

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Maniyar@18',
            database='folio_fetch'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_database_and_tables():
    try:
        # Connect to MySQL server without specifying database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Maniyar@18'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            # Create database if not exists
            cursor.execute("CREATE DATABASE IF NOT EXISTS folio_fetch")
            cursor.execute("USE folio_fetch")

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(255) PRIMARY KEY,
                    password VARCHAR(255) NOT NULL,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create user_profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    username VARCHAR(255) PRIMARY KEY,
                    full_name VARCHAR(255),
                    email VARCHAR(255) UNIQUE,
                    gender ENUM('Male', 'Female', 'Other'),
                    date_of_birth DATE,
                    pan_card VARCHAR(10) UNIQUE,
                    aadhar_card VARCHAR(12) UNIQUE,
                    mobile_number VARCHAR(10) UNIQUE,
                    profile_photo_path VARCHAR(255),
                    address TEXT,
                    city VARCHAR(100),
                    state VARCHAR(100),
                    pincode VARCHAR(10),
                    country VARCHAR(100),
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)

            # Create bank accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_banks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255),
                    bank_name VARCHAR(255) NOT NULL,
                    account_number VARCHAR(20) NOT NULL,
                    ifsc_code VARCHAR(11) NOT NULL,
                    account_balance DECIMAL(15, 2) DEFAULT 0.00,
                    FOREIGN KEY (username) REFERENCES users(username),
                    UNIQUE(username, account_number)
                )
            """)

            # Add nominee_name column to user_banks table (with error handling)
            try:
                cursor.execute("""
                    ALTER TABLE user_banks 
                    ADD COLUMN nominee_name VARCHAR(255)
                """)
            except Error as e:
                if "Duplicate column name" in str(e):
                    print("Column nominee_name already exists in user_banks table")
                else:
                    raise

            # Create mutual funds table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_mutual_funds (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255),
                    folio_number VARCHAR(50) NOT NULL,
                    fund_name VARCHAR(255) NOT NULL,
                    fund_type ENUM('Equity', 'Debt', 'Hybrid', 'ELSS', 'Other') NOT NULL,
                    investment_amount DECIMAL(15, 2),
                    current_value DECIMAL(15, 2),
                    nominee_name VARCHAR(255),
                    FOREIGN KEY (username) REFERENCES users(username),
                    UNIQUE(username, folio_number)
                )
            """)

            # Add to create_database_and_tables() function
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_cards (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255),
                    card_number VARCHAR(16) NOT NULL,
                    card_name VARCHAR(255),
                    card_classification ENUM('Debit', 'Credit') NOT NULL,
                    card_type ENUM('Visa', 'Mastercard', 'RuPay', 'Amex', 'Other') NOT NULL,
                    expiry_month VARCHAR(2) NOT NULL,
                    expiry_year VARCHAR(4) NOT NULL,
                    cvv VARCHAR(3) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (username) REFERENCES users(username),
                    UNIQUE(username, card_number)
    )
""")         

            connection.commit()
            print("Database setup completed successfully")
            
    except Error as e:
        print(f"Error creating database/tables: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_bank_account(account_id):
    """Delete a bank account from database"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                st.error("Failed to connect to database")
                return False
                
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM user_banks WHERE id = %s", (account_id,))
                conn.commit()
                st.success("Bank account deleted successfully!")
                return True
    except Error as e:
        st.error(f"Error deleting bank account: {e}")
        return False  

def delete_mutual_fund(fund_id):
    """Delete a mutual fund from database"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                st.error("Failed to connect to database")
                return False
                
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM user_mutual_funds WHERE id = %s", (fund_id,))
                conn.commit()
                st.success("Mutual fund deleted successfully!")
                return True
    except Error as e:
        st.error(f"Error deleting mutual fund: {e}")
        return False

def get_bank_accounts(username):
    """Get all bank accounts for a user"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                st.error("Failed to connect to database")
                return []
                
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, bank_name, account_number, ifsc_code, 
                           account_balance, nominee_name
                    FROM user_banks 
                    WHERE username = %s
                """, (username,))
                return cursor.fetchall()
    except Error as e:
        st.error(f"Error fetching bank accounts: {e}")
        return []

def get_mutual_funds(username):
    """Get all mutual funds for a user"""
    try:
        with get_db_connection() as conn:
            if conn is None:
                st.error("Failed to connect to database")
                return []
                
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT id, folio_number, fund_name, fund_type,
                           investment_amount, current_value, nominee_name
                    FROM user_mutual_funds 
                    WHERE username = %s
                """, (username,))
                return cursor.fetchall()
    except Error as e:
        st.error(f"Error fetching mutual funds: {e}")
        return []


if __name__ == "__main__":
    create_database_and_tables()