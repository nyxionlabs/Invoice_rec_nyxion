from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import sqlite3
import random
from datetime import datetime
from werkzeug.utils import secure_filename
import time
from config import Config
from models import db, ProcessedInvoice
from processor import InvoiceProcessor

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database with app
db.init_app(app)

# Ensure uploads folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Azure processor
invoice_processor = InvoiceProcessor(Config.AZURE_ENDPOINT, Config.AZURE_KEY)

@app.before_first_request
def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def index():
    invoices = ProcessedInvoice.query.order_by(ProcessedInvoice.upload_timestamp.desc()).limit(10).all()
    return render_template('index.html', invoices=invoices)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Process invoice
    with open(filepath, "rb") as f:
        result = invoice_processor.process_invoice(f)

    if not result['success']:
        invoice = ProcessedInvoice(filename=filename, is_valid=False, error_message=result['error'],
                                   processing_time=result['processing_time'])
        db.session.add(invoice)
        db.session.commit()
        return jsonify({'error': result['error']}), 500

    data = result['data']
    invoice = ProcessedInvoice(
        filename=filename,
        invoice_id=data.get('invoice_id'),
        invoice_date=data.get('invoice_date'),
        due_date=data.get('due_date'),
        total_amount=data.get('total_amount'),
        currency=data.get('currency'),
        subtotal=data.get('subtotal'),
        tax_amount=data.get('tax_amount'),
        vendor_name=data.get('vendor_name'),
        vendor_address=data.get('vendor_address'),
        customer_name=data.get('customer_name'),
        confidence_score=data.get('confidence_score'),
        processing_time=data.get('processing_time')
    )
    db.session.add(invoice)
    db.session.commit()

    return jsonify({'success': True, 'data': invoice.to_dict()})

@app.route('/dashboard')
def dashboard():
    invoices = ProcessedInvoice.query.order_by(ProcessedInvoice.upload_timestamp.desc()).limit(10).all()
    total_invoices = ProcessedInvoice.query.count()
    total_amount = db.session.query(db.func.coalesce(db.func.sum(ProcessedInvoice.total_amount), 0)).scalar()
    avg_confidence = db.session.query(db.func.coalesce(db.func.avg(ProcessedInvoice.confidence_score), 0)).scalar()
    avg_time = db.session.query(db.func.coalesce(db.func.avg(ProcessedInvoice.processing_time), 0)).scalar()

    time_saved_hours = (total_invoices * 15 - (avg_time * total_invoices / 60)) / 60

    return render_template('dashboard.html',
                           total_invoices=total_invoices,
                           total_amount=total_amount,
                           avg_confidence=avg_confidence,
                           time_saved_hours=max(0, time_saved_hours),
                           recent_invoices=invoices)


@app.route('/ai-demo')
def ai_demo():
    try:
        total_invoices = ProcessedInvoice.query.count()
        avg_confidence = db.session.query(db.func.coalesce(db.func.avg(ProcessedInvoice.confidence_score), 0)).scalar()
        avg_time = db.session.query(db.func.coalesce(db.func.avg(ProcessedInvoice.processing_time), 0)).scalar()

        return render_template('ai_demo.html',
                               total_invoices=total_invoices,
                               avg_confidence=avg_confidence * 100 if avg_confidence else 0,
                               avg_time=avg_time or 0)
    except Exception as e:
        return f"Demo Error: {str(e)}"

@app.route('/api/process-demo', methods=['POST'])
def process_demo():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Process invoice using your existing processor
        with open(filepath, "rb") as f:
            result = invoice_processor.process_invoice(f)

        if result['success']:
            data = result['data']
            demo_data = {
                'vendor_name': data.get('vendor_name') or 'N/A',
                'total_amount': f"${data.get('total_amount', 0):.2f}" if data.get('total_amount') else 'N/A',
                'invoice_id': data.get('invoice_id') or 'N/A',
                'invoice_date': data.get('invoice_date').strftime('%Y-%m-%d') if data.get('invoice_date') else 'N/A',
                'due_date': data.get('due_date').strftime('%Y-%m-%d') if data.get('due_date') else 'N/A',
                'subtotal': f"${data.get('subtotal', 0):.2f}" if data.get('subtotal') else 'N/A',
                'tax_amount': f"${data.get('tax_amount', 0):.2f}" if data.get('tax_amount') else 'N/A',
                'confidence_score': f"{data.get('confidence_score', 0) * 100:.1f}" if data.get('confidence_score') else 'N/A',
                'processing_time': f"{data.get('processing_time', 0):.1f}"
            }
            return jsonify({'success': True, 'data': demo_data})
        else:
            return jsonify({'success': False, 'error': result['error']}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- move these OUTSIDE of process_demo ---
@app.route('/test')
def test():
    return "Flask app is working!"

@app.route('/health')
def health():
    return "OK", 200
# --- end patch ---


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)