import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = '0e792a2b521d96afca834c9dca286dbe'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///invoices.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Azure
    AZURE_ENDPOINT = 'https://nyxion-form-recognizer.cognitiveservices.azure.com/'
    AZURE_KEY = '7g3UCPXzClukLhyIgw54xvyofcNdeuNgaHMU2ktrLMUXevZCLQBFJQQJ99BIACYeBjFXJ3w3AAALACOG4D8F'

    # Power BI
    POWER_BI_CLIENT_ID = '21b28f19-aba7-46f9-86f6-90f7a977aae3'
    POWER_BI_CLIENT_SECRET = '76159fcd-a674-43ef-a4ac-6aaf562d14b5'
    POWER_BI_TENANT_ID = '079d201f-b282-41e6-a5f1-f7c760316153'
    POWER_BI_WORKSPACE_ID = '3fb423af-22e9-4ade-a193-6c1aa3fef1ab'
    POWER_BI_REPORT_ID = '1c9b24f4-4e6c-4fc0-b76a-0745dc111d4c'