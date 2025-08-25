import os 
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

load_dotenv()

#get google refresh token for Gmail API access - run this once  
def get_refresh_token():
    SCOPES=['https://www.googleapis.com/auth/gmail.send'] #OAuth 2.0 scopes

    flow=Flow.from_client_config(
        {
            "web":{
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:5000/auth/google/callback"]
            }

        },
        scopes=SCOPES
    )
    flow.redirect_uri='http://localhost:5000/auth/google/callback'
    #get auth url, accesstype->ensures you get a refresh token.
    auth_url,_=flow.authorization_url(access_type='offline',prompt='consent')
    print("Open this url in your browser")
    print(auth_url)
    print("\n After authorizing, copy the entire url from your browser address bar:")
    #get auth response url
    authorization_response_url=input("Paste the full redirect url here:").strip()
    #exchange  auth code for tokens
    flow.fetch_token(authorization_response=authorization_response_url)
    credentials=flow.credentials
    print("\n Success! Add this to your .env file:")
    print(f"GOOGLE_REFRESH_TOKEN={credentials.refresh_token}")
    print(f"\n Also save these (you might need them):")
    print(f"ACCESS_TOKEN={credentials.token}")
    print(f"TOKEN_URI={credentials.token_uri}")
    return credentials.refresh_token


if __name__ == "__main__":
    print("Google Gmail API - Refresh Token Generator")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('GOOGLE_CLIENT_ID') or not os.getenv('GOOGLE_CLIENT_SECRET'):
        print("Error: Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in environment variables")
        print("Please check your .env file and try again.")
        exit(1)
    
    try:
        refresh_token = get_refresh_token()
        print("\nSetup complete! You can now send emails via Gmail API.")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your redirect URI is exactly: http://localhost:5000/auth/google/callback")
        print("2. Check that Gmail API is enabled in Google Cloud Console")
        print("3. Verify your client ID and secret are correct")

