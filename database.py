import sqlite3
from datetime import datetime

DB_NAME = "loan_ledger.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Loans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINFO,
            customer_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            metal_type TEXT NOT NULL,       -- 'Gold' ya 'Silver'
            weight_grams REAL NOT NULL,
            carat TEXT NOT NULL,            -- e.g., '22K', '18K', '92.5%'
            principal_amount REAL NOT NULL,
            monthly_rate REAL NOT NULL,     -- % per month
            start_date TEXT NOT NULL,       -- YYYY-MM-DD
            status TEXT DEFAULT 'ACTIVE'    -- 'ACTIVE' ya 'CLOSED'
        )
    """)
    
    # Payments table (Interest & Principal Repayments)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER,
            amount_paid REAL NOT NULL,
            payment_type TEXT NOT NULL,     -- 'INTEREST' ya 'PRINCIPAL'
            payment_date TEXT NOT NULL,
            FOREIGN KEY(loan_id) REFERENCES loans(id)
        )
    """)
    conn.commit()
    conn.close()

def add_loan(name, phone, metal, weight, carat, principal, rate, start_date=None):
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO loans (customer_name, phone_number, metal_type, weight_grams, carat, principal_amount, monthly_rate, start_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, metal.capitalize(), weight, carat, principal, rate, start_date))
    conn.commit()
    conn.close()

def record_payment(loan_id, amount, payment_type):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payments (loan_id, amount_paid, payment_type, payment_date)
        VALUES (?, ?, ?, ?)
    """, (loan_id, amount, payment_type.upper(), today))
    conn.commit()
    conn.close()

def calculate_loan_statement(loan_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
    loan = cursor.fetchone()
    if not loan:
        conn.close()
        return None
    
    # Loan columns: id, name, phone, metal, weight, carat, principal, rate, start_date, status
    principal = loan[6]
    monthly_rate = loan[7]
    start_date = datetime.strptime(loan[8], "%Y-%m-%d")
    today = datetime.now()
    
    # Days elapsed -> Month calculation (1 month = 30 days basis)
    days_elapsed = (today - start_date).days
    months_elapsed = max(1, round(days_elapsed / 30, 2))  # Minimum 1 month default
    
    total_interest_due = round((principal * monthly_rate * months_elapsed) / 100, 2)
    
    # Get payments made
    cursor.execute("SELECT payment_type, SUM(amount_paid) FROM payments WHERE loan_id = ? GROUP BY payment_type", (loan_id,))
    payments = dict(cursor.fetchall())
    
    interest_paid = payments.get("INTEREST", 0.0)
    principal_paid = payments.get("PRINCIPAL", 0.0)
    
    current_principal = principal - principal_paid
    remaining_interest = total_interest_due - interest_paid
    
    conn.close()
    
    return {
        "loan_id": loan[0],
        "name": loan[1],
        "phone": loan[2],
        "metal": loan[3],
        "weight": loan[4],
        "carat": loan[5],
        "original_principal": principal,
        "current_principal": current_principal,
        "monthly_rate": monthly_rate,
        "start_date": loan[8],
        "days_elapsed": days_elapsed,
        "months_elapsed": months_elapsed,
        "total_interest_due": total_interest_due,
        "interest_paid": interest_paid,
        "remaining_interest": remaining_interest,
        "total_settlement_amount": current_principal + remaining_interest
    }

def search_loans(query):
    conn = get_connection()
    cursor = conn.cursor()
    search_term = f"%{query}%"
    cursor.execute("""
        SELECT id, customer_name, phone_number, metal_type, weight_grams, principal_amount, status
        FROM loans
        WHERE (customer_name LIKE ? OR phone_number LIKE ?) AND status = 'ACTIVE'
    """, (search_term, search_term))
    results = cursor.fetchall()
    conn.close()
    return results

def get_dashboard_summary():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Active gold & silver weights
    cursor.execute("""
        SELECT metal_type, SUM(weight_grams) 
        FROM loans 
        WHERE status = 'ACTIVE' 
        GROUP BY metal_type
    """)
    weights = dict(cursor.fetchall())
    
    # Total principal given in market
    cursor.execute("SELECT SUM(principal_amount) FROM loans WHERE status = 'ACTIVE'")
    total_given = cursor.fetchone()[0] or 0.0
    
    # Total principal recovered
    cursor.execute("""
        SELECT SUM(p.amount_paid) 
        FROM payments p 
        JOIN loans l ON p.loan_id = l.id 
        WHERE p.payment_type = 'PRINCIPAL' AND l.status = 'ACTIVE'
    """)
    total_recovered = cursor.fetchone()[0] or 0.0
    
    conn.close()
    
    return {
        "gold_weight": weights.get("Gold", 0.0),
        "silver_weight": weights.get("Silver", 0.0),
        "net_market_out": total_given - total_recovered
    }
