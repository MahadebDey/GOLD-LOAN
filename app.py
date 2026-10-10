import streamlit as st
import requests
import pandas as pd
from datetime import date

st.set_page_config(page_title="Gold & Silver Loan Manager", layout="wide", page_icon="🪙")

# AAPKA GOOGLE APPS SCRIPT URL
API_URL = "https://script.google.com/macros/s/AKfycbxAkdWvO9cEg_BdruMFHvlsXLpLZGYI1nP8bR74uvpU8w70W_2d2lTq3popU0sz-Euspg/exec"

def load_data():
    try:
        res = requests.get(API_URL, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Data load karne mein samasya: {e}")
    return pd.DataFrame()

df = load_data()

# Data Type Corrections
if not df.empty:
    if "Weight_gm" in df.columns:
        df["Weight_gm"] = pd.to_numeric(df["Weight_gm"], errors="coerce").fillna(0.0)
    if "Loan_Amount" in df.columns:
        df["Loan_Amount"] = pd.to_numeric(df["Loan_Amount"], errors="coerce").fillna(0.0)

# ----------------- HEADER & DASHBOARD -----------------
st.title("🪙 Gold & Silver Loan Management System")

active_df = df[df["Status"] == "Active"] if (not df.empty and "Status" in df.columns) else pd.DataFrame()

active_gold_wt = active_df[active_df["Metal_Type"] == "Gold"]["Weight_gm"].sum() if (not active_df.empty and "Metal_Type" in active_df.columns) else 0.0
active_silver_wt = active_df[active_df["Metal_Type"] == "Silver"]["Weight_gm"].sum() if (not active_df.empty and "Metal_Type" in active_df.columns) else 0.0
active_loan_amount = active_df["Loan_Amount"].sum() if (not active_df.empty and "Loan_Amount" in active_df.columns) else 0.0
total_lifetime_amount = df["Loan_Amount"].sum() if (not df.empty and "Loan_Amount" in df.columns) else 0.0

st.markdown("### 📊 Tijori aur Market ka Live Hisab")
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
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            s_filter = st.selectbox("Status Filter", ["All", "Active", "Closed"])
        with c2:
            m_filter = st.selectbox("Metal Filter", ["All", "Gold", "Silver"])
            
        filtered_df = df.copy()
        if s_filter != "All" and "Status" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Status"] == s_filter]
        if m_filter != "All" and "Metal_Type" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Metal_Type"] == m_filter]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.info("Abhi sheet mein koi data nahi mila.")

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
            item_desc = st.text_input("Gehne ka Vivaran (Item Details)*")
        with col_b:
            entry_date = st.date_input("Date", value=date.today())
            weight = st.number_input("Weight (gm)*", min_value=0.000, step=0.001, format="%.3f")
            loan_amt = st.number_input("Loan Amount (₹)*", min_value=0.0, step=500.0)
            interest_rate = st.number_input("Monthly Byaaj Dar (%)", value=1.5, step=0.1)
            
        if st.form_submit_button("Record Save Karein"):
            if cust_name and loan_amt > 0 and weight > 0:
                prefix = "GL" if metal_type == "Gold" else "SL"
                loan_id = f"{prefix}-{entry_date.strftime('%Y')}-{sl_no:03d}"
                row_data = [
                    sl_no, loan_id, entry_date.strftime("%d/%m/%Y"), cust_name, phone,
                    metal_type, item_desc, weight, loan_amt, interest_rate, "Active", "", ""
                ]
                payload = {"action": "add_loan", "row": row_data}
                res = requests.post(API_URL, json=payload)
                st.success(f"{cust_name} ki entry ({loan_id}) Google Sheet mein save ho gayi!")
                st.rerun()
            else:
                st.error("Kripya sabhi zaroori fields (Naam, Weight, Amount) bharein.")

# ================= TAB 3: TOP-UP AMOUNT =================
with tab3:
    st.subheader("Puraney Loan par Rashi Badhayein")
    if not active_df.empty:
        topup_id = st.selectbox("Loan ID Chunein", active_df["Loan_ID"].tolist(), key="topup_id")
        rec = active_df[active_df["Loan_ID"] == topup_id].iloc[0]
        cur_amt = float(rec["Loan_Amount"])
        st.info(f"**Grahak:** {rec['Customer_Name']} | **Current Amount:** ₹{cur_amt:,.2f}")
        
        with st.form("topup_f"):
            c1, c2 = st.columns(2)
            with c1:
                t_date = st.date_input("Date", value=date.today())
                extra = st.number_input("Extra Paisa Badhana Hai (₹)*", min_value=100.0, step=500.0)
            with c2:
                new_total = cur_amt + extra
                st.markdown(f"**Naya Total Hoga:** ₹{new_total:,.2f}")
            if st.form_submit_button("Update Karein"):
                rem = f"{rec.get('Remarks', '')} | +₹{extra:,.0f} ({t_date.strftime('%d/%m/%Y')})".strip(" | ")
                payload = {"action": "update_loan", "loan_id": topup_id, "amount": new_total, "remarks": rem}
                requests.post(API_URL, json=payload)
                st.success(f"Amount badhakar ₹{new_total:,.2f} kar diya gaya!")
                st.rerun()
    else:
        st.info("Abhi koi Active loan uplabdh nahi hai.")

# ================= TAB 4: LOAN CLOSE =================
with tab4:
    st.subheader("Loan Chhudana / Status Closed Karna")
    if not active_df.empty:
        close_id = st.selectbox("Loan ID Chunein", active_df["Loan_ID"].tolist(), key="close_id")
        rec_close = active_df[active_df["Loan_ID"] == close_id].iloc[0]
        st.info(f"**Grahak:** {rec_close['Customer_Name']} | **Item:** {rec_close['Item_Description']}")
        
        with st.form("close_f"):
            c_date = st.date_input("Close Date", value=date.today())
            remarks_c = st.text_input("Remarks", value="Full settlement received, gold released")
            if st.form_submit_button("Loan Close Karein"):
                payload = {
                    "action": "update_loan", 
                    "loan_id": close_id, 
                    "status": "Closed", 
                    "close_date": c_date.strftime("%d/%m/%Y"), 
                    "remarks": remarks_c
                }
                requests.post(API_URL, json=payload)
                st.success("Loan closed ho gaya aur gold tijori se release mark ho gaya!")
                st.rerun()
    else:
        st.info("Abhi koi Active loan uplabdh nahi hai.")
