# Language native package
import logging
from typing import Dict
from datetime import datetime, timezone

# Third party package
from fastapi import Request, HTTPException, Depends, status

# Import from other folders
from core.service import BaseService
from core.database import db_session
from app.v1.users.modules import Users
from app.v1.customers.modules import Customers
from app.dependencies.user import get_current_user


error_logger = logging.getLogger("errorLogger")


class CustomerService(BaseService):
    """
    Service class for handling customer-related business logic.
    Inherits from BaseService and provides access to the request,
    database session, and currently authenticated user.
    """
    def __init__(self, request: Request, db: db_session, user: Users = Depends(get_current_user)) -> None:
        self.request = request
        self.db = db
        self.current_user = user

    def raise_exception(self, status_code:int, detail:str) -> None:
        raise HTTPException(status_code=status_code, detail=detail)
    
    def get_customer_module(self, customer_name:str, customer_phone_number:str) -> Customers:
        """
        Retrieve a customer record by name and phone number.

        Args:
            customer_name (str): The full name of the customer.
            customer_phone_number (str): The phone number of the customer.

        Returns:
            Customers: The matched customer record from the database.
        """
        query = self.db.query(Customers).filter(
            Customers.name == customer_name,
            Customers.phone_number == customer_phone_number,
            Customers.revoke == False
        ).first()

        if not query:
            raise HTTPException(status_code=404, detail="Customer not found")
        return query

    def get_customers(
        self,
        page: int,
        per_page: int,
        search_field: str,
        search_value: str,
        only_active: bool = True
    ) -> Dict:
        """
        Retrieve a paginated list of customers with optional search and filtering.

        Args:
            page (int): Current page number.
            per_page (int): Number of records per page.
            search_field (str): Field name to search.
            search_value (str): Keyword to search in the specified field.
            only_active (bool, optional): Whether to only return active (non-revoked) customers. Defaults to True.

        Returns:
            dict: A dictionary with a list of customers and total number of pages.
        """
        query = self.db.query(Customers)

        if only_active:
            query = query.filter(Customers.revoke == False)
        
        if search_field and search_value:
            if hasattr(Customers, search_field):
                query = query.filter(getattr(Customers, search_field).like(f"%{search_value}%"))
            else:
                raise HTTPException(status_code=400, detail="Invalid search field")
        
        items_count = query.count()
        page_items = (
            query
            .order_by(Customers.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        total_pages = (items_count + per_page - 1) // per_page

        results = []
        for item in page_items:
            customer_detail = {
                "name": item.name,
                "phone_number": item.phone_number,
                "cashbalance": item.cashbalance,
                "registered_time": item.registered_time,
                "registered_by": item.registered_user.nickname if item.registered_user else None,
                "revoke": item.revoke,
                "revoked_time": item.revoked_time,
                "revoked_by": item.revoked_user.nickname if item.revoked_user else None
            }
            results.append(customer_detail)
        
        return {"customers": results, "total_pages": total_pages}
    
    def create_customer(
        self,
        name: str,
        phone_number: str
    ) -> Dict:
        """
        Create a new customer record in the database.

        Args:
            customer_name (str): The full name of the customer.
            customer_phone_number (str): The phone number of the customer.
            cashbalance (int, optional): Initial cash balance for the customer. Defaults to 0.

        Returns:
            Customers: The created customer record.
        """
        try:
            new_customer = Customers(
                name=name,
                phone_number=phone_number,
                cashbalance=0,
                registered_time=datetime.now(timezone.utc),
                registered_user=self.current_user
            )
            
            self.db.add(new_customer)
            self.db.commit()
            self.db.refresh(new_customer)
        except Exception as e:
            self.db.rollback()
            error_logger.error(f"Failed to create customer in database: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create customer in database, check error log"
            )

        results = {
            "name": new_customer.name,
            "phone_number": new_customer.phone_number,
            "cashbalance": new_customer.cashbalance,
            "registered_time": new_customer.registered_time,
            "registered_by": self.current_user.nickname,
            "revoke": new_customer.revoke,
            "revoked_time": new_customer.revoked_time,
            "revoked_by": None
        }
        
        return results
