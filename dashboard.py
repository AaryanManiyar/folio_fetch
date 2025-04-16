import streamlit as st
import pandas as pd
from io import BytesIO
from database import get_db_connection
from mysql.connector import Error
from database import delete_bank_account
from database import delete_mutual_fund

# Constants for styling
CARD_STYLE = """
<style>
.card {
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    transition: 0.3s;
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 20px;
}
.card:hover {
    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
}
.summary-card {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
}
.action-btn {
    margin: 5px;
}
@media (max-width: 600px) {
    .column {
        width: 100%;
    }
}
</style>
"""

def format_currency(value):
    """Format numeric values as currency with ₹ symbol"""
    return f"₹{value:,.2f}"

def format_percentage(value):
    """Format numeric values as percentage with 2 decimal places"""
    return f"{value:.2f}%"

def get_bank_data(username):
    """Fetch bank account data for the given username including ID and nominee"""
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
        st.error(f"Error fetching bank details: {e}")
        return []

def get_mf_data(username):
    """Fetch mutual fund data for the given username including ID and ROI"""
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
                funds = cursor.fetchall()
                
                # Calculate ROI for each fund
                for fund in funds:
                    fund['roi'] = ((fund['current_value'] - fund['investment_amount']) / 
                                  fund['investment_amount']) * 100 if fund['investment_amount'] else 0
                return funds
    except Error as e:
        st.error(f"Error fetching mutual funds: {e}")
        return []

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

