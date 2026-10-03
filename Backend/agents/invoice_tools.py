from livekit.agents import function_tool, RunContext
from agents.invoice_manager import invoice_manager
import re

# Simple session ID generator - in a real app you might use user IDs or room IDs
def get_session_id() -> str:
    """Generate a simple session ID - you can customize this based on your needs"""
    import time
    return f"invoice_{int(time.time())}"

@function_tool()
async def start_new_invoice() -> str:
    """
    Start creating a new invoice. This initializes a new invoice session.
    
    Returns:
        Confirmation message that invoice creation has started
    """
    session_id = get_session_id()
    return invoice_manager.start_invoice_session(session_id)

@function_tool()
async def set_invoice_customer(customer_name: str) -> str:
    """
    Set the customer for the current invoice. The customer must exist in QuickBooks.
    
    Args:
        customer_name: The name of the customer as it appears in QuickBooks
        
    Returns:
        Confirmation if customer is found, or error message if not found
    """
    # Get the most recent session ID (in a real app, you'd track this per user/room)
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session. Please start a new invoice first."
    
    session_id = session_ids[-1]  # Use most recent session
    return invoice_manager.update_customer_info(session_id, customer_name)

@function_tool()
async def add_invoice_item(description: str, quantity: float = None, unit_price: float = None) -> str:
    """
    Add an item/service to the current invoice.
    
    Args:
        description: Description of the item or service
        quantity: Number of items (optional, can be set later)
        unit_price: Price per item in dollars (optional, can be set later)
        
    Returns:
        Confirmation message and what information is still needed
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session. Please start a new invoice first."
    
    session_id = session_ids[-1]
    return invoice_manager.add_line_item(session_id, description, quantity, unit_price)

@function_tool()
async def update_invoice_item_quantity(item_number: int, quantity: float) -> str:
    """
    Update the quantity for a specific line item on the invoice.
    
    Args:
        item_number: The line item number (1, 2, 3, etc.)
        quantity: The quantity/number of items
        
    Returns:
        Confirmation message
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session. Please start a new invoice first."
    
    session_id = session_ids[-1]
    return invoice_manager.update_line_item(session_id, item_number - 1, quantity=quantity)

@function_tool()
async def update_invoice_item_price(item_number: int, unit_price: float) -> str:
    """
    Update the unit price for a specific line item on the invoice.
    
    Args:
        item_number: The line item number (1, 2, 3, etc.)
        unit_price: The price per item in dollars
        
    Returns:
        Confirmation message
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session. Please start a new invoice first."
    
    session_id = session_ids[-1]
    return invoice_manager.update_line_item(session_id, item_number - 1, unit_price=unit_price)

@function_tool()
async def set_invoice_due_date(due_date: str) -> str:
    """
    Set the due date for the current invoice.
    
    Args:
        due_date: Due date in YYYY-MM-DD format (e.g., "2024-12-31")
        
    Returns:
        Confirmation message
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session. Please start a new invoice first."
    
    session_id = session_ids[-1]
    return invoice_manager.set_due_date(session_id, due_date)

@function_tool()
async def get_invoice_summary() -> str:
    """
    Get a summary of the current invoice showing all entered information and what's still missing.
    
    Returns:
        Detailed summary of the invoice status
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session."
    
    session_id = session_ids[-1]
    return invoice_manager.get_invoice_summary(session_id)

@function_tool()
async def create_invoice_in_quickbooks() -> str:
    """
    Create the invoice in QuickBooks once all required information has been provided.
    
    Returns:
        Success message with invoice number, or error message if information is missing
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session."
    
    session_id = session_ids[-1]
    return invoice_manager.create_invoice(session_id)

@function_tool()
async def cancel_current_invoice() -> str:
    """
    Cancel the current invoice session and clear all entered data.
    
    Returns:
        Confirmation message
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session to cancel."
    
    session_id = session_ids[-1]
    return invoice_manager.cancel_invoice_session(session_id)

@function_tool()
async def create_new_customer(customer_name: str, email: str = None, phone: str = None, address: str = None) -> str:
    """
    Create a new customer in QuickBooks and set them as the invoice customer.
    Use this when the customer doesn't exist in QuickBooks yet.
    
    Args:
        customer_name: The name of the new customer
        email: Customer's email address (optional)
        phone: Customer's phone number (optional)  
        address: Customer's billing address (optional)
        
    Returns:
        Success or error message
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session. Please start a new invoice first."
    
    session_id = session_ids[-1]
    return invoice_manager.create_new_customer(session_id, customer_name, email, phone, address)

