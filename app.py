import io  # For working with in-memory bytes
from datetime import date, timedelta
from flask import Flask, render_template, request, send_file
from fpdf import FPDF

# --- Tax Calculation Function ---

def calculate_tax(income):
    # ... (Tax calculation logic remains the same)

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

        # Reset file pointer for reading
        pdf_bytes.seek(0)

        # Create filename (to prevent caching)
        filename = f"payslips_{date.today():%Y-%m-%d}.pdf"

        # Send PDF as a download
        response = send_file(pdf_bytes, mimetype='application/pdf', as_attachment=True, download_name=filename)
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'  # Trigger download
        return response

    return render_template('payslip_form.html')  # Render the form for GET requests



# --- Payslip Generation Function ---

def generate_payslips(num_payslips, first_name, last_name, business_name, abn, address, annual_income):
    # ... (Payslip content generation logic remains the same, but returns the FPDF object)

# --- Main Application ---

if __name__ == '__main__':
    app.run(debug=True) 