def display_summary_metrics(total_balance, total_invested, current_value, net_worth):
    """Display the summary metrics cards"""
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Total Balance", total_balance),
        ("Invested Amount", total_invested),
        ("Current Value", current_value),
        ("Net Worth", net_worth)
    ]
    
    for col, (title, value) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class="summary-card">
                <h4>{title}</h4>
                <h3>{format_currency(value)}</h3>
            </div>
            """, unsafe_allow_html=True)

def add_bank_account_form(username, edit_data=None):
    """Form to add/edit bank account"""
    st.header("✏️ Edit Bank Account" if edit_data else "➕ Add New Bank Account")
    
    with st.form("bank_form"):
        bank_name = st.text_input("Bank Name*", value=edit_data['bank_name'] if edit_data else "")
        account_number = st.text_input("Account Number*", value=edit_data['account_number'] if edit_data else "")
        ifsc_code = st.text_input("IFSC Code*", max_chars=11, value=edit_data['ifsc_code'] if edit_data else "")
        account_balance = st.number_input("Account Balance (₹)", min_value=0.0, format="%.2f",
                                        value=float(edit_data['account_balance']) if edit_data else 0.0)
        nominee_name = st.text_input("Nominee Name", value=edit_data.get('nominee_name', '') if edit_data else "")
        
        col1, col2 = st.columns(2)
        with col1:
            save_clicked = st.form_submit_button("Update" if edit_data else "Save")
        with col2:
            cancel_clicked = st.form_submit_button("Cancel")
        
        if save_clicked:
            if not all([bank_name, account_number, ifsc_code]):
                st.error("Please fill all required fields (*)")
            else:
                try:
                    with get_db_connection() as conn:
                        if conn is None:
                            st.error("Failed to connect to database")
                            return False
                            
                        with conn.cursor() as cursor:
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
                            st.session_state.show_bank_form = False
                            if edit_data:
                                st.session_state.editing_bank = None
                            st.success("Bank details saved successfully!")
                            return True
                except Error as e:
                    st.error(f"Error saving bank details: {e}")
        
        if cancel_clicked:
            st.session_state.show_bank_form = False
            if edit_data:
                st.session_state.editing_bank = None
    return False

def add_mutual_fund_form(username, edit_data=None):
    """Form to add/edit mutual fund"""
    st.header("✏️ Edit Mutual Fund" if edit_data else "➕ Add New Mutual Fund")
    
    with st.form("mf_form"):
        folio_number = st.text_input("Folio Number*", value=edit_data['folio_number'] if edit_data else "")
        fund_name = st.text_input("Fund Name*", value=edit_data['fund_name'] if edit_data else "")
        fund_type = st.selectbox("Fund Type*", ["Equity", "Debt", "Hybrid", "ELSS", "Other"],
                               index=["Equity", "Debt", "Hybrid", "ELSS", "Other"].index(
                                   edit_data['fund_type']) if edit_data else 0)
        investment_amount = st.number_input("Investment Amount (₹)", min_value=0.0, format="%.2f",
                                          value=float(edit_data['investment_amount']) if edit_data else 0.0)
        current_value = st.number_input("Current Value (₹)", min_value=0.0, format="%.2f",
                                      value=float(edit_data['current_value']) if edit_data else 0.0)
        nominee_name = st.text_input("Nominee Name", value=edit_data.get('nominee_name', '') if edit_data else "")
        
        col1, col2 = st.columns(2)
        with col1:
            save_clicked = st.form_submit_button("Update" if edit_data else "Save")
        with col2:
            cancel_clicked = st.form_submit_button("Cancel")
        
        if save_clicked:
            if not all([folio_number, fund_name]):
                st.error("Please fill all required fields (*)")
            else:
                try:
                    with get_db_connection() as conn:
                        if conn is None:
                            st.error("Failed to connect to database")
                            return False
                            
                        with conn.cursor() as cursor:
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
                            st.session_state.show_mf_form = False
                            if edit_data:
                                st.session_state.editing_mf = None
                            st.success("Mutual fund details saved successfully!")
                            return True
                except Error as e:
                    st.error(f"Error saving mutual fund details: {e}")
        
        if cancel_clicked:
            st.session_state.show_mf_form = False
            if edit_data:
                st.session_state.editing_mf = None
    return False

def display_bank_accounts(bank_data, username):
    """Display bank accounts section with Add/Edit/Delete functionality"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("🏦 Bank Accounts")
    with col2:
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        if st.button("➕ Add Bank Account", key="add_bank"):
            st.session_state.show_bank_form = True
    
    if st.session_state.get('show_bank_form', False):
        add_bank_account_form(username)
        return
    
    if st.session_state.get('editing_bank', None):
        if add_bank_account_form(username, st.session_state.editing_bank):
            st.experimental_rerun()
        return
    
    if not bank_data:
        st.info("No bank accounts added yet")
        return
    
    # Display bank accounts with edit/delete options
    for account in bank_data:
        with st.container():
            st.markdown(f"""
            <div class="card">
                <h3>{account['bank_name']}</h3>
                <p><b>Account:</b> ****{account['account_number'][-4:]}</p>
                <p><b>IFSC:</b> {account['ifsc_code']}</p>
                <p><b>Balance:</b> {format_currency(account['account_balance'])}</p>
                {f"<p><b>Nominee:</b> {account['nominee_name']}</p>" if account['nominee_name'] else ""}
            </div>
            """, unsafe_allow_html=True)
            
            # Create columns for buttons inside the container
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(f"Edit", key=f"edit_bank_{account['id']}"):
                    st.session_state.editing_bank = account
                    st.experimental_rerun()
            with btn_col2:
                if st.button(f"Delete", key=f"delete_bank_{account['id']}"):
                    with st.container():
                        st.warning("Are you sure you want to delete this account?")
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("Yes, delete", key=f"confirm_delete_bank_{account['id']}"):
                                if delete_bank_account(account['id']):
                                    st.experimental_rerun()
                        with confirm_col2:
                            if st.button("Cancel", key=f"cancel_delete_bank_{account['id']}"):
                                pass

