import io
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

            pdf_data = generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income)
            
            # Output PDF to bytes
            pdf_bytes = io.BytesIO()
            pdf_data.output(pdf_bytes, dest='S')
            pdf_bytes.seek(0)

            filename = f"payslips_{date.today():%Y-%m-%d}.pdf"
            response = send_file(pdf_bytes, mimetype='application/pdf', as_attachment=True, download_name=filename)
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:  # Add error handling
            return f"Error generating PDF: {str(e)}", 500

    return render_template('payslip_form.html')  # Render the form


# --- Payslip Generation Function ---

def generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income):
    super_rate = 0.11  
    today = date.today()
    financial_year_start = date(today.year - 1, 7, 1)
    pay_period_end = today - timedelta(days=today.weekday() + 1) 
    fortnights_since_fy_start = (pay_period_end - financial_year_start).days // 14 + 1

    pdf = FPDF()  

    # --- Loop to Generate Multiple Payslips ---
    for _ in range(num_payslips):
        pay_period_start = pay_period_end - timedelta(days=13)
        fortnightly_gross = annual_income / 26
        ytd_taxable_income = (annual_income - (annual_income * super_rate)) * fortnights_since_fy_start / 26
        fortnightly_tax = calculate_tax(ytd_taxable_income)
        fortnightly_super = fortnightly_gross * super_rate
        fortnightly_net = fortnightly_gross - fortnightly_tax - fortnightly_super

        ytd_gross = fortnightly_gross * fortnights_since_fy_start
        ytd_tax = calculate_tax(ytd_gross)
        ytd_super = ytd_gross * super_rate

        # --- Detailed PDF Content Generation for ONE Payslip ---
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Payslip for {first_name} {last_name}", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"{business_name} - ABN: {abn}", ln=True, align="C")
        pdf.cell(0, 5, address, ln=True, align="C")
        pdf.ln(10)

        # Pay Period and Dates
        pdf.cell(0, 8, f"Pay Period: {pay_period_start:%d/%m/%Y} - {pay_period_end:%d/%m/%Y}", ln=True)
        pdf.cell(0, 8, f"Date Paid: {pay_period_end + timedelta(days=1):%d/%m/%Y}", ln=True)
        pdf.ln(5)

        # Earnings and Deductions Table
        data = [
            ["Earnings", "", "Deductions", ""],
            ["Description", "Amount", "Description", "Amount"],
            ["Gross Pay", f"${fortnightly_gross:.2f}", "Tax", f"${fortnightly_tax:.2f}"],
            ["", "", "Superannuation", f"${fortnightly_super:.2f}"],
            ["", "", "", ""],  # Empty row for spacing
            ["Total Earnings", f"${fortnightly_gross:.2f}", "Total Deductions", f"${fortnightly_tax + fortnightly_super:.2f}"]
        ]

        for row in data:
            for item in row:
                pdf.cell(47, 8, str(item), border=1, align="C")
            pdf.ln()

        # YTD Totals
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, "Year-To-Date Totals:", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(50, 8, "YTD Gross:", border=1)
        pdf.cell(0, 8, f"${ytd_gross:.2f}", border=1, ln=True)
        pdf.cell(50, 8, "YTD Tax:", border=1)
        pdf.cell(0, 8, f"${ytd_tax:.2f}", border=1, ln=True)
        pdf.cell(50, 8, "YTD Super:", border=1)
        pdf.cell(0, 8, f"${ytd_super:.2f}", border=1, ln=True)

        # Net Pay
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(50, 8, "Net Pay:", border=1)
        pdf.cell(0, 8, f"${fortnightly_net:.2f}", border=1, ln=True)
        pdf.ln(10)

        # Update Dates for Next Payslip in the Loop
        pay_period_end -= timedelta(days=14)
        fortnights_since_fy_start -= 1


    return pdf # Return the FPDF object after all payslips are generated


# --- Main Application ---
if __name__ == '__main__':
    app.run(debug=True)


