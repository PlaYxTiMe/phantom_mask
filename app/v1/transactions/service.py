# Language native package
import logging
from typing import List, Dict
from datetime import datetime

# Third party package
from sqlalchemy import func
from fastapi import Request, HTTPException

# Import from other folders
from core.service import BaseService
from core.database import db_session
from app.v1.transactions.modules import Transactions
from app.v1.products.modules import Products
from app.v1.customers.modules import Customers


error_logger = logging.getLogger("errorLogger")


class TransactionService(BaseService):
    """
    Service class to handle transaction-related operations.

    Provides methods to query, process, and manage transaction data 
    within the application context.
    """
    def __init__(self, request: Request, db: db_session) -> None:
        self.request = request
        self.db = db
    
    def raise_exception(self, status_code:int, detail:str) -> None:
        raise HTTPException(status_code=status_code, detail=detail)

    def top_by_transactions(
            self,
            transactions_type: str,
            product_type: str,
            start_time: datetime,
            end_time: datetime,
            rank_scope: int
        ) -> List[Dict]:
        """
        Get top customers by total transaction amount for a given product type and date range.

        This function:
        1. Aggregates transaction amounts to find top-N customers.
        2. Retrieves all related transaction records for those customers.
        3. Returns ranked customers with detailed transaction history.

        Args:
            transactions_type (str): Type of transaction (e.g., "purchase").
            product_type (str): Type of product (e.g., "mask").
            start_time (datetime): Start date for filtering transactions.
            end_time (datetime): End date for filtering transactions.
            rank_scope (int): Number of top customers to retrieve.

        Returns:
            List[Dict]: A list of dictionaries containing customer details and their transaction records.
        """
        # Step 1: Get the top customers by total transaction amount
        subquery = (
            self.db.query(
                Transactions.customer_id,
                func.sum(Transactions.amount).label("total_amount")
            )
            .join(Products, Transactions.product_id == Products.id)
            .filter(
                Transactions.transactions_type == transactions_type,
                Products.product_type == product_type,
                Transactions.transactions_date >= start_time,
                Transactions.transactions_date <= end_time
            )
            .group_by(Transactions.customer_id)
            .order_by(func.sum(Transactions.amount).desc())
            .limit(rank_scope)
            .subquery()
        )

        # Step 2: fetch all transaction details for those customers
        query = (
            self.db.query(Transactions)
            .join(Products, Transactions.product_id == Products.id)
            .join(Customers, Transactions.customer_id == Customers.id)
            .filter(
                Transactions.transactions_type == transactions_type,
                Products.product_type == product_type,
                Transactions.transactions_date >= start_time,
                Transactions.transactions_date <= end_time,
                Transactions.customer_id.in_(self.db.query(subquery.c.customer_id))
            )
        )
    
        items = query.all()

        # Step 3: Group and assemble response
        results = []
        customer_position = {}
        subquery_results = self.db.query(subquery.c.customer_id, subquery.c.total_amount).all()
        total_amount_map = {sr.customer_id: sr.total_amount for sr in subquery_results}

        for item in items:
            customer = item.customer
            product = item.product
            key = (customer.name, customer.phone_number)

            if key not in customer_position:
                customer_position[key] = len(results)
                results.append({
                    "customer_name": customer.name,
                    "customer_phone_number": customer.phone_number,
                    "customer_cashbalance": customer.cashbalance,
                    "customer_registered_time": customer.registered_time,
                    "total_amount": round(total_amount_map.get(customer.id, 0), 2),
                    "transaction_records": []
                })

            results[customer_position[key]]["transaction_records"].append({
                "transaction_date": item.transactions_date,
                "product_type": product.product_type,
                "product_brand": product.brand,
                "product_color": product.color,
                "product_pack_size": product.pack_size,
                "unit": item.unit,
                "amount": item.amount
            })
        
        # Step 4: Sort results by total amount
        results.sort(key=lambda x: x["total_amount"], reverse=True)

        return results
