from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import time
from datetime import datetime


class InvoiceProcessor:
    def __init__(self, endpoint, key):
        self.client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

    def process_invoice(self, file_stream):
        start_time = time.time()

        try:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-invoice",
                document=file_stream
            )
            result = poller.result()
            processing_time = time.time() - start_time

            if not result.documents:
                return {
                    'success': False,
                    'error': 'No invoice detected',
                    'processing_time': processing_time
                }

            invoice = result.documents[0]

            return {
                'success': True,
                'data': {
                    'invoice_id': self._extract_field(invoice, 'InvoiceId'),
                    'invoice_date': self._extract_date(invoice, 'InvoiceDate'),
                    'due_date': self._extract_date(invoice, 'DueDate'),
                    'total_amount': self._extract_amount(invoice, 'InvoiceTotal'),
                    'currency': self._extract_field(invoice, 'CurrencyCode') or 'USD',
                    'subtotal': self._extract_amount(invoice, 'SubTotal'),
                    'tax_amount': self._extract_amount(invoice, 'TotalTax'),
                    'vendor_name': self._extract_field(invoice, 'VendorName'),
                    'vendor_address': str(self._extract_field(invoice, 'VendorAddress') or ''),
                    'customer_name': self._extract_field(invoice, 'CustomerName'),
                    'confidence_score': invoice.confidence,
                    'processing_time': processing_time
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }

    def _extract_field(self, invoice, field_name):
        try:
            field = invoice.fields.get(field_name)
            return field.value if field and hasattr(field, 'value') else None
        except:
            return None

    def _extract_amount(self, invoice, field_name):
        try:
            field = invoice.fields.get(field_name)
            if field and hasattr(field, 'value') and field.value:
                if hasattr(field.value, 'amount'):
                    return float(field.value.amount)
                return float(field.value)
        except:
            pass
        return None

    def _extract_date(self, invoice, field_name):
        try:
            field = invoice.fields.get(field_name)
            if field and hasattr(field, 'value') and field.value:
                if hasattr(field.value, 'date'):
                    return field.value.date()
                return field.value
        except:
            pass
        return None