@function_tool()
async def remove_invoice_item(item_number: int) -> str:
    """
    Remove a specific line item from the current invoice.
    
    Args:
        item_number: The line item number to remove (1, 2, 3, etc.)
        
    Returns:
        Confirmation message
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session."
    
    session_id = session_ids[-1]
    return invoice_manager.remove_line_item(session_id, item_number)

@function_tool()
async def clear_all_invoice_items() -> str:
    """
    Remove all line items from the current invoice. Use this to start over with line items.
    
    Returns:
        Confirmation message
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        return "No active invoice session."
    
    session_id = session_ids[-1]
    return invoice_manager.clear_all_line_items(session_id)

@function_tool()
async def parse_invoice_from_transcript(transcript: str) -> str:
    """
    Extract invoice information from a user transcript and populate the invoice automatically.
    This is useful when users provide multiple pieces of information at once.
    
    Args:
        transcript: The user's spoken transcript containing invoice information
        
    Returns:
        Summary of what information was extracted and what's still needed
    """
    session_ids = list(invoice_manager.session_data.keys())
    if not session_ids:
        # Start a new session if none exists
        session_id = get_session_id()
        invoice_manager.start_invoice_session(session_id)
    else:
        session_id = session_ids[-1]
    
    results = []
    transcript_lower = transcript.lower()
    
    # Try to extract customer name
    customer_patterns = [
        r'(?:customer|client|for)\s+(?:is\s+)?([a-zA-Z\s]+?)(?:\s+(?:needs|wants|ordered|total|cost|price|due|\$))',
        r'invoice\s+(?:for\s+)?([a-zA-Z\s]+?)(?:\s+(?:needs|wants|ordered|total|cost|price|due|\$))',
        r'bill\s+(?:for\s+)?([a-zA-Z\s]+?)(?:\s+(?:needs|wants|ordered|total|cost|price|due|\$))'
    ]
    
    for pattern in customer_patterns:
        match = re.search(pattern, transcript_lower)
        if match:
            customer_name = match.group(1).strip().title()
            if len(customer_name) > 2:  # Sanity check
                result = invoice_manager.update_customer_info(session_id, customer_name)
                results.append(f"Customer: {result}")
                break
    
    # Try to extract line items with prices
    # Look for patterns like "3 hours at $75 per hour" or "plumbing repair for $200"
    item_patterns = [
        r'(\d+(?:\.\d+)?)\s+(?:hours?|hrs?)\s+(?:at|for)\s+\$?(\d+(?:\.\d+)?)\s*(?:per\s+hour|each|hr)?',
        r'(\d+(?:\.\d+)?)\s+([\w\s]+?)\s+(?:at|for)\s+\$?(\d+(?:\.\d+)?)\s*(?:each|per)?',
        r'([\w\s]+?)\s+(?:for|costs?|priced?\s+at)\s+\$?(\d+(?:\.\d+)?)'
    ]
    
    for pattern in item_patterns:
        matches = re.finditer(pattern, transcript_lower)
        for match in matches:
            if len(match.groups()) == 2:  # Pattern with description and price
                description = match.group(1).strip()
                price = float(match.group(2))
                result = invoice_manager.add_line_item(session_id, description, 1.0, price)
                results.append(f"Item: {result}")
            elif len(match.groups()) == 3:  # Pattern with quantity, description, price
                try:
                    quantity = float(match.group(1))
                    description = match.group(2).strip()
                    price = float(match.group(3))
                    result = invoice_manager.add_line_item(session_id, description, quantity, price)
                    results.append(f"Item: {result}")
                except ValueError:
                    continue
    
    # Try to extract due date
    date_patterns = [
        r'due\s+(?:on\s+)?(\d{4}-\d{2}-\d{2})',
        r'due\s+(?:by\s+)?(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, transcript_lower)
        if match:
            due_date_str = match.group(1)
            # For now, only handle YYYY-MM-DD format automatically
            if re.match(r'\d{4}-\d{2}-\d{2}', due_date_str):
                result = invoice_manager.set_due_date(session_id, due_date_str)
                results.append(f"Due date: {result}")
                break
    
    if results:
        summary = invoice_manager.get_invoice_summary(session_id)
        return f"Extracted information:\n" + "\n".join(results) + f"\n\n{summary}"
    else:
        return "I couldn't extract specific invoice information from that transcript. Let me help you enter the details step by step. What's the customer name?"

# Export all invoice-related functions
INVOICE_TOOLS = [
    start_new_invoice,
    set_invoice_customer,
    add_invoice_item,
    set_invoice_due_date,
    get_invoice_summary,
    create_invoice_in_quickbooks,
]

# INVOICE_TOOLS = [
#     start_new_invoice,
#     set_invoice_customer,
#     add_invoice_item,
#     update_invoice_item_quantity,
#     update_invoice_item_price,
#     set_invoice_due_date,
#     get_invoice_summary,
#     create_invoice_in_quickbooks,
#     cancel_current_invoice,
#     parse_invoice_from_transcript,
#     create_new_customer,
#     remove_invoice_item,
#     clear_all_invoice_items
# ] 