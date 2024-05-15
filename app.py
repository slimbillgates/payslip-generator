import os
from datetime import date, timedelta
from flask import Flask, render_template, request, send_file
from fpdf import FPDF

def calculate_tax(income):
    """Calculates income tax based on Australian tax brackets."""
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

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def payslip_form():
    if request.method == 'POST':
        num_payslips = int(request.form['num_payslips'])
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        business_name = request.form['business_name']
        abn = request.form['abn']
        address = request.form['address']
        annual_income = float(request.form['annual_income'])

        pdf_data = generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income)
        pdf_bytes = pdf_data.output(dest='S')
        
        # Use a unique filename to prevent caching issues
        filename = f"payslips_{date.today():%Y-%m-%d}.pdf" 
        
        response = send_file(pdf_bytes, mimetype='application/pdf', as_attachment=True, download_name=filename)

        # Add a Content-Disposition header to trigger the download
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    return render_template('payslip_form.html')


def generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income):
    super_rate = 0.11  # 11% superannuation
    today = date.today()
    financial_year_start = date(today.year - 1, 7, 1)
    pay_period_end = today - timedelta(days=today.weekday() + 1)

    fortnights_since_fy_start = (pay_period_end - financial_year_start).days // 14 + 1

    pdf = FPDF()  # Create a single PDF for all payslips

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

        # Create PDF (modify to match your desired format)
        pdf.add_page()
        pdf.set_font("Arial", size=10)  

        # Header
        pdf.set_font("Arial", "B", 12) 
        pdf.cell(0, 10, f"Payslip for {first_name} {last_name}", ln=True, align="C")
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 5, f"{business_name} - ABN: {abn}", ln=True, align="C")
        pdf.ln(5)

        # Pay Period and Dates
        pdf.cell(50, 8, "Pay Period:", border=1, align="L")
        pdf.cell(0, 8, f"{pay_period_start:%d/%m/%Y} - {pay_period_end:%d/%m/%Y}", border=1, ln=True, align="L")
        pdf.cell(50, 8, "Date Paid:", border=1, align="L")
        pdf.cell(0, 8, f"{pay_period_end + timedelta(days=1):%d/%m/%Y}", border=1, ln=True, align="L")
        pdf.ln(5)

        # Earnings and Deductions Table
        data = [
            ["Earnings", "", "Deductions", ""],
            ["Description", "Amount", "Description", "Amount"],
            ["Gross Pay", f"${fortnightly_gross:.2f}", "Tax", f"${fortnightly_tax:.2f}"],
            ["", "", "Superannuation", f"${fortnightly_super:.2f}"],
            ["", "", "", ""], 
            ["Total Earnings", f"${fortnightly_gross:.2f}", "Total Deductions", f"${fortnightly_tax + fortnightly_super:.2f}"]
        ]

        for row in data:
            for item in row:
                pdf.cell(47, 8, str(item), border=1, align="C")
            pdf.ln()

        # YTD Totals
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)  
        pdf.cell(0, 8, "Year-To-Date Totals:", ln=True, align="L")
        pdf.set_font("Arial", size=10)
        pdf.cell(50, 8, "YTD Gross:", border=1, align="L")
        pdf.cell(0, 8, f"${ytd_gross:.2f}", border=1, ln=True, align="L")
        pdf.cell(50, 8, "YTD Tax:", border=1, align="L")
        pdf.cell(0, 8, f"${ytd_tax:.2f}", border=1, ln=True, align="L")
        pdf.cell(50, 8, "YTD Super:", border=1, align="L")
        pdf.cell(0, 8, f"${ytd_super:.2f}", border=1, ln=True, align="L")

        # Net Pay
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(50, 8, "Net Pay:", border=1, align="L")
        pdf.cell(0, 8, f"${fortnightly_net:.2f}", border=1, ln=True, align="L")

        # Save to desktop
        pay_period_end -= timedelta(days=14)
        fortnights_since_fy_start -= 1
        return pdf



if __name__ == '__main__':
    app.run(debug=True)


