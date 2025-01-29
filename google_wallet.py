import json
import time
import base64
import jwt
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Replace with your service account JSON key file path
SERVICE_ACCOUNT_FILE = "path/to/your-service-account-key.json"
SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]

# Initialize credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Build the Google Wallet API client
wallet_service = build("walletobjects", "v1", credentials=credentials)

# Replace with your issuer ID from Google Wallet Manager
ISSUER_ID = "YOUR_ISSUER_ID"
USER_ID = "USER_ID"  # Replace with actual user ID
LOYALTY_CLASS_ID = f"{ISSUER_ID}.LOYALTY_CLASS"
LOYALTY_OBJECT_ID = f"{ISSUER_ID}.{USER_ID}"  # Must match loyalty object ID

# Loyalty class definition
LOYALTY_CLASS = {
    "id": LOYALTY_CLASS_ID,
    "issuerName": "Your Business Name",
    "programName": "Your Loyalty Program",
    "programLogo": {
        "sourceUri": {"uri": "https://example.com/logo.png"}
    },
    "reviewStatus": "UNDER_REVIEW",
}

def create_loyalty_class():
    """Create a Google Wallet loyalty class"""
    try:
        response = wallet_service.loyaltyclass().insert(body=LOYALTY_CLASS).execute()
        print("Loyalty class created:", response["id"])
    except Exception as e:
        print("Error creating loyalty class:", e)


# Loyalty object definition
LOYALTY_OBJECT = {
    "id": LOYALTY_OBJECT_ID,
    "classId": LOYALTY_CLASS_ID,
    "state": "ACTIVE",
    "barcode": {"type": "QR_CODE", "value": "1234567890"},
    "accountName": "John Doe",
    "loyaltyPoints": {"label": "Points", "balance": {"int": 100}},
}

def create_loyalty_object():
    """Create a Google Wallet loyalty object"""
    try:
        response = wallet_service.loyaltyobject().insert(body=LOYALTY_OBJECT).execute()
        print("Loyalty object created:", response["id"])
    except Exception as e:
        print("Error creating loyalty object:", e)


def generate_jwt():
    """Generate a JWT for the 'Save to Google Wallet' link"""
    payload = {
        "iss": credentials.service_account_email,
        "aud": "google",
        "origins": ["https://your-website.com"],
        "typ": "savetowallet",
        "payload": {"loyaltyObjects": [{"id": LOYALTY_OBJECT_ID}]},
        "iat": int(time.time()),
    }

    # Sign the JWT
    signed_jwt = jwt.encode(
        payload,
        credentials.sign_bytes,  # Correct signing method
        algorithm="RS256"
    )

    return f"https://pay.google.com/gp/v/save/{signed_jwt}"


if __name__ == "__main__":
    create_loyalty_class()
    create_loyalty_object()
    save_link = generate_jwt()
    print("Save to Wallet Link:", save_link)
