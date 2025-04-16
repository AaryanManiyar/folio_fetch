import streamlit as st
import pandas as pd
from database import get_db_connection
from mysql.connector import Error
from database import delete_mutual_fund

def mutual_fund_details_form(username, edit_data=None):
    st.subheader("Edit Mutual Fund" if edit_data else "Add Mutual Fund")
    
    with st.form("mutual_fund_form"):
        folio_number = st.text_input("Folio Number*", value=edit_data['folio_number'] if edit_data else "")
        fund_name = st.text_input("Fund Name*", value=edit_data['fund_name'] if edit_data else "")
        fund_type = st.selectbox("Fund Type*", ["Equity", "Debt", "Hybrid", "ELSS", "Other"], 
                               index=["Equity", "Debt", "Hybrid", "ELSS", "Other"].index(edit_data['fund_type']) 
                               if edit_data else 0)
        investment_amount = st.number_input("Investment Amount (₹)", min_value=0.0, format="%.2f",
                                          value=float(edit_data['investment_amount']) if edit_data else 0.0)
        current_value = st.number_input("Current Value (₹)", min_value=0.0, format="%.2f",
                                      value=float(edit_data['current_value']) if edit_data else 0.0)
        nominee_name = st.text_input("Nominee Name", value=edit_data.get('nominee_name', '') if edit_data else "")
        
        submitted = st.form_submit_button("Update Fund Details" if edit_data else "Save Fund Details")
        
        if submitted:
            if not all([folio_number, fund_name]):
                st.error("Please fill all required fields (*)")
                return
            
            conn = get_db_connection()
            if conn is not None:
                cursor = conn.cursor()
                try:
                    if edit_data:
                        cursor.execute("""
                            UPDATE user_mutual_funds SET
                                folio_number = %s,
                                fund_name = %s,
                                fund_type = %s,
                                investment_amount = %s,
                                current_value = %s,
                                nominee_name = %s
                            WHERE id = %s
                        """, (
                            folio_number, fund_name, fund_type,
                            investment_amount, current_value, nominee_name,
                            edit_data['id']
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO user_mutual_funds (
                                username, folio_number, fund_name,
                                fund_type, investment_amount,
                                current_value, nominee_name
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            username, folio_number, fund_name,
                            fund_type, investment_amount,
                            current_value, nominee_name
                        ))
                    conn.commit()
                    st.success("Mutual fund details saved successfully!")
                    return True
                except Error as e:
                    st.error(f"Error saving mutual fund details: {e}")
                finally:
                    cursor.close()
                    conn.close()
    return False

def delete_mutual_fund(fund_id):
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_mutual_funds WHERE id = %s", (fund_id,))
            conn.commit()
            st.success("Mutual fund deleted successfully!")
            return True
        except Error as e:
            st.error(f"Error deleting mutual fund: {e}")
        finally:
            cursor.close()
            conn.close()
    return False

def view_mutual_funds(username):
    conn = get_db_connection()
    if conn is not None:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT id, folio_number, fund_name, fund_type,
                       investment_amount, current_value, nominee_name
                FROM user_mutual_funds 
                WHERE username = %s
            """, (username,))
            
            funds = cursor.fetchall()
            
            if funds:
                st.subheader("Your Mutual Funds")
                
                for fund in funds:
                    roi = ((fund['current_value'] - fund['investment_amount']) / fund['investment_amount']) * 100
                    
                    with st.expander(f"{fund['fund_name']} ({fund['fund_type']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Folio Number:** {fund['folio_number']}")
                            st.write(f"**Investment:** ₹{fund['investment_amount']:,.2f}")
                            st.write(f"**Current Value:** ₹{fund['current_value']:,.2f}")
                        with col2:
                            st.write(f"**ROI:** {roi:.2f}%")
                            if fund['nominee_name']:
                                st.write(f"**Nominee:** {fund['nominee_name']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Edit {fund['fund_name']}", key=f"edit_{fund['id']}"):
                                st.session_state['editing_fund'] = fund
                        with col2:
                            if st.button(f"Delete {fund['fund_name']}", key=f"delete_{fund['id']}"):
                                if st.warning("Are you sure you want to delete this fund?"):
                                    if delete_mutual_fund(fund['id']):
                                        st.experimental_rerun()
                
                if 'editing_fund' in st.session_state:
                    if mutual_fund_details_form(username, st.session_state['editing_fund']):
                        del st.session_state['editing_fund']
                        st.experimental_rerun()
                
            else:
                st.info("No mutual funds added yet")
        except Error as e:
            st.error(f"Error fetching mutual funds: {e}")
        finally:
            cursor.close()
            conn.close()