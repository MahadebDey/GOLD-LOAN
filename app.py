import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Sovaa Gold & Silver Loan Manager", layout="wide", page_icon="🪙")

# ==================== 1. SECURITY & LOGIN ====================
# Yahan apna pasandida Password ya PIN set karein:
APP_PIN = "1234"  # <-- Ise apni pasand ke PIN se badal lein

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Sovaa Jewellers - Secure Login")
    pin_input = st.text_input("Enter Master PIN / Password:", type="password")
    if st.button("Unlock System"):
        if pin_input == APP_PIN:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Galat Password / PIN! Access Denied.")
    st.stop()

# Logout Option Sidebar mein
with st.sidebar:
    st.write("Logged in: **Owner**")
    if st.button("Logout 🔒"):
        st.session_state["authenticated"] = False
        st.rerun()

# ==================== 2. DATA CONNECTION ====================
API_URL = "https://script.google.com/macros/s/AKfycbxAkdWvO9cEg_BdruMFHvlsXLpLZGYI1nP8bR74uvpU8w70W_2d2lTq3popU0sz-Euspg/exec"

def load_data():
    try:
        res = requests.get(API_URL, timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except Exception as e:
        st.error(f"Data fetch error: {e}")
    return pd.DataFrame()

df = load_data()

if not df.empty:
    if "Weight_gm" in df.columns:
        df["Weight_gm"] = pd.to_numeric(df["Weight_gm"], errors="coerce").fillna(0.0)
    if "Loan_Amount" in df.columns:
        df["Loan_Amount"] = pd.to_numeric(df["Loan_Amount"], errors="coerce").fillna(0.0)
    if "Monthly_Interest_Rate" in df.columns:
        df["Monthly_Interest_Rate"] = pd.to_numeric(df["Monthly_Interest_Rate"], errors="coerce").fillna(1.5)

# ==================== 3. LIVE DASHBOARD ====================
st.title("🪙 Gold & Silver Loan Manager")

active_df = df[df["Status"] == "Active"] if (not df.empty and "Status" in df.columns) else pd.DataFrame()
active_gold_wt = active_df[active_df["Metal_Type"] == "Gold"]["Weight_gm"].sum() if not active_df.empty else 0.0
active_silver_wt = active_df[active_df["Metal_Type"] == "Silver"]["Weight_gm"].sum() if not active_df.empty else 0.0
active_loan_amount = active_df["Loan_Amount"].sum() if not active_df.empty else 0.0
total_disbursed = df["Loan_Amount"].sum() if (not df.empty and "Loan_Amount" in df.columns) else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("🟡 Tijori mein Gold (Active)", f"{active_gold_wt:,.3f} gm")
col2.metric("⚪ Tijori mein Silver (Active)", f"{active_silver_wt:,.3f} gm")
col3.metric("💰 Market mein Bacha Paisa", f"₹ {active_loan_amount:,.2f}")
col4.metric("📈 Aaj tak Kul Diya Loan", f"₹ {total_disbursed:,.2f}")

st.divider()

# ==================== 4. TABS ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Search & Ledger", 
    "➕ Nayi Loan Entry", 
    "✏️ Galat Entry Sudharein (Edit)", 
    "📈 Amount Badhayein (Top-up)", 
    "🔒 Loan Close / Settle"
])

# ----------------- TAB 1: ADVANCED SEARCH & LEDGER -----------------
with tab1:
    st.subheader("Bahi-Khata aur Khoj (Search)")
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            search_name = st.text_input("Grahak ke Naam se khojein:")
            search_phone = st.text_input("Mobile Number se khojein:")
        with c2:
            search_date = st.text_input("Taareekh se khojein (e.g. 31/07/2024):")
            search_amount = st.text_input("Loan Amount (₹) se khojein:")
        with c3:
            s_filter = st.selectbox("Status Filter", ["All", "Active", "Closed"])
            m_filter = st.selectbox("Metal Filter", ["All", "Gold", "Silver"])

        filtered = df.copy()
        if search_name:
            filtered = filtered[filtered["Customer_Name"].astype(str).str.contains(search_name, case=False, na=False)]
        if search_phone:
            filtered = filtered[filtered["Phone_Number"].astype(str).str.contains(search_phone, na=False)]
        if search_date:
            filtered = filtered[filtered["Date"].astype(str).str.contains(search_date, na=False)]
        if search_amount:
            filtered = filtered[filtered["Loan_Amount"].astype(str).str.contains(search_amount, na=False)]
        if s_filter != "All":
            filtered = filtered[filtered["Status"] == s_filter]
        if m_filter != "All":
            filtered = filtered[filtered["Metal_Type"] == m_filter]

        st.dataframe(filtered, use_container_width=True)
        st.caption(f"Kul Entries Found: {len(filtered)}")
    else:
        st.info("Koi data uplabdh nahi hai.")

# ----------------- TAB 2: NAYI ENTRY -----------------
with tab2:
    st.subheader("Naya Loan Register Karein")
    with st.form("new_entry_form", clear_on_submit=True):
        ca, cb = st.columns(2)
        with ca:
            sl_no = len(df) + 1
            st.text(f"Serial No: {sl_no}")
            cust_name = st.text_input("Grahak ka Naam*")
            phone = st.text_input("Mobile Number")
            metal_type = st.selectbox("Metal Type*", ["Gold", "Silver"])
            item_desc = st.text_input("Gehne ka Vivaran*")
        with cb:
            entry_date = st.date_input("Date", value=date.today())
            weight = st.number_input("Weight (gm)*", min_value=0.000, step=0.001, format="%.3f")
            loan_amt = st.number_input("Loan Amount (₹)*", min_value=0.0, step=500.0)
            interest_rate = st.number_input("Monthly Byaaj Dar (%)*", value=1.5, step=0.1)
            
        if st.form_submit_button("Record Save Karein"):
            if cust_name and loan_amt > 0 and weight > 0:
                prefix = "GL" if metal_type == "Gold" else "SL"
                loan_id = f"{prefix}-{entry_date.strftime('%Y')}-{sl_no:03d}"
                row_data = [
                    sl_no, loan_id, entry_date.strftime("%d/%m/%Y"), cust_name, phone,
                    metal_type, item_desc, weight, loan_amt, interest_rate, "Active", "", ""
                ]
                requests.post(API_URL, json={"action": "add_loan", "row": row_data})
                st.success(f"{cust_name} ({loan_id}) save ho gaya!")
                st.rerun()

