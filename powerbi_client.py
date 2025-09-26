import msal
import requests


class PowerBIClient:
    def __init__(self, client_id, client_secret, tenant_id):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = ["https://analysis.windows.net/powerbi/api/.default"]

    def get_access_token(self):
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

        result = app.acquire_token_for_client(scopes=self.scope)

        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Failed to get token: {result}")

    def get_embed_token(self, workspace_id, report_id):
        access_token = self.get_access_token()

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Get report details
        report_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
        report_response = requests.get(report_url, headers=headers)

        if report_response.status_code != 200:
            raise Exception(f"Failed to get report: {report_response.text}")

        report = report_response.json()

        # Generate embed token
        embed_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/GenerateToken"
        embed_body = {"accessLevel": "View", "allowSaveAs": False}

        embed_response = requests.post(embed_url, headers=headers, json=embed_body)

        if embed_response.status_code != 200:
            raise Exception(f"Failed to generate embed token: {embed_response.text}")

        embed_token = embed_response.json()

        return {
            'token': embed_token['token'],
            'embed_url': report['embedUrl'],
            'report_id': report_id,
            'expires': embed_token['expiration']
        }