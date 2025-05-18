# Language native package
import logging
from typing import List, Dict
from collections import defaultdict

# Third party package
import operator
from fastapi import Request, HTTPException, status

# Import from other folders
from core.service import BaseService
from core.database import db_session
from app.v1.products.modules import Products
from app.v1.stores.modules import Stores
from app.v1.common.modules import StoresProducts


error_logger = logging.getLogger("errorLogger")


class ProductService(BaseService):
    """
    Service layer for handling product-related business logic and database interactions.

    Attributes:
        ops (dict): A class-level dictionary that maps string-based comparison operators 
                    (e.g., "gt", "lt", "ge", "le", "eq") to their corresponding Python 
                    operator functions from the `operator` module. This is defined at 
                    the class level to avoid recreating the dictionary on each instance, 
                    improving memory efficiency.

    Args:
        request (Request): The incoming FastAPI request object.
        db (Session): The SQLAlchemy database session used for executing queries.
    """
    # Mapping of comparison operators
    # Place it at the class level to avoid creating a new dictionary each time an instance is created, which helps save memory.
    ops = {
        "gt": operator.gt,
        "lt": operator.lt,
        "ge": operator.ge,
        "le": operator.le,
        "eq": operator.eq
    }

    def __init__(self, request: Request, db: db_session) -> None:
        self.request = request
        self.db = db
    
    def raise_exception(self, status_code:int, detail:str) -> None:
        raise HTTPException(status_code=status_code, detail=detail)
    
    def get_store_product_by_price_condition(
            self,
            product_type: str,
            price: float,
            condition: str,
            store_type: str,
            only_active: bool
        ) -> List[Dict]:
        """
        Retrieve all stores that sell a specific product type within a given price condition.
        Filters by product type, price comparison, store type, and active status.
        Results are grouped by store with product details.

        Args:
            product_type (str): Type of product to filter, e.g., "mask".
            price (float): The reference price to compare against.
            condition (str): Comparison operator: "gt" (greater than), "ge" (greater or equal),
                            "lt" (less than), "le" (less or equal), "eq" (equal).
            store_type (str): Type of store to filter, e.g., "pharmacy".
            only_active (bool): If True, only include active stores and products.

        Returns:
            List[Dict]: A list of stores with matching products, grouped by store.
        """
        query = self.db.query(StoresProducts).join(Products).filter(
            self.ops[condition.lower()](StoresProducts.price, price)
        ).filter(
            Products.product_type == product_type
        )

        if only_active:
            query = query.filter(Products.is_active == only_active)
        if store_type:
            query = query.join(Stores).filter(
                Stores.store_type == store_type
            )
        
        items = query.all()

        store_map = defaultdict(lambda: {
            "store_name": "",
            "store_type": "",
            "is_active": True,
            "products": []
        })

        for item in items:
            store = item.store
            product = item.product

            store_data = store_map[store.name]
            store_data["store_name"] = store.name
            store_data["store_type"] = store.store_type
            store_data["is_active"] = store.is_active
            store_data["products"].append({
                "product_type": product.product_type,
                "brand": product.brand,
                "color": product.color,
                "pack_size": product.pack_size,
                "price": item.price,
                "is_active": product.is_active
            })
        results = list(store_map.values())

        return results
