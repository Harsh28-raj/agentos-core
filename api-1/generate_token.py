import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://mail.google.com/']

def generate_gmail_token():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    credentials_path = os.path.join(base_dir, 'credentials.json')
    token_path = os.path.join(base_dir, 'token.json')
    
    if not os.path.exists(credentials_path):
        print("❌ Error: credentials.json missing in api-1 folder!")
        return

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    print("\n🎉 Success: token.json file successfully created!")

if __name__ == '__main__':
    generate_gmail_token()
