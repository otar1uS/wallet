import json
import time
import jwt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from cryptography.hazmat.primitives import serialization
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SCOPES = os.getenv("SCOPES").split(",")  # In case you have multiple scopes
ISSUER_ID = os.getenv("ISSUER_ID")
USER_ID = os.getenv("USER_ID")
PROGRAM_LOGO_URI = os.getenv("PROGRAM_LOGO_URI")
HERO_IMAGE_URI = os.getenv("HERO_IMAGE_URI")
ISSUER_NAME = os.getenv("ISSUER_NAME")
PROGRAM_NAME = os.getenv("PROGRAM_NAME")
INITIAL_POINTS = os.getenv("INITIAL_POINTS")
POINTS_PER_PAYMENT = int(os.getenv("POINTS_PER_PAYMENT"))
REWARD_THRESHOLD = int(os.getenv("REWARD_THRESHOLD"))
BARCODE_VALUE = os.getenv("BARCODE_VALUE")
BARCODE_ALT_TEXT = os.getenv("BARCODE_ALT_TEXT")
FREE_COFFEE_MESSAGE = os.getenv("FREE_COFFEE_MESSAGE")
SAVE_TO_WALLET_ORIGIN = os.getenv("SAVE_TO_WALLET_ORIGIN")
# Replace with your service account JSON key file path
SERVICE_ACCOUNT_FILE = "/mnt/c/Users/opkho/Downloads/medusa.json"
SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]

# Initialize credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Build the Google Wallet API client
wallet_service = build("walletobjects", "v1", credentials=credentials)


LOYALTY_CLASS_ID = f"{ISSUER_ID}.MedusaLoyalty_v2"  # Unique class ID
LOYALTY_OBJECT_ID = f"{ISSUER_ID}.{USER_ID}"  # Valid object ID

# Loyalty class definition
LOYALTY_CLASS = {
    "id": LOYALTY_CLASS_ID,
    "programLogo": {
        "sourceUri": {
            "uri": "https://images.unsplash.com/photo-1512568400610-62da28bc8a13?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=660&h=660"
        },
        "contentDescription": {
            "defaultValue": {
                "language": "en-US",
                "value": "LOGO_IMAGE_DESCRIPTION"
            }
        }
    },
    "localizedIssuerName": {
        "defaultValue": {
            "language": "en-US",
            "value": "MEDUSA"
        }
    },
    "localizedProgramName": {
        "defaultValue": {
            "language": "en-US",
            "value": "STALIN WAS A MAN HIMSELF"
        }
    },
    "hexBackgroundColor": "#b8cdb7",
    "heroImage": {
        "sourceUri": {
            "uri": "https://images.unsplash.com/photo-1447933601403-0c6688de566e?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1032&h=336"
        },
        "contentDescription": {
            "defaultValue": {
                "language": "en-US",
                "value": "HERO_IMAGE_DESCRIPTION"
            }
        }
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

# Loyalty object definition (initially set to 1400 points)
LOYALTY_OBJECT = {
    "id": LOYALTY_OBJECT_ID,
    "classId": LOYALTY_CLASS_ID,
    "state": "ACTIVE",
    "loyaltyPoints": {
        "balance": {
            "int": "1400"  # starting with 1400 points
        },
        "localizedLabel": {
            "defaultValue": {
                "language": "en-US",
                "value": "Reward Points"
            }
        }
    },
    "barcode": {
        "type": "QR_CODE",
        "value": "BARCODE_VALUE",
        "alternateText": "ravaxar zma"
    }
}

def create_loyalty_object():
    """Create a Google Wallet loyalty object"""
    try:
        response = wallet_service.loyaltyobject().insert(body=LOYALTY_OBJECT).execute()
        print("Loyalty object created:", response["id"])
    except Exception as e:
        print("Error creating loyalty object:", e)

def update_loyalty_points(points_to_add=200):
    """
    Retrieve the current loyalty object, add the specified points, and update the object.
    If the balance reaches 2000 or more, reset to 0 and trigger a notification.
    """
    try:
        # Retrieve the current loyalty object
        loyalty_object = wallet_service.loyaltyobject().get(id=LOYALTY_OBJECT_ID).execute()
        current_balance = int(
            loyalty_object.get("loyaltyPoints", {}).get("balance", {}).get("int", "0")
        )
        new_balance = current_balance + points_to_add
        notification_message = None

        # Check if new balance meets or exceeds threshold
        if new_balance >= 2000:
            new_balance = 0  # reset points
            notification_message = "Congratulations! You've earned a free coffee!"
            # Here you can integrate your notification service (e.g., Firebase Cloud Messaging)
            print("Notification:", notification_message)

        # Prepare the patch body to update the points balance
        patch_body = {
            "loyaltyPoints": {
                "balance": {"int": str(new_balance)}
            }
        }

        # Patch (update) the loyalty object with the new balance
        updated_object = wallet_service.loyaltyobject().patch(
            id=LOYALTY_OBJECT_ID, body=patch_body
        ).execute()
        print("Updated loyalty object:", updated_object)
        return notification_message

    except Exception as e:
        print("Error updating loyalty points:", e)
        return None

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

    # Get the private key in PEM format
    private_key = credentials.signer._key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Sign the JWT
    signed_jwt = jwt.encode(
        payload,
        private_key,
        algorithm="RS256"
    )

    return f"https://pay.google.com/gp/v/save/{signed_jwt}"

if __name__ == "__main__":
    # Create the class and object if not already created
    create_loyalty_class()
    create_loyalty_object()

    # Simulate a purchase that increases points by 200
    notification = update_loyalty_points(points_to_add=200)
    if notification:
        # In a real application, this is where you might trigger an actual notification to the user.
        print("User Notification:", notification)

    # Generate the 'Save to Google Wallet' link
    save_link = generate_jwt()
    print("Save to Wallet Link:", save_link)
