import io
import tempfile
import os
from datetime import date, timedelta
from flask import Flask, render_template, request, send_file
from fpdf import FPDF

# --- Tax Calculation Function ---

def calculate_tax(income):
    if 0 <= income <= 18200:
        return 0
    elif 18201 <= income <= 45000:
        return 0.19 * (income - 18200)
    elif 45001 <= income <= 120000:
        return 5092 + 0.325 * (income - 45000)
    elif 120001 <= income <= 180000:
        return 29467 + 0.37 * (income - 120000)
    else:
        return 51667 + 0.45 * (income - 180000)

# --- Flask Application Setup ---

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def payslip_form():
    if request.method == 'POST':
        try:
            # Get form data
            num_payslips = int(request.form['num_payslips'])
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            business_name = request.form['business_name']
            abn = request.form['abn']
            address = request.form['address']
            annual_income = float(request.form['annual_income'])

            pdf = generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income)
            # Write to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                pdf.output(temp.name, 'F') 

            # Send the temporary file 
            try:
                response = send_file(temp.name, as_attachment=True, download_name=f"payslips_{date.today():%Y-%m-%d}.pdf")
                response.headers["Content-Type"] = "application/pdf"
                return response
            finally:
                # Clean up the temporary file
                os.remove(temp.name)
        except Exception as e:
            app.logger.error(f"Error generating payslip(s): {str(e)}")  
            return f"Error generating payslip(s): {str(e)}", 500

    return render_template('payslip_form.html')  # Render the form for GET requests

# --- Payslip Generation Function ---

def generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income):
    super_rate = 0.11
    today = date.today()
    financial_year_start = date(today.year - 1, 7, 1)
    pay_period_end = today - timedelta(days=today.weekday() + 1)  
    original_fortnights_since_fy_start = (pay_period_end - financial_year_start).days // 14 + 1

    pdf = FPDF()  
    pdf.set_margins(20, 15, 20) # Set margins for the document

    # --- Loop to Generate Multiple Payslips ---
    for _ in range(num_payslips):
        pay_period_start = pay_period_end - timedelta(days=13)  # Start of this pay period

        # Calculations (same as before)
        fortnightly_gross = annual_income / 26
        ytd_taxable_income = (annual_income - (annual_income * super_rate)) * original_fortnights_since_fy_start / 26
        fortnightly_tax = calculate_tax(ytd_taxable_income)
        fortnightly_super = fortnightly_gross * super_rate
        fortnightly_net = fortnightly_gross - fortnightly_tax - fortnightly_super

        # Calculate YTD totals for display
        ytd_gross = fortnightly_gross * original_fortnights_since_fy_start
        ytd_tax = calculate_tax(ytd_gross)
        ytd_super = ytd_gross * super_rate


        # --- Detailed PDF Content Generation for ONE Payslip ---
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Payslip for {first_name} {last_name}", ln=True, align="C")
        pdf.set_font("Arial", "", 10)

        # Business Details (with line breaks for clarity)
        pdf.cell(0, 5, f"{business_name}", ln=True, align="C")
        pdf.cell(0, 5, f"ABN: {abn}", ln=True, align="C")
        pdf.cell(0, 5, address, ln=True, align="C")
        pdf.ln(10)  # Add spacing

        # Pay Period and Date Paid
        pdf.cell(0, 10, f"Pay Period: {pay_period_start:%d/%m/%Y} - {pay_period_end:%d/%m/%Y}", ln=True)
        pdf.cell(0, 10, f"Date Paid: {pay_period_end + timedelta(days=1):%d/%m/%Y}", ln=True)
        pdf.ln(10)

        # Earnings and Deductions Table
        pdf.set_font("Arial", "B", 10)
        pdf.cell(95, 8, "Earnings", border=1, align="C")
        pdf.cell(95, 8, "Deductions", border=1, align="C", ln=1)
        pdf.set_font("Arial", "", 10)
        pdf.cell(95, 8, "Description", border=1, align="C")
        pdf.cell(95, 8, "Amount", border=1, align="C", ln=1)
        pdf.cell(95, 8, "Gross Pay", border=1)
        pdf.cell(95, 8, f"${fortnightly_gross:.2f}", border=1, ln=1)
        pdf.cell(95, 8, "Tax", border=1)
        pdf.cell(95, 8, f"${fortnightly_tax:.2f}", border=1, ln=1)
        pdf.cell(95, 8, "Superannuation", border=1)
        pdf.cell(95, 8, f"${fortnightly_super:.2f}", border=1, ln=1)

        # Total Earnings and Deductions
        pdf.set_font("Arial", "B", 10)
        pdf.cell(95, 8, "Total Earnings", border=1, align="C")
        pdf.cell(95, 8, f"${fortnightly_gross:.2f}", border=1, align="C", ln=1)
        pdf.cell(95, 8, "Total Deductions", border=1, align="C")
        pdf.cell(95, 8, f"${fortnightly_tax + fortnightly_super:.2f}", border=1, align="C", ln=1)
        pdf.ln(10)

        # YTD Totals
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, "Year-To-Date Totals:", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(95, 8, "YTD Gross:", border=1)
        pdf.cell(95, 8, f"${ytd_gross:.2f}", border=1, ln=1)
        pdf.cell(95, 8, "YTD Tax:", border=1)
        pdf.cell(95, 8, f"${ytd_tax:.2f}", border=1, ln=1)
        pdf.cell(95, 8, "YTD Super:", border=1)
        pdf.cell(95, 8, f"${ytd_super:.2f}", border=1, ln=1)

        # Net Pay
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(95, 10, "Net Pay:", border=1)
        pdf.cell(95, 10, f"${fortnightly_net:.2f}", border=1, ln=1)

        # Update for next pay period
        pay_period_end -= timedelta(days=14)
        original_fortnights_since_fy_start -= 1
    
    return pdf 


# --- Main Application ---
if __name__ == '__main__':
    app.run(debug=True)




