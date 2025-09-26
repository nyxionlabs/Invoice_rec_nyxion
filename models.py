from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ProcessedInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)

    # Basic Info
    invoice_id = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    due_date = db.Column(db.Date)

    # Financial Data
    total_amount = db.Column(db.Float)
    currency = db.Column(db.String(10))
    subtotal = db.Column(db.Float)
    tax_amount = db.Column(db.Float)

    # Vendor Info
    vendor_name = db.Column(db.String(255))
    vendor_address = db.Column(db.Text)

    # Customer Info
    customer_name = db.Column(db.String(255))

    # Processing Metadata
    confidence_score = db.Column(db.Float)
    processing_time = db.Column(db.Float)  # in seconds
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    processing_method = db.Column(db.String(50), default='azure-form-recognizer')

    # Status
    is_valid = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'invoice_id': self.invoice_id,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'total_amount': self.total_amount,
            'vendor_name': self.vendor_name,
            'confidence_score': self.confidence_score,
            'processing_time': self.processing_time,
            'upload_timestamp': self.upload_timestamp.isoformat()
        }