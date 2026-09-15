from database import init_db, add_loan, record_payment, calculate_loan_statement, search_loans, get_dashboard_summary

def main():
    init_db()
    while True:
        print("\n===============================")
        print("  GOLD & SILVER LOAN LEDGER")
        print("===============================")
        print("1. Dashboard Summary (Total Gold/Silver & Market Cash)")
        print("2. Naya Loan Add Karein")
        print("3. Customer Search Karein (Name ya Phone)")
        print("4. Customer Statement / Hisab Dekhein")
        print("5. Payment Entry (Interest / Principal Jama Karein)")
        print("6. Exit")
        
        choice = input("\nOption chunein (1-6): ").strip()
        
        if choice == "1":
            summary = get_dashboard_summary()
            print("\n--- VYAPAR SUMMARY ---")
            print(f"Total Active Gold Girvi  : {summary['gold_weight']:.2f} grams")
            print(f"Total Active Silver Girvi: {summary['silver_weight']:.2f} grams")
            print(f"Total Market Out (Cash)  : Rs. {summary['net_market_out']:,.2f}")

        elif choice == "2":
            print("\n--- NAYA LOAN FORM ---")
            name = input("Customer Ka Naam: ").strip()
            phone = input("Phone Number: ").strip()
            metal = input("Metal Type (Gold / Silver): ").strip()
            weight = float(input("Wajan (Grams): "))
            carat = input("Purity / Carat (e.g. 22K / 92.5%): ").strip()
            principal = float(input("Loan Amount (Rupaye): "))
            rate = float(input("Monthly Interest Rate (% per month): "))
            
            add_loan(name, phone, metal, weight, carat, principal, rate)
            print(">> Loan Entry Safalta Se Save Ho Gayi!")

        elif choice == "3":
            query = input("\nSearch Name ya Mobile No dalein: ").strip()
            results = search_loans(query)
            if not results:
                print(">> Koi active record nahi mila.")
            else:
                print(f"\nFound {len(results)} record(s):")
                print("-" * 65)
                print(f"{'ID':<4} | {'Name':<15} | {'Phone':<12} | {'Metal':<6} | {'Wt(g)':<6} | {'Principal':<10}")
                print("-" * 65)
                for r in results:
                    print(f"{r[0]:<4} | {r[1]:<15} | {r[2]:<12} | {r[3]:<6} | {r[4]:<6} | Rs.{r[5]:<9}")
                print("-" * 65)

        elif choice == "4":
            loan_id = input("\nLoan ID enter karein: ").strip()
            if not loan_id.isdigit():
                print("Invalid Loan ID")
                continue
            stmt = calculate_loan_statement(int(loan_id))
            if not stmt:
                print(">> Loan ID nahi mili.")
                continue
            
            print("\n" + "=" * 45)
            print(f"LOAN STATEMENT: #{stmt['loan_id']}")
            print("=" * 45)
            print(f"Customer Name     : {stmt['name']} ({stmt['phone']})")
            print(f"Girvi Saman       : {stmt['metal']} - {stmt['weight']}g ({stmt['carat']})")
            print(f"Start Date        : {stmt['start_date']} ({stmt['days_elapsed']} din huye)")
            print(f"Original Principal: Rs. {stmt['original_principal']:,.2f}")
            print(f"Current Principal : Rs. {stmt['current_principal']:,.2f}")
            print(f"Byaj Rate         : {stmt['monthly_rate']}% per month")
            print("-" * 45)
            print(f"Kul Byaj Banta Hai: Rs. {stmt['total_interest_due']:,.2f}")
            print(f"Byaj Jama Hua     : Rs. {stmt['interest_paid']:,.2f}")
            print(f"Baki Byaj         : Rs. {stmt['remaining_interest']:,.2f}")
            print("-" * 45)
            print(f"KUL DENA (PAYOFF) : Rs. {stmt['total_settlement_amount']:,.2f}")
            print("=" * 45)

        elif choice == "5":
            loan_id = input("\nLoan ID dalein: ").strip()
            if not loan_id.isdigit():
                print("Invalid Loan ID")
                continue
            amount = float(input("Kitna rupaya jama karna hai: "))
            p_type = input("Payment Type chunein (1 for INTEREST, 2 for PRINCIPAL): ").strip()
            type_str = "INTEREST" if p_type == "1" else "PRINCIPAL"
            
            record_payment(int(loan_id), amount, type_str)
            print(f">> Rs. {amount} jama ho gaya ({type_str}).")

        elif choice == "6":
            print("\nExiting. Dhanyawad!")
            break

if __name__ == "__main__":
    main()
