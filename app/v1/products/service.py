# Language native package
import logging
from typing import List, Dict
from collections import defaultdict

# Third party package
import operator
from fastapi import Request, HTTPException, status, Depends

# Import from other folders
from core.service import BaseService
from core.database import db_session
from app.v1.users.modules import Users
from app.v1.products.modules import Products
from app.v1.stores.modules import Stores
from app.v1.common.modules import StoresProducts
from app.dependencies.user import get_current_user


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

    def __init__(self, request: Request, db: db_session, user: Users = Depends(get_current_user)) -> None:
        self.request = request
        self.db = db
        self.current_user = user
    
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

    def get_products(
            self,
            page: int,
            per_page: int,
            product_type: str,
            search_fields: str,
            fields_value: str,
            only_active: bool
        ) -> Dict:
        """
        Retrieve a paginated list of products filtered by type and optional search criteria,
        along with store details and pricing information.

        Args:
            page (int): The current page number (1-based).
            per_page (int): Number of products to return per page.
            product_type (str): Filter products by this product type.
            search_fields (str): Product attribute to search on (e.g., brand, color).
            fields_value (str): Value to search for in the specified product attribute.
            only_active (bool): Whether to filter only active products and stores.

        Returns:
            dict: A dictionary containing:
                - "products": A list of products with their details and associated stores sorted by price.
                - "total_pages": Total number of pages available for the given per_page limit.
        """
        query = (
            self.db.query(Products).join(StoresProducts).join(Stores).filter(
                Products.product_type == product_type
            )
        )

        if search_fields and fields_value:
            if hasattr(Products, search_fields):
                query = query.filter(getattr(Products, search_fields).ilike(f"%{fields_value}%"))
            else:
                self.raise_exception(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid search field: {search_fields}"
                )
        
        if only_active:
            query = query.filter(
                Products.is_active == only_active,
                Stores.is_active == only_active
            )

        total_items = query.distinct(Products.id).count()
        total_pages = (total_items + per_page - 1) // per_page
        page_items = (
            query.distinct(Products.id)
            .order_by(Products.brand, Products.color, Products.pack_size)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        results = []
        for item in page_items:
            products_detail = {
                "product_type": item.product_type,
                "brand": item.brand,
                "color": item.color,
                "pack_size": item.pack_size,
                "stores": []
            }
            item.stores.sort(key=lambda x: x.price)
            for store in item.stores:
                products_detail["stores"].append({
                    "store_name": store.store.name,
                    "store_type": store.store.store_type,
                    "price": store.price,
                    "is_active": store.store.is_active
                })
            results.append(products_detail)
        
        return {"products": results, "total_pages": total_pages}

    def get_product_price(self,
        store_name:str,
        store_type:str,
        product_type:str,
        brand:str,
        color:str,
        pack_size:int,
        only_active:bool=True
    ) -> StoresProducts:
        """
        Retrieve the price and details of a specific product in a specific store.

        Args:
            store_name (str): The name of the store.
            store_type (str): The type/category of the store.
            product_type (str): The type/category of the product.
            brand (str): The brand of the product.
            color (str): The color of the product.
            pack_size (int): The pack size of the product.
            only_active (bool): Whether to filter only active products and stores (default is True).

        Returns:
            StoresProducts: The matching store-product relationship, including price and inventory info.
        """
        query = self.db.query(StoresProducts).join(Products).join(Stores).filter(
            Stores.name == store_name,
            Stores.store_type == store_type,
            Products.product_type == product_type,
            Products.brand == brand,
            Products.color == color,
            Products.pack_size == pack_size
        )
        if only_active:
            query = query.filter(
                Stores.is_active == only_active,
                Products.is_active == only_active
            )
        item = query.first()
        if not item:
            self.raise_exception(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found in the specified store"
            )
        
        return item
