from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os
from config import Config
from models import db, ProcessedInvoice
from processor import InvoiceProcessor
from powerbi_client import PowerBIClient
from sqlalchemy import func
from datetime import datetime, timedelta


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Initialize processors
processor = InvoiceProcessor(app.config['AZURE_ENDPOINT'], app.config['AZURE_KEY'])
powerbi_client = PowerBIClient(
    app.config['POWER_BI_CLIENT_ID'],
    app.config['POWER_BI_CLIENT_SECRET'],
    app.config['POWER_BI_TENANT_ID']
)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    recent_invoices = ProcessedInvoice.query.order_by(ProcessedInvoice.upload_timestamp.desc()).limit(10).all()
    return render_template('index.html', invoices=recent_invoices)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Process the invoice
        result = processor.process_invoice(file.stream)

        # Save to database
        invoice = ProcessedInvoice(
            filename=filename,
            is_valid=result['success']
        )

        if result['success']:
            data = result['data']
            invoice.invoice_id = data.get('invoice_id')
            invoice.invoice_date = data.get('invoice_date')
            invoice.due_date = data.get('due_date')
            invoice.total_amount = data.get('total_amount')
            invoice.currency = data.get('currency')
            invoice.subtotal = data.get('subtotal')
            invoice.tax_amount = data.get('tax_amount')
            invoice.vendor_name = data.get('vendor_name')
            invoice.vendor_address = data.get('vendor_address')
            invoice.customer_name = data.get('customer_name')
            invoice.confidence_score = data.get('confidence_score')
            invoice.processing_time = data.get('processing_time')
        else:
            invoice.error_message = result['error']
            invoice.processing_time = result.get('processing_time', 0)

        db.session.add(invoice)
        db.session.commit()

        return jsonify({
            'success': result['success'],
            'invoice_id': invoice.id,
            'data': result.get('data', {}),
            'error': result.get('error')
        })

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/dashboard')
def dashboard():
    try:
        # Get basic counts
        total_invoices = ProcessedInvoice.query.count()

        # Get recent invoices
        recent_invoices = ProcessedInvoice.query.order_by(ProcessedInvoice.upload_timestamp.desc()).limit(5).all()

        # Simple totals
        total_amount = 0
        total_confidence = 0
        valid_invoices = 0

        for invoice in recent_invoices:
            if invoice.total_amount:
                total_amount += invoice.total_amount
            if invoice.confidence_score:
                total_confidence += invoice.confidence_score
                valid_invoices += 1

        avg_confidence = total_confidence / valid_invoices if valid_invoices > 0 else 0

        return render_template('dashboard.html',
                               total_invoices=total_invoices,
                               total_amount=total_amount,
                               avg_confidence=avg_confidence,
                               time_saved_hours=total_invoices * 0.25,  # Simple calculation
                               recent_invoices=recent_invoices,
                               vendor_names=['Microsoft', 'Amazon', 'Google'],
                               vendor_counts=[3, 2, 1],
                               daily_dates=['Mon', 'Tue', 'Wed', 'Thu'],
                               daily_counts=[1, 2, 1, total_invoices])

    except Exception as e:
        return f"Dashboard error: {str(e)}", 500
def api_data():
    """API endpoint for Power BI data refresh"""
    invoices = ProcessedInvoice.query.all()
    data = []

    for invoice in invoices:
        data.append({
            'InvoiceID': invoice.id,
            'FileName': invoice.filename,
            'VendorName': invoice.vendor_name or 'Unknown',
            'TotalAmount': invoice.total_amount or 0,
            'ProcessingTime': invoice.processing_time or 0,
            'ConfidenceScore': invoice.confidence_score or 0,
            'UploadDate': invoice.upload_timestamp.isoformat(),
            'IsValid': invoice.is_valid,
            'TimeSaved': max(0, 900 - (invoice.processing_time or 0)),  # 15 min baseline
            'CostSaving': max(0, 900 - (invoice.processing_time or 0)) * 0.25  # $15/hour
        })

    return jsonify(data)


@app.route('/api/summary')
def api_summary():
    """Summary statistics for dashboard"""
    total_invoices = ProcessedInvoice.query.count()
    total_amount = db.session.query(db.func.sum(ProcessedInvoice.total_amount)).scalar() or 0
    avg_confidence = db.session.query(db.func.avg(ProcessedInvoice.confidence_score)).scalar() or 0
    avg_processing_time = db.session.query(db.func.avg(ProcessedInvoice.processing_time)).scalar() or 0

    return jsonify({
        'total_invoices': total_invoices,
        'total_value': round(total_amount, 2),
        'avg_confidence': round(avg_confidence, 3),
        'avg_processing_time': round(avg_processing_time, 2),
        'time_saved_hours': round((total_invoices * 900 - (avg_processing_time * total_invoices)) / 3600, 1),
        'estimated_cost_savings': round((total_invoices * 900 - (avg_processing_time * total_invoices)) * 0.25 / 3600,
                                        2)
    })

@app.route('/dashboard-test')
def dashboard_test():
    # Dummy data for testing
    return render_template('./templates/dashboard.html',
                         total_invoices=25,
                         total_amount=45750.50,
                         avg_confidence=0.94,
                         time_saved_hours=8.5,
                         recent_invoices=[],  # Empty for now
                         vendor_names=['Microsoft', 'Amazon', 'Google', 'Adobe'],
                         vendor_counts=[8, 6, 5, 3],
                         daily_dates=['12/18', '12/19', '12/20', '12/21'],
                         daily_counts=[3, 5, 7, 4])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)