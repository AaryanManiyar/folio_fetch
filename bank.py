import streamlit as st
import pandas as pd
from io import BytesIO
from database import get_db_connection
from mysql.connector import Error
from database import delete_bank_account

def bank_details_form(username, edit_data=None):
    st.subheader("Edit Bank Account" if edit_data else "Add Bank Account")
    
    with st.form("bank_form"):
        bank_name = st.text_input("Bank Name*", value=edit_data['bank_name'] if edit_data else "")
        account_number = st.text_input("Account Number*", value=edit_data['account_number'] if edit_data else "")
        ifsc_code = st.text_input("IFSC Code*", max_chars=11, value=edit_data['ifsc_code'] if edit_data else "")
        account_balance = st.number_input("Account Balance (₹)", min_value=0.0, format="%.2f", 
                                        value=float(edit_data['account_balance']) if edit_data else 0.0)
        nominee_name = st.text_input("Nominee Name", value=edit_data.get('nominee_name', '') if edit_data else "")
        
        submitted = st.form_submit_button("Update Bank Details" if edit_data else "Save Bank Details")
        
        if submitted:
            if not all([bank_name, account_number, ifsc_code]):
                st.error("Please fill all required fields (*)")
                return
            
            conn = get_db_connection()
            if conn is not None:
                cursor = conn.cursor()
                try:
                    if edit_data:
                        cursor.execute("""
                            UPDATE user_banks SET
                                bank_name = %s,
                                account_number = %s,
                                ifsc_code = %s,
                                account_balance = %s,
                                nominee_name = %s
                            WHERE id = %s
                        """, (
                            bank_name, account_number, ifsc_code, 
                            account_balance, nominee_name,
                            edit_data['id']
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO user_banks (
                                username, bank_name, account_number, 
                                ifsc_code, account_balance, nominee_name
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            username, bank_name, account_number, 
                            ifsc_code, account_balance, nominee_name
                        ))
                    conn.commit()
                    st.success("Bank details saved successfully!")
                    return True
                except Error as e:
                    st.error(f"Error saving bank details: {e}")
                finally:
                    cursor.close()
                    conn.close()
    return False

def delete_bank_account(account_id):
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_banks WHERE id = %s", (account_id,))
            conn.commit()
            st.success("Bank account deleted successfully!")
            return True
        except Error as e:
            st.error(f"Error deleting bank account: {e}")
        finally:
            cursor.close()
            conn.close()
    return False

def view_bank_accounts(username):
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT id, bank_name, account_number, ifsc_code, 
                       account_balance, nominee_name
                FROM user_banks 
                WHERE username = %s
            """, (username,))
            
            accounts = cursor.fetchall()
            
            if accounts:
                st.subheader("Your Bank Accounts")
                
                for account in accounts:
                    with st.expander(f"{account['bank_name']} - ****{account['account_number'][-4:]}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Bank Name:** {account['bank_name']}")
                            st.write(f"**Account Number:** {account['account_number']}")
                            st.write(f"**IFSC Code:** {account['ifsc_code']}")
                        with col2:
                            st.write(f"**Balance:** ₹{account['account_balance']:,.2f}")
                            if account['nominee_name']:
                                st.write(f"**Nominee:** {account['nominee_name']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Edit {account['bank_name']}", key=f"edit_{account['id']}"):
                                st.session_state['editing_bank'] = account
                        with col2:
                            if st.button(f"Delete {account['bank_name']}", key=f"delete_{account['id']}"):
                                if st.warning("Are you sure you want to delete this account?"):
                                    if delete_bank_account(account['id']):
                                        st.experimental_rerun()
                
                if 'editing_bank' in st.session_state:
                    if bank_details_form(username, st.session_state['editing_bank']):
                        del st.session_state['editing_bank']
                        st.experimental_rerun()
                
            else:
                st.info("No bank accounts added yet")
        except Error as e:
            st.error(f"Error fetching bank details: {e}")
        finally:
            cursor.close()
            conn.close()