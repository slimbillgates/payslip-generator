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
        # Get form data
        num_payslips = int(request.form['num_payslips'])
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        business_name = request.form['business_name']
        abn = request.form['abn']
        address = request.form['address']
        annual_income = float(request.form['annual_income'])

        # Generate PDF in memory
        pdf_bytes = io.BytesIO()
        pdf_data = generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income)
        pdf_data.output(pdf_bytes, dest='S')
        pdf_bytes.seek(0)

        filename = f"payslips_{date.today():%Y-%m-%d}.pdf"
        response = send_file(pdf_bytes, mimetype='application/pdf', as_attachment=True, download_name=filename)
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return render_template('payslip_form.html')

# --- Payslip Generation Function ---
def generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income):
    super_rate = 0.11  
    today = date.today()
    financial_year_start = date(today.year - 1, 7, 1)
    pay_period_end = today - timedelta(days=today.weekday() + 1) 
    fortnights_since_fy_start = (pay_period_end - financial_year_start).days // 14 + 1

    pdf = FPDF()  

    for i in range(num_payslips):
        pay_period_start = pay_period_end - timedelta(days=13)
        fortnightly_gross = annual_income / 26
        ytd_taxable_income = (annual_income - (annual_income * super_rate)) * fortnights_since_fy_start / 26
        fortnightly_tax = calculate_tax(ytd_taxable_income)
        fortnightly_super = fortnightly_gross * super_rate
        fortnightly_net = fortnightly_gross - fortnightly_tax - fortnightly_super

        ytd_gross = fortnightly_gross * fortnights_since_fy_start
        ytd_tax = calculate_tax(ytd_gross)
        ytd_super = ytd_gross * super_rate

        # --- PDF Content Generation (You can customize this part) ---
        pdf.add_page()
        # ... (rest of your PDF generation logic for headers, tables, etc.)

        pay_period_end -= timedelta(days=14)
        fortnights_since_fy_start -= 1
    
    return pdf  


# --- Main Application ---
if __name__ == '__main__':
    app.run(debug=True) 

