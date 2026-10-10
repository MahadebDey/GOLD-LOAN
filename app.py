import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import date

st.set_page_config(page_title="Gold & Silver Loan Manager", layout="wide", page_icon="🪙")

# ----------------- GOOGLE SHEETS CONNECTION -----------------
@st.cache_resource
def get_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    # Spreadsheet open karein
    sheet = client.open("Gold_and_Silver_Loan_Ledger").sheet1
    return sheet

try:
    sheet = get_google_sheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Google Sheet connect karne mein samasya: {e}")
    st.stop()

# Data Type Corrections
if not df.empty:
    df["Weight_gm"] = pd.to_numeric(df["Weight_gm"], errors="coerce").fillna(0.0)
    df["Loan_Amount"] = pd.to_numeric(df["Loan_Amount"], errors="coerce").fillna(0.0)

# ----------------- LIVE METRICS -----------------
st.title("🪙 Gold & Silver Loan Management System")

active_df = df[df["Status"] == "Active"] if not df.empty else pd.DataFrame()
active_gold_wt = active_df[active_df["Metal_Type"] == "Gold"]["Weight_gm"].sum() if not active_df.empty else 0.0
active_silver_wt = active_df[active_df["Metal_Type"] == "Silver"]["Weight_gm"].sum() if not active_df.empty else 0.0
active_loan_amount = active_df["Loan_Amount"].sum() if not active_df.empty else 0.0
total_lifetime_amount = df["Loan_Amount"].sum() if not df.empty else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("🟡 Tijori mein Gold (Active)", f"{active_gold_wt:,.3f} gm")
col2.metric("⚪ Tijori mein Silver (Active)", f"{active_silver_wt:,.3f} gm")
col3.metric("💰 Market mein Bacha Paisa", f"₹ {active_loan_amount:,.2f}")
col4.metric("📈 Aaj tak Kul Diya Loan", f"₹ {total_lifetime_amount:,.2f}")

st.divider()

# ----------------- TABS -----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Loan Ledger", 
    "➕ Nayi Loan Entry", 
    "📈 Amount Badhayein (Top-up)", 
    "🔒 Loan Close / Settle"
])

# ================= TAB 1: LEDGER =================
with tab1:
    st.subheader("Bahi-Khata / Ledger")
    c1, c2 = st.columns(2)
    with c1:
        status_filter = st.selectbox("Status Filter", ["All", "Active", "Closed"])
    with c2:
        metal_filter = st.selectbox("Metal Filter", ["All", "Gold", "Silver"])
        
    filtered_df = df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]
    if metal_filter != "All":
        filtered_df = filtered_df[filtered_df["Metal_Type"] == metal_filter]
        
    st.dataframe(filtered_df, use_container_width=True)

