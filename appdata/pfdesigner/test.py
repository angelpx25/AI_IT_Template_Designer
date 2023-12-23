import requests
import base64
from msal import ConfidentialClientApplication

def get_access_token(client_id, tenant_id, certificate_path, resource_url='https://graph.microsoft.com/.default'):
    # Load the private key from the PFX file
    with open(certificate_path, 'rb') as pfx_file:
        pfx_data = pfx_file.read()

    app = ConfidentialClientApplication(
        client_id,
        authority=f'https://login.microsoftonline.com/{tenant_id}',
        client_credential={'private_key': pfx_data, 'thumbprint': '440FC2B08CC7586C815CACE316B72C79C7FDDE21'},
    )

    token_response = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
    print(client_id)
    print(token_response)
    return token_response['access_token']


def get_site_id(client_id, tenant_id, certificate_path, site_name):
    access_token = get_access_token(client_id, tenant_id, certificate_path)

    # Make request to Microsoft Graph API to get a list of sites
    endpoint_url = 'https://graph.microsoft.com/v1.0/sites'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.get(endpoint_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(data)
        for site in data.get('value', []):
            if site.get('name') == site_name:
                return site.get('id')
        return f"Site with name '{site_name}' not found."
    else:
        return f'Error: {response.status_code} - {response.text}'

# Replace these values with your actual Azure AD App Registration details and site name
client_id = '09b4038a-b7ed-4784-99ef-09fcfe12eaef'
tenant_id = '1629059d-1b1e-4108-bee7-f509b4c6e6ff'
site_name = 'Fuelnow'
list_id = '273f2e45-131d-4b30-8c58-4d57aae31021'
client_certificate = './AKTISFLOWS.pem'
#site_id = get_site_id(client_id, tenant_id, client_certificate, site_name)
#print(f"The siteId for '{site_name}' is: {site_id}")

access_token = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6Ijc3b2lxdlJRYmFwLTNTcDBoNnNuSnJabWRfRnVYYjBpajNrcmRfZENSRTgiLCJhbGciOiJSUzI1NiIsIng1dCI6IlQxU3QtZExUdnlXUmd4Ql82NzZ1OGtyWFMtSSIsImtpZCI6IlQxU3QtZExUdnlXUmd4Ql82NzZ1OGtyWFMtSSJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8xNjI5MDU5ZC0xYjFlLTQxMDgtYmVlNy1mNTA5YjRjNmU2ZmYvIiwiaWF0IjoxNzAyMjY4NDMzLCJuYmYiOjE3MDIyNjg0MzMsImV4cCI6MTcwMjI3MjMzMywiYWlvIjoiRTJWZ1lOZ3JMcjlWUHJqdnFaaHA4SlRqUzBPUEF3QT0iLCJhcHBfZGlzcGxheW5hbWUiOiJBS1RJU0ZMT1dTIiwiYXBwaWQiOiIwOWI0MDM4YS1iN2VkLTQ3ODQtOTllZi0wOWZjZmUxMmVhZWYiLCJhcHBpZGFjciI6IjIiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8xNjI5MDU5ZC0xYjFlLTQxMDgtYmVlNy1mNTA5YjRjNmU2ZmYvIiwiaWR0eXAiOiJhcHAiLCJvaWQiOiI2NzExMGY2Zi1lYTVlLTQ4OTgtYmFiZC1iZDU5ZjAwNzA3MDgiLCJyaCI6IjAuQVN3QW5RVXBGaDRiQ0VHLTVfVUp0TWJtX3dNQUFBQUFBQUFBd0FBQUFBQUFBQUQyQUFBLiIsInJvbGVzIjpbIlVzZXIuUmVhZFdyaXRlLkFsbCIsIkdyb3VwLlJlYWRXcml0ZS5BbGwiXSwic3ViIjoiNjcxMTBmNmYtZWE1ZS00ODk4LWJhYmQtYmQ1OWYwMDcwNzA4IiwidGVuYW50X3JlZ2lvbl9zY29wZSI6Ik5BIiwidGlkIjoiMTYyOTA1OWQtMWIxZS00MTA4LWJlZTctZjUwOWI0YzZlNmZmIiwidXRpIjoiQ01jbWdFZDhpMEd3b2d4V0hWcElBQSIsInZlciI6IjEuMCIsIndpZHMiOlsiMDk5N2ExZDAtMGQxZC00YWNiLWI0MDgtZDVjYTczMTIxZTkwIl0sInhtc190Y2R0IjoxNTI5NTM5Mzg3fQ.SeyndSDCmTUNz_k2X5cXB8jO7OVGROsPZjGvXYr56h5IH-fUPyeQRmT0XkAvKHlD-Fdd0ee0mAG2azk7wpcGgdJTsV_oKQCFzAkPlw9qo0B2CdTIHn0jbwU7-LBFpsmXis1BMzMH-4vAJsuRp1-Z2xo1fnsV9fpnteoUWX1TRm80bT4D-NzvZtPfBsFNxgnTrobB3ORHyg3KXtZrCGuBYAlgh-0QRIJx9g_eoQTT0hfvjTc8M6ZJMdR0HLGxPkkbuEd-Y1E6Jw1yOjzPfIcR0HjPEsopRC9b5AXurPyqq2bbFe6lG-WfaDYnfsv4UxpbcgGB4oNl0hzy5o3flv6NTw'


endpoint_url = 'https://graph.microsoft.com/v1.0/sites/projectfuelnow.sharepoint.com:/sites/Fuelnow'
headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
response = requests.get(endpoint_url, headers=headers)
print(response.json())