# ----------------- TAB 3: GALAT ENTRY EDIT KARNA -----------------
with tab3:
    st.subheader("Galat Entry Sudharein / Byaaj Dar (Rate) Badalna")
    if not df.empty:
        # User kisi bhi entry ko select kar sakta hai
        loan_choices = [f"{r['Loan_ID']} | {r['Customer_Name']} ({r['Date']})" for _, r in df.iterrows()]
        selected_choice = st.selectbox("Sudharne ke liye Loan Chunein", loan_choices)
        selected_loan_id = selected_choice.split(" | ")[0]
        rec = df[df["Loan_ID"] == selected_loan_id].iloc[0]

        with st.form("edit_form"):
            e1, e2 = st.columns(2)
            with e1:
                e_date = st.text_input("Date (DD/MM/YYYY)", value=str(rec.get("Date", "")))
                e_name = st.text_input("Customer Name", value=str(rec.get("Customer_Name", "")))
                e_phone = st.text_input("Phone Number", value=str(rec.get("Phone_Number", "")))
                e_metal = st.selectbox("Metal Type", ["Gold", "Silver"], index=0 if rec.get("Metal_Type") == "Gold" else 1)
                e_item = st.text_input("Item Details", value=str(rec.get("Item_Description", "")))
            with e2:
                e_wt = st.number_input("Weight (gm)", value=float(rec.get("Weight_gm", 0.0)), step=0.001, format="%.3f")
                e_amt = st.number_input("Loan Amount (₹)", value=float(rec.get("Loan_Amount", 0.0)), step=500.0)
                e_rate = st.number_input("Monthly Interest Rate (%)", value=float(rec.get("Monthly_Interest_Rate", 1.5)), step=0.1)
                e_status = st.selectbox("Status", ["Active", "Closed"], index=0 if rec.get("Status") == "Active" else 1)
                e_close = st.text_input("Close Date", value=str(rec.get("Close_Date", "")))
                e_remarks = st.text_input("Remarks", value=str(rec.get("Remarks", "")))

            if st.form_submit_button("Sudhar (Update) Save Karein"):
                updated_row = [
                    rec.get("Serial_No", 1),
                    selected_loan_id,
                    e_date,
                    e_name,
                    e_phone,
                    e_metal,
                    e_item,
                    e_wt,
                    e_amt,
                    e_rate,
                    e_status,
                    e_close,
                    e_remarks
                ]
                requests.post(API_URL, json={"action": "edit_loan", "loan_id": selected_loan_id, "row": updated_row})
                st.success(f"{selected_loan_id} ka record safaltapoorvak update ho gaya!")
                st.rerun()

# ----------------- TAB 4: TOP-UP AMOUNT -----------------
with tab4:
    st.subheader("Puraney Loan par Rashi Badhayein")
    if not active_df.empty:
        top_id = st.selectbox("Loan ID", active_df["Loan_ID"].tolist(), key="t_id")
        r_top = active_df[active_df["Loan_ID"] == top_id].iloc[0]
        cur_amt = float(r_top["Loan_Amount"])
        st.info(f"**Grahak:** {r_top['Customer_Name']} | **Puraana Amount:** ₹{cur_amt:,.2f}")
        
        with st.form("top_f"):
            extra_amt = st.number_input("Extra Rashi Badhayein (₹)", min_value=100.0, step=500.0)
            if st.form_submit_button("Amount Update Karein"):
                n_tot = cur_amt + extra_amt
                r_top_list = r_top.tolist()
                r_top_list[8] = n_tot # Loan_Amount index
                r_top_list[12] = f"{r_top.get('Remarks', '')} | +₹{extra_amt:,.0f} ({date.today().strftime('%d/%m/%Y')})".strip(" | ")
                requests.post(API_URL, json={"action": "edit_loan", "loan_id": top_id, "row": r_top_list})
                st.success("Amount barabar update ho gaya!")
                st.rerun()

# ----------------- TAB 5: LOAN CLOSE -----------------
with tab5:
    st.subheader("Loan Chhudana / Close Karna")
    if not active_df.empty:
        c_id = st.selectbox("Loan ID Chunein", active_df["Loan_ID"].tolist(), key="c_id")
        r_cls = active_df[active_df["Loan_ID"] == c_id].iloc[0]
        st.info(f"**Grahak:** {r_cls['Customer_Name']} | **Item:** {r_cls['Item_Description']}")
        with st.form("c_f"):
            cls_date = st.date_input("Close Date", value=date.today())
            cls_rem = st.text_input("Remarks", value="Full settlement received, gold released")
            if st.form_submit_button("Loan Closed Karein"):
                r_cls_list = r_cls.tolist()
                r_cls_list[10] = "Closed" # Status index
                r_cls_list[11] = cls_date.strftime("%d/%m/%Y") # Close_Date index
                r_cls_list[12] = cls_rem # Remarks index
                requests.post(API_URL, json={"action": "edit_loan", "loan_id": c_id, "row": r_cls_list})
                st.success("Loan closed ho gaya!")
                st.rerun()
