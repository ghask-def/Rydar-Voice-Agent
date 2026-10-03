import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from services.quickbooks_service import get_customers, get_items, create_simple_invoice, create_customer

@dataclass
class InvoiceLineItem:
    """Represents a single line item in an invoice"""
    description: Optional[str] = None
    item_ref: Optional[str] = None  # QuickBooks item ID
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    
    def is_complete(self) -> bool:
        """Check if line item has all required information"""
        return all([
            self.description,
            self.quantity is not None and self.quantity > 0,
            self.unit_price is not None and self.unit_price > 0
        ])
    
    def missing_fields(self) -> List[str]:
        """Return list of missing required fields"""
        missing = []
        if not self.description:
            missing.append("description")
        if self.quantity is None or self.quantity <= 0:
            missing.append("quantity")
        if self.unit_price is None or self.unit_price <= 0:
            missing.append("unit_price")
        return missing

@dataclass
class InvoiceData:
    """Represents complete invoice information"""
    customer_name: Optional[str] = None
    customer_ref: Optional[str] = None  # QuickBooks customer ID
    line_items: List[InvoiceLineItem] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []
    
    def is_complete(self) -> bool:
        """Check if invoice has all required information"""
        return (
            self.customer_ref is not None and
            len(self.line_items) > 0 and
            all(item.is_complete() for item in self.line_items)
        )
    
    def missing_fields(self) -> List[str]:
        """Return list of missing required fields"""
        missing = []
        
        if not self.customer_ref:
            missing.append("customer")
        
        if not self.line_items:
            missing.append("line_items")
        else:
            for i, item in enumerate(self.line_items):
                item_missing = item.missing_fields()
                if item_missing:
                    missing.extend([f"line_item_{i+1}_{field}" for field in item_missing])
        
        return missing
    
    def get_total_amount(self) -> float:
        """Calculate total invoice amount"""
        total = 0.0
        for item in self.line_items:
            if item.quantity and item.unit_price:
                total += item.quantity * item.unit_price
        return total

