

from app.core import db_connection
from app.core.exceptions import NotFoundException
from app.customers.models import Customer


db = db_connection.session

def get_customer_by_id(customer_id: str):
    """
    Retrieves a customer by their ID.
    
    Args:
        customer_id (str): The ID of the customer to retrieve.
        
    Returns:
        
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise NotFoundException(f"Customer with id {customer_id} not found")
    return customer
            