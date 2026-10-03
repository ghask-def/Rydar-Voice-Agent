import os
import json
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# QuickBooks Online settings
QUICKBOOKS_CLIENT_ID = os.getenv('QUICKBOOKS_CLIENT_ID')
QUICKBOOKS_CLIENT_SECRET = os.getenv('QUICKBOOKS_CLIENT_SECRET')
QUICKBOOKS_SANDBOX = os.getenv('QUICKBOOKS_SANDBOX', 'true').lower() == 'true'

# API URLs
if QUICKBOOKS_SANDBOX:
    BASE_URL = "https://sandbox-quickbooks.api.intuit.com"
else:
    BASE_URL = "https://quickbooks.api.intuit.com"

TOKEN_FILE = 'quickbooks_token.json'

def get_basic_auth_header():
    """Generate basic auth header for token requests"""
    credentials = f"{QUICKBOOKS_CLIENT_ID}:{QUICKBOOKS_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return encoded_credentials

def load_stored_tokens():
    """Load stored tokens from file"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def save_tokens(tokens):
    """Save tokens to file"""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)

def refresh_access_token(refresh_token):
    """Refresh the access token using refresh token"""
    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {get_basic_auth_header()}'
    }
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Token refresh failed: {response.status_code} - {response.text}")

def get_quickbooks_service():
    """Get valid QuickBooks credentials - similar to get_gmail_service()"""
    print("\n[get_quickbooks_service]\n")
    
    # Load existing tokens
    tokens = load_stored_tokens()
    
    if not tokens:
        print("No QuickBooks tokens found. Run quickbooksAuth.py first")
        return None
    
    # Check if tokens need refresh
    if 'refresh_token' in tokens:
        try:
            print("Checking/refreshing QuickBooks tokens...")
            refreshed = refresh_access_token(tokens['refresh_token'])
            refreshed['realm_id'] = tokens['realm_id']
            save_tokens(refreshed)
            print("QuickBooks tokens refreshed successfully")
            return refreshed
        except Exception as e:
            print(f"Failed to refresh QuickBooks tokens: {e}")
            print("You need to re-authenticate with quickbooksAuth.py")
            return None
    
    return tokens

def make_quickbooks_api_call(endpoint, method='GET', data=None):
    """Make authenticated API call to QuickBooks - similar to Gmail service pattern"""
    tokens = get_quickbooks_service()
    
    if not tokens:
        raise Exception("No valid QuickBooks credentials available")
    
    access_token = tokens['access_token']
    realm_id = tokens['realm_id']
    
    url = f"{BASE_URL}/v3/company/{realm_id}/{endpoint}"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    if method.upper() == 'POST' and data:
        headers['Content-Type'] = 'application/json'
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"QuickBooks API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"QuickBooks API call failed: {e}")
        raise

# Common QuickBooks operations (like Gmail operations)
def get_company_info():
    """Get company information"""
    tokens = get_quickbooks_service()
    if not tokens:
        return None
    
    realm_id = tokens['realm_id']
    return make_quickbooks_api_call(f"companyinfo/{realm_id}")

def get_customers():
    """Get all customers"""
    return make_quickbooks_api_call("query?query=SELECT * FROM Customer")

def get_items():
    """Get all items/products"""
    return make_quickbooks_api_call("query?query=SELECT * FROM Item")

def get_invoices():
    """Get all invoices"""
    return make_quickbooks_api_call("query?query=SELECT * FROM Invoice")

def create_customer(customer_data):
    """Create a new customer"""
    return make_quickbooks_api_call("customer", method="POST", data=customer_data)

def create_invoice(invoice_data):
    """Create a new invoice in QuickBooks"""
    return make_quickbooks_api_call("invoice", method="POST", data=invoice_data)

def create_simple_invoice(customer_ref, line_items, due_date=None):
    """
    Create a simple invoice with basic structure
    
    Args:
        customer_ref: Customer ID (string) or {"value": "customer_id"}
        line_items: List of line items [{"item_ref": "item_id", "quantity": 1, "unit_price": 100.00}]
        due_date: Due date string (YYYY-MM-DD) or None for no due date
    
    Returns:
        QuickBooks API response
    """
    # Format customer reference
    if isinstance(customer_ref, str):
        customer_ref = {"value": customer_ref}
    
    # Format line items for QuickBooks API
    formatted_lines = []
    for item in line_items:
        quantity = item.get("quantity", 1)
        unit_price = item.get("unit_price", 0)
        amount = quantity * unit_price
        
        line = {
            "Amount": amount,
            "DetailType": "SalesItemLineDetail",
            "SalesItemLineDetail": {
                "ItemRef": {
                    "value": item["item_ref"]
                }
            }
        }
        
        # Only add Qty and UnitPrice if they're provided
        if quantity > 0:
            line["SalesItemLineDetail"]["Qty"] = quantity
        if unit_price > 0:
            line["SalesItemLineDetail"]["UnitPrice"] = unit_price
            
        if "description" in item:
            line["Description"] = item["description"]
            
        formatted_lines.append(line)
    
    # Build invoice data structure (correct format)
    invoice_data = {
        "CustomerRef": customer_ref,
        "Line": formatted_lines
    }
    
    # Add due date if provided
    if due_date:
        invoice_data["DueDate"] = due_date
    
    return create_invoice(invoice_data)

# Example usage function
def test_quickbooks_connection():
    """Test QuickBooks connection - similar to Gmail test"""
    try:
        print("Testing QuickBooks connection...")
        
        # Test company info
        company_info = get_company_info()
        if company_info:
            company_name = company_info.get('QueryResponse', {}).get('CompanyInfo', [{}])[0].get('CompanyName', 'Unknown')
            print(f"Connected to QuickBooks company: {company_name}")
            return True
        else:
            print("Failed to get company info")
            return False
            
    except Exception as e:
        print(f"QuickBooks connection test failed: {e}")
        return False 