class InvoiceSessionManager:
    """Manages invoice creation sessions with partial data storage"""
    
    def __init__(self):
        self.session_data: Dict[str, InvoiceData] = {}
        self._customers_cache = None
        self._items_cache = None
    
    def start_invoice_session(self, session_id: str) -> str:
        """Start a new invoice creation session"""
        self.session_data[session_id] = InvoiceData()
        return f"Started new invoice creation session. I'll help you gather all the necessary information step by step."
    
    def get_invoice_data(self, session_id: str) -> Optional[InvoiceData]:
        """Get current invoice data for a session"""
        return self.session_data.get(session_id)
    
    def update_customer_info(self, session_id: str, customer_name: str) -> str:
        """Update customer information and try to find matching QuickBooks customer"""
        if session_id not in self.session_data:
            return "No active invoice session. Please start a new invoice first."
        
        invoice_data = self.session_data[session_id]
        invoice_data.customer_name = customer_name
        
        # Try to find matching customer in QuickBooks
        customer_ref = self._find_customer_by_name(customer_name)
        
        if customer_ref:
            invoice_data.customer_ref = customer_ref
            return f"Found customer '{customer_name}' in QuickBooks. Customer information updated."
        else:
            return f"Customer '{customer_name}' not found in QuickBooks. You may need to create this customer first, or provide the exact name as it appears in QuickBooks."
    
    def add_line_item(self, session_id: str, description: str, quantity: float = None, unit_price: float = None) -> str:
        """Add a line item to the invoice"""
        if session_id not in self.session_data:
            return "No active invoice session. Please start a new invoice first."
        
        invoice_data = self.session_data[session_id]
        line_item = InvoiceLineItem(
            description=description,
            quantity=quantity,
            unit_price=unit_price
        )
        
        invoice_data.line_items.append(line_item)
        
        # Check what's still missing for this line item
        missing = line_item.missing_fields()
        if missing:
            missing_str = ", ".join(missing)
            return f"Added line item '{description}'. Still need: {missing_str}. What would you like to provide next?"
        else:
            total_amount = quantity * unit_price
            return f"Added complete line item: '{description}' - {quantity} x ${unit_price:.2f} = ${total_amount:.2f}"
    
    def update_line_item(self, session_id: str, item_index: int, quantity: float = None, unit_price: float = None) -> str:
        """Update a specific line item"""
        if session_id not in self.session_data:
            return "No active invoice session. Please start a new invoice first."
        
        invoice_data = self.session_data[session_id]
        
        if item_index >= len(invoice_data.line_items):
            return f"Line item {item_index + 1} doesn't exist. You have {len(invoice_data.line_items)} line items."
        
        line_item = invoice_data.line_items[item_index]
        
        if quantity is not None:
            line_item.quantity = quantity
        if unit_price is not None:
            line_item.unit_price = unit_price
        
        # Check if line item is now complete
        if line_item.is_complete():
            total_amount = line_item.quantity * line_item.unit_price
            return f"Updated line item '{line_item.description}': {line_item.quantity} x ${line_item.unit_price:.2f} = ${total_amount:.2f}"
        else:
            missing = line_item.missing_fields()
            missing_str = ", ".join(missing)
            return f"Updated line item '{line_item.description}'. Still need: {missing_str}"
    
    def set_due_date(self, session_id: str, due_date: str) -> str:
        """Set the due date for the invoice"""
        if session_id not in self.session_data:
            return "No active invoice session. Please start a new invoice first."
        
        try:
            # Validate date format (expecting YYYY-MM-DD)
            datetime.strptime(due_date, '%Y-%m-%d')
            self.session_data[session_id].due_date = due_date
            return f"Due date set to {due_date}"
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD format (e.g., 2024-12-31)"
    
    def get_invoice_summary(self, session_id: str) -> str:
        """Get a summary of the current invoice state"""
        if session_id not in self.session_data:
            return "No active invoice session."
        
        invoice_data = self.session_data[session_id]
        
        summary = []
        summary.append("=== INVOICE SUMMARY ===")
        
        # Customer info
        if invoice_data.customer_name:
            status = "" if invoice_data.customer_ref else ""
            summary.append(f"{status} Customer: {invoice_data.customer_name}")
        else:
            summary.append("Customer: Not specified")
        
        # Line items
        summary.append(f"\nLine Items ({len(invoice_data.line_items)}):")
        total_amount = 0.0
        
        for i, item in enumerate(invoice_data.line_items, 1):
            status = "" if item.is_complete() else ""
            line = f"{status} {i}. {item.description or 'No description'}"
            
            if item.quantity and item.unit_price:
                item_total = item.quantity * item.unit_price
                line += f" - {item.quantity} x ${item.unit_price:.2f} = ${item_total:.2f}"
                total_amount += item_total
            else:
                missing = item.missing_fields()
                line += f" (Missing: {', '.join(missing)})"
            
            summary.append(line)
        
        if not invoice_data.line_items:
            summary.append("  No line items added yet")
        
        # Due date
        if invoice_data.due_date:
            summary.append(f"\nDue Date: {invoice_data.due_date}")
        else:
            summary.append(f"\nDue Date: Not set (optional)")
        
        # Total
        if total_amount > 0:
            summary.append(f"\nTotal Amount: ${total_amount:.2f}")
        
        # Completion status
        if invoice_data.is_complete():
            summary.append("\nInvoice is ready to create!")
        else:
            missing = invoice_data.missing_fields()
            summary.append(f"\n Still need: {', '.join(missing)}")
        
        return "\n".join(summary)
    
    def create_invoice(self, session_id: str) -> str:
        """Create the invoice in QuickBooks if all data is complete"""
        if session_id not in self.session_data:
            return "No active invoice session."
        
        invoice_data = self.session_data[session_id]
        
        if not invoice_data.is_complete():
            missing = invoice_data.missing_fields()
            return f"Cannot create invoice. Missing: {', '.join(missing)}. Use 'get invoice summary' to see current status."
        
        try:
            # Prepare line items for QuickBooks API
            qb_line_items = []
            for item in invoice_data.line_items:
                # Find matching QuickBooks item ID if possible
                item_ref = self._find_item_by_name(item.description)
                
                line_item = {
                    "quantity": item.quantity,
                    "unit_price": item.unit_price
                }
                
                # If we found a matching QB item, use it; otherwise use description as free-form text
                if item_ref:
                    line_item["item_ref"] = item_ref
                else:
                    line_item["description"] = item.description
                    # Use a generic service item if no specific match found
                    line_item["item_ref"] = "1"  # "Services" item from QB
                
                qb_line_items.append(line_item)
            
            # Create invoice using QuickBooks service
            result = create_simple_invoice(
                customer_ref=invoice_data.customer_ref,
                line_items=qb_line_items,
                due_date=invoice_data.due_date
            )
            
            if result and 'Invoice' in result:
                invoice_num = result['Invoice'].get('DocNumber', 'Unknown')
                total_amt = result['Invoice'].get('TotalAmt', 0)
                
                # Clear the session data after successful creation
                del self.session_data[session_id]
                
                return f"Invoice #{invoice_num} created successfully! Total: ${total_amt:.2f}"
            else:
                return "Failed to create invoice. Please check your QuickBooks connection and try again."
                
        except Exception as e:
            return f"Error creating invoice: {str(e)}"
    
    def cancel_invoice_session(self, session_id: str) -> str:
        """Cancel and clear the current invoice session"""
        if session_id in self.session_data:
            del self.session_data[session_id]
            return "Invoice session cancelled and data cleared."
        else:
            return "No active invoice session to cancel."
    
    def create_new_customer(self, session_id: str, customer_name: str, email: str = None, phone: str = None, address: str = None) -> str:
        """Create a new customer in QuickBooks and set as invoice customer"""
        if session_id not in self.session_data:
            return "No active invoice session. Please start a new invoice first."
        
        try:
            # Build customer data for QuickBooks (using correct field names)
            customer_data = {
                "DisplayName": customer_name,
                "FullyQualifiedName": customer_name,
                "CompanyName": customer_name,
                "PrintOnCheckName": customer_name,
                "Active": True
            }
            
            # Add optional contact information
            if email:
                customer_data["PrimaryEmailAddr"] = {"Address": email}
            
            if phone:
                customer_data["PrimaryPhone"] = {"FreeFormNumber": phone}
            
            if address:
                # Simple address parsing - in production you'd want more sophisticated parsing
                customer_data["BillAddr"] = {"Line1": address}
            
            # Create customer in QuickBooks
            result = create_customer(customer_data)
            
            if result and 'Customer' in result:
                customer_id = result['Customer']['Id']
                
                # Set as current invoice customer
                invoice_data = self.session_data[session_id]
                invoice_data.customer_name = customer_name
                invoice_data.customer_ref = customer_id
                
                # Clear customer cache to include new customer
                self._customers_cache = None
                
                contact_info = []
                if email:
                    contact_info.append(f"email: {email}")
                if phone:
                    contact_info.append(f"phone: {phone}")
                if address:
                    contact_info.append(f"address: {address}")
                
                contact_str = f" ({', '.join(contact_info)})" if contact_info else ""
                
                return f"Created new customer '{customer_name}'{contact_str} in QuickBooks and set as invoice customer."
            else:
                return f"Failed to create customer '{customer_name}' in QuickBooks. Please check the information and try again."
                
        except Exception as e:
            return f"Error creating customer: {str(e)}"
    
    def remove_line_item(self, session_id: str, item_number: int) -> str:
        """Remove a line item from the invoice"""
        if session_id not in self.session_data:
            return "No active invoice session. Please start a new invoice first."
        
        invoice_data = self.session_data[session_id]
        
        if not invoice_data.line_items:
            return "No line items to remove."
        
        if item_number < 1 or item_number > len(invoice_data.line_items):
            return f"Invalid item number. Please choose between 1 and {len(invoice_data.line_items)}."
        
        # Remove the item (convert to 0-based index)
        removed_item = invoice_data.line_items.pop(item_number - 1)
        
        return f"Removed line item #{item_number}: '{removed_item.description}'. {len(invoice_data.line_items)} items remaining."
    
    def clear_all_line_items(self, session_id: str) -> str:
        """Clear all line items from the invoice"""
        if session_id not in self.session_data:
            return "No active invoice session. Please start a new invoice first."
        
        invoice_data = self.session_data[session_id]
        item_count = len(invoice_data.line_items)
        
        if item_count == 0:
            return "No line items to clear."
        
        invoice_data.line_items.clear()
        return f"Cleared all {item_count} line items from the invoice."
    
    def _find_customer_by_name(self, customer_name: str) -> Optional[str]:
        """Find customer ID by name in QuickBooks"""
        try:
            if not self._customers_cache:
                customers_response = get_customers()
                if customers_response and 'QueryResponse' in customers_response:
                    self._customers_cache = customers_response['QueryResponse'].get('Customer', [])
            
            customer_name_lower = customer_name.lower()
            for customer in self._customers_cache or []:
                # Check both DisplayName and FullyQualifiedName for matches
                display_name = customer.get('DisplayName', '').lower()
                qualified_name = customer.get('FullyQualifiedName', '').lower()
                
                if display_name == customer_name_lower or qualified_name == customer_name_lower:
                    return customer.get('Id')
            
            return None
        except Exception as e:
            print(f"Error finding customer: {e}")
            return None

    def _find_item_by_name(self, item_name: str) -> Optional[str]:
        """Find QuickBooks item ID by name"""
        try:
            if not self._items_cache:
                items_response = get_items()
                if items_response and 'QueryResponse' in items_response:
                    self._items_cache = items_response['QueryResponse'].get('Item', [])
            
            item_name_lower = item_name.lower()
            for item in self._items_cache or []:
                # Check Name and Description for matches
                name = item.get('Name', '').lower()
                description = item.get('Description', '').lower()
                
                if (name == item_name_lower or 
                    item_name_lower in name or 
                    item_name_lower in description):
                    return item.get('Id')
            
            return None
        except Exception as e:
            print(f"Error finding item: {e}")
            return None

# Global instance for session management
invoice_manager = InvoiceSessionManager() 