# ================= TAB 2: NAYI ENTRY =================
with tab2:
    st.subheader("Naya Loan Register Karein")
    with st.form("new_entry_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            sl_no = len(df) + 1
            st.text(f"Serial No: {sl_no}")
            cust_name = st.text_input("Grahak ka Naam (Customer Name)*")
            phone = st.text_input("Mobile Number")
            metal_type = st.selectbox("Metal Type*", ["Gold", "Silver"])
            item_desc = st.text_input("Gehne ka Vivaran (Item Description)*")
        with col_b:
            entry_date = st.date_input("Date", value=date.today())
            weight = st.number_input("Weight (Grams mein)*", min_value=0.000, step=0.001, format="%.3f")
            loan_amt = st.number_input("Loan Amount (₹)*", min_value=0.0, step=500.0)
            interest_rate = st.number_input("Monthly Byaaj Dar (%)", value=1.5, step=0.1)
            
        submitted = st.form_submit_button("Record Save Karein")
        
        if submitted:
            if cust_name and loan_amt > 0 and weight > 0:
                prefix = "GL" if metal_type == "Gold" else "SL"
                loan_id = f"{prefix}-{entry_date.strftime('%Y')}-{sl_no:03d}"
                new_row = [
                    sl_no,
                    loan_id,
                    entry_date.strftime("%d/%m/%Y"),
                    cust_name,
                    phone,
                    metal_type,
                    item_desc,
                    weight,
                    loan_amt,
                    interest_rate,
                    "Active",
                    "",
                    ""
                ]
                sheet.append_row(new_row)
                st.success(f"{cust_name} ki entry ({loan_id}) save ho gayi!")
                st.rerun()
            else:
                st.error("Kripya sabhi zaroori jankari sahi bharein.")

# ================= TAB 3: LOAN AMOUNT BADHAYEIN (TOP-UP) =================
with tab3:
    st.subheader("Puraney Loan par Rashi Badhayein (Top-up Amount)")
    
    if not active_df.empty:
        active_loans = active_df["Loan_ID"].tolist()
        topup_loan_id = st.selectbox("Loan ID Chunein", active_loans, key="topup_select")
        
        selected_record = active_df[active_df["Loan_ID"] == topup_loan_id].iloc[0]
        current_amt = float(selected_record["Loan_Amount"])
        
        st.info(f"**Grahak:** {selected_record['Customer_Name']} | **Item:** {selected_record['Item_Description']} ({selected_record['Weight_gm']} gm) | **Puraana Loan Amount:** ₹{current_amt:,.2f}")
        
        with st.form("topup_form"):
            c_top1, c_top2 = st.columns(2)
            with c_top1:
                topup_date = st.date_input("Rashi Badhane ki Taareekh", value=date.today())
                extra_amt = st.number_input("Kitna Paisa Aur Badhana Hai (₹)*", min_value=100.0, step=500.0)
            with c_top2:
                topup_note = st.text_input("Vivaran / Note", value=f"Top-up on {topup_date.strftime('%d/%m/%Y')}")
                new_total_amt = current_amt + extra_amt
                st.markdown(f"**Naya Kul Loan Amount Hoga:** ₹{new_total_amt:,.2f}")
                
            submitted_topup = st.form_submit_button("Amount Badhayein & Update Karein")
            
            if submitted_topup:
                cell = sheet.find(topup_loan_id)
                if cell:
                    # Column 9 = Loan_Amount, Column 13 = Remarks
                    existing_remarks = str(selected_record.get("Remarks", ""))
                    updated_remarks = f"{existing_remarks} | +₹{extra_amt:,.0f} ({topup_date.strftime('%d/%m/%Y')})".strip(" | ")
                    
                    sheet.update_cell(cell.row, 9, new_total_amt)
                    sheet.update_cell(cell.row, 13, updated_remarks)
                    
                    st.success(f"Loan ID {topup_loan_id} ka amount badhakar ₹{new_total_amt:,.2f} kar diya gaya hai!")
                    st.rerun()
    else:
        st.info("Abhi koi Active loan nahi hai.")

# ================= TAB 4: LOAN CLOSE =================
with tab4:
    st.subheader("Loan Chhudana / Status Closed Karna")
    
    if not active_df.empty:
        close_loan_id = st.selectbox("Chhudaane ke liye Loan ID chunein", active_df["Loan_ID"].tolist(), key="close_select")
        close_record = active_df[active_df["Loan_ID"] == close_loan_id].iloc[0]
        st.info(f"**Grahak:** {close_record['Customer_Name']} | **Item:** {close_record['Item_Description']} | **Loan Amount:** ₹{close_record['Loan_Amount']}")
        
        with st.form("close_form"):
            c_date = st.date_input("Close / Delivery Date", value=date.today())
            remarks_close = st.text_input("Remarks", value="Full settlement received, item released")
            close_btn = st.form_submit_button("Loan Close Karein")
            
            if close_btn:
                cell = sheet.find(close_loan_id)
                if cell:
                    sheet.update_cell(cell.row, 11, "Closed")
                    sheet.update_cell(cell.row, 12, c_date.strftime("%d/%m/%Y"))
                    sheet.update_cell(cell.row, 13, remarks_close)
                    st.success(f"Loan ID {close_loan_id} safaltapoorvak close ho gaya!")
                    st.rerun()
    else:
        st.info("Abhi koi Active loan nahi hai.")