def display_mutual_funds(mf_data, username):
    """Display mutual funds section with Add/Edit/Delete functionality"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("📈 Mutual Funds")
    with col2:
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        if st.button("➕ Add Mutual Fund", key="add_mf"):
            st.session_state.show_mf_form = True
    
    if st.session_state.get('show_mf_form', False):
        add_mutual_fund_form(username)
        return
    
    if st.session_state.get('editing_mf', None):
        if add_mutual_fund_form(username, st.session_state.editing_mf):
            st.experimental_rerun()
        return
    
    if not mf_data:
        st.info("No mutual funds added yet")
        return
    
    # Display mutual funds with edit/delete options
    cols = st.columns(1 if len(mf_data) == 1 else min(2, len(mf_data)))
    
    for idx, fund in enumerate(mf_data):
        with cols[idx % len(cols)]:
            st.markdown(f"""
            <div class="card">
                <h3>{fund['fund_name']}</h3>
                <p><b>Type:</b> {fund['fund_type']}</p>
                <p><b>Folio:</b> {fund['folio_number']}</p>
                <p><b>Invested:</b> {format_currency(fund['investment_amount'])}</p>
                <p><b>Current Value:</b> {format_currency(fund['current_value'])}</p>
                <p><b>ROI:</b> {format_percentage(fund['roi'])}</p>
                {f"<p><b>Nominee:</b> {fund['nominee_name']}</p>" if fund['nominee_name'] else ""}
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Edit", key=f"edit_mf_{fund['id']}"):
                    st.session_state.editing_mf = fund
                    st.experimental_rerun()
            with col2:
                if st.button(f"Delete", key=f"delete_mf_{fund['id']}"):
                    with st.container():
                        st.warning("Are you sure you want to delete this fund?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Yes, delete", key=f"confirm_delete_mf_{fund['id']}"):
                                if delete_mutual_fund(fund['id']):
                                    st.experimental_rerun()
                        with col2:
                            if st.button("Cancel", key=f"cancel_delete_mf_{fund['id']}"):
                                pass

def display_export_options(bank_data, mf_data):
    """Display data export options"""
    st.header("📤 Export Data")
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        if bank_data:
            bank_df = pd.DataFrame(bank_data)
            bank_df['account_balance'] = bank_df['account_balance'].apply(format_currency)
            csv = bank_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Export Bank Data (CSV)",
                data=csv,
                file_name="bank_accounts.csv",
                mime="text/csv"
            )
    
    with export_col2:
        if mf_data:
            mf_df = pd.DataFrame(mf_data)
            mf_df['investment_amount'] = mf_df['investment_amount'].apply(format_currency)
            mf_df['current_value'] = mf_df['current_value'].apply(format_currency)
            mf_df['roi'] = mf_df['roi'].apply(format_percentage)
            csv = mf_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Export MF Data (CSV)",
                data=csv,
                file_name="mutual_funds.csv",
                mime="text/csv"
            )

def logout():
    """Handle user logout process"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.profile_completed = False
    st.session_state.just_signed_up = False
    st.experimental_rerun()

def financial_dashboard(username):
    """Main dashboard function"""
    st.markdown(CARD_STYLE, unsafe_allow_html=True)
    
    # Initialize session state variables if they don't exist
    if 'show_bank_form' not in st.session_state:
        st.session_state.show_bank_form = False
    if 'show_mf_form' not in st.session_state:
        st.session_state.show_mf_form = False
    if 'editing_bank' not in st.session_state:
        st.session_state.editing_bank = None
    if 'editing_mf' not in st.session_state:
        st.session_state.editing_mf = None
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"💰 Financial Dashboard")
        st.markdown(f"**Welcome back, {username}!** Here's your financial overview.")
    with col2:
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout"):
            logout()
    
    # Fetch data
    bank_data = get_bank_data(username)
    mf_data = get_mf_data(username)
    
    # Calculate summary metrics
    total_balance = sum(acc['account_balance'] for acc in bank_data) if bank_data else 0
    total_invested = sum(mf['investment_amount'] for mf in mf_data) if mf_data else 0
    current_value = sum(mf['current_value'] for mf in mf_data) if mf_data else 0
    net_worth = total_balance + current_value
    
    if st.session_state.show_bank_form:
        add_bank_account_form(username)
    else:
        display_bank_accounts(bank_data, username)
    
    # Display mutual funds or form
    if st.session_state.show_mf_form:
        add_mutual_fund_form(username)
    else:
        display_mutual_funds(mf_data, username)
    
    # Display export options if not showing forms
    if not st.session_state.show_bank_form and not st.session_state.show_mf_form:
        display_export_options(bank_data, mf_data)