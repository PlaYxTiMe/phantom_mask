# Language native package
import logging
from typing import List, Dict
from datetime import datetime, timezone

# Third party package
from sqlalchemy import func
from fastapi import Request, HTTPException, Depends, status

# Import from other folders
from core.service import BaseService
from core.database import db_session
from app.v1.users.modules import Users
from app.v1.transactions.modules import Transactions
from app.v1.products.modules import Products
from app.v1.customers.modules import Customers
from app.v1.common.modules import StoresProducts
from app.dependencies.user import get_current_user


error_logger = logging.getLogger("errorLogger")


class TransactionService(BaseService):
    """
    Service class to handle transaction-related operations.

    Provides methods to query, process, and manage transaction data 
    within the application context.
    """
    def __init__(self, request: Request, db: db_session, user: Users = Depends(get_current_user)) -> None:
        self.request = request
        self.db = db
        self.current_user = user
    
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
                func.lower(Transactions.transactions_type) == transactions_type.lower(),
                func.lower(Products.product_type) == product_type.lower(),
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
                func.lower(Transactions.transactions_type) == transactions_type.lower(),
                func.lower(Products.product_type) == product_type.lower(),
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

    def calculate_product_summary_by_date_range(
        self,
        transactions_type: str,
        product_type: str,
        start_time: datetime,
        end_time: datetime
    ):
        """
        Calculate a summary of product transactions within a specific date range.
        
        Args:
            transactions_type (str): The type of transaction (e.g., 'inbound', 'outbound').
            product_type (str): The type of product to filter by.
            start_time (datetime): Start of the date range.
            end_time (datetime): End of the date range.

        Returns:
            dict: A dictionary containing total summary statistics and detailed transaction records.
        """

        query = (
            self.db.query(Transactions)
            .join(Products, Transactions.product_id == Products.id)
            .filter(
                func.lower(Transactions.transactions_type) == transactions_type.lower(),
                func.lower(Products.product_type) == product_type.lower(),
                Transactions.transactions_date >= start_time,
                Transactions.transactions_date <= end_time
            )
            .order_by(Transactions.transactions_date.desc())
        )
        
        items = query.all()

        results = {
            "summary": {
                "total_amount": 0,
                "total_unit": 0
            },
            "transaction_records": []
        }
        total_amount = 0
        total_unit = 0
        for item in items:
            product = item.product
            store = item.store
            total_amount += item.amount
            total_unit += item.unit
            results["transaction_records"].append({
                "transaction_date": item.transactions_date,
                "product_type": product.product_type,
                "product_brand": product.brand,
                "product_color": product.color,
                "product_pack_size": product.pack_size,
                "unit": item.unit,
                "amount": item.amount,
                "store_name": store.name,
                "store_type": store.store_type
            })
        results["summary"]["total_amount"] = total_amount
        results["summary"]["total_unit"] = total_unit

        return results

    def purchase(
        self,
        customer: Customers,
        product_detail: StoresProducts,
        unit: int,
        description: str = None
    ) -> Dict:
        """
        Processes a purchase transaction between a customer and a store.

        Args:
            customer (Customers): The customer making the purchase.
            product_detail (StoresProducts): The product and store relationship with pricing.
            unit (int): Number of product units being purchased.
            description (str, optional): Optional description of the transaction.

        Returns:
            Dict: A summary containing customer name, phone number, and updated cash balance.
        """

        if customer.cashbalance < product_detail.price * unit:
            self.raise_exception(
                status_code=400,
                detail="Customer cash balance is not enough"
            )
        
        try:
            total_price = round(product_detail.price * unit, 2)

            # Create a new transaction
            transaction = Transactions(
                transactions_type="purchase",
                unit=unit,
                amount=total_price,
                transactions_date=datetime.now(timezone.utc),
                description=description,
                customer=customer,
                store=product_detail.store,
                product=product_detail.product,
                user=self.current_user
            )

            # Update customer's cash balance
            customer.cashbalance -= total_price

            # Update store's cash balance
            product_detail.store.cashbalance += total_price

            # Add transaction to the session
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
        except Exception as e:
            self.db.rollback()
            error_logger.error(f"Error during purchase transaction: {e}", exc_info=True)
            self.raise_exception(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing the purchase transaction, check error log."
            )
        
        results = {
            "customer_name": customer.name,
            "customer_cashbalance": customer.cashbalance
        }

        return results

    def recharge(
        self,
        customer: Customers,
        cashbalance: float,
        description: str = None
    ):
        """
        Recharge the customer's cash balance.

        This method increases the customer's `cashbalance` by the specified `balance`,
        and creates a new transaction record with the type 'recharge'. It also logs
        the transaction user and optional description.

        Args:
            customer (Customers): The customer object whose balance is to be recharged.
            balance (float): The amount to be added to the customer's balance.
            description (str, optional): Optional description of the transaction.

        Returns:
            dict: A dictionary containing the customer's name and updated cash balance.
        """
        try:
            customer.cashbalance += cashbalance
            transaction = Transactions(
                transactions_type="recharge",
                amount=cashbalance,
                transactions_date=datetime.now(timezone.utc),
                description=description,
                customer=customer,
                user=self.current_user
            )
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
        except Exception as e:
            self.db.rollback()
            error_logger.error(f"Error during recharge transaction: {e}", exc_info=True)
            self.raise_exception(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing the recharge transaction, check error log."
            )
        
        results = {
            "customer_name": customer.name,
            "customer_cashbalance": customer.cashbalance
        }

        return results
