# Language native package
import logging
from typing import List, Dict
from datetime import datetime

# Third party package
from sqlalchemy import and_, func
from fastapi import Request, HTTPException, status, Depends

# Import from other folders
from core.service import BaseService
from core.database import db_session
from app.v1.users.modules import Users
from app.v1.stores.modules import Stores
from app.v1.products.modules import Products
from app.v1.common.modules import Opentime, StoresProducts
from app.dependencies.user import get_current_user



error_logger = logging.getLogger("errorLogger")


class StoreService(BaseService):
    """
    Service layer for handling store-related operations.

    Attributes:
        search_store_column (List[str]): Fixed column(s) allowed for store search. Defined at the class level to avoid recreating it per instance.
        weekdays (List[str]): List of weekday abbreviations. Defined at the class level to save memory.

    Constructor Args:
        request (Request): The incoming HTTP request context.
        db (db_session): Database session used for executing queries.
    """
    # Fixed constants should be placed at the class level to save memory.
    weekdays = ["Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun"]

    def __init__(self, request:Request, db: db_session, user: Users = Depends(get_current_user)) -> None:
        self.request = request
        self.db = db
        self.current_user = user

    def raise_exception(self, status_code:int, detail:str) -> None:
        raise HTTPException(status_code=status_code, detail=detail)
    
    def _get_store_ids_by_datetime(self, datetime_string:str) -> List[int]:
        """
        Retrieve store IDs that are open at a specific datetime.

        Parses the input ISO 8601 datetime string and identifies stores that are open
        on the corresponding weekday and within the specified time range.

        Args:
            datetime_string (str): A datetime string in the format "%Y-%m-%dT%H:%M:%SZ".

        Returns:
            List[int]: A list of unique store IDs that are open at the specified datetime.
        """
        try:
            datetime_format = datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            error_logger.error(f"Error by datetime format: {e}", exc_info=True)
            self.raise_exception(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error by datetime format, check error log.")
        weekday = self.weekdays[datetime_format.weekday()]
        time = datetime_format.time()

        opentimes = self.db.query(Opentime).filter(
            and_(
                func.lower(Opentime.week_day) == weekday.lower(),
                Opentime.start_time < time,
                Opentime.end_time > time
            )
        ).all()
        return list({so.store_id for ot in opentimes for so in ot.stores_opentime})

    def _get_store_ids_by_weekday(self, weekday_string:str) -> List[int]:
        """
        Retrieve store IDs that are open on a specific weekday.

        Converts the input string to a capitalized weekday format (e.g., "Mon", "Tue"),
        then queries the database for all stores that have operating hours on that day.

        Args:
            weekday_string (str): A string representing the day of the week (e.g., "mon", "tue").

        Returns:
            List[int]: A list of unique store IDs that are open on the specified weekday.
        """
        opentimes = self.db.query(Opentime).filter(
            func.lower(Opentime.week_day) == weekday_string.lower()
        ).all()
        return list({so.store_id for ot in opentimes for so in ot.stores_opentime})

    def get_stores(
            self, 
            page:int, 
            per_page:int, 
            store_type:str, 
            search_fields:str, 
            fields_value:str, 
            only_active:bool
        ) -> Dict:
        """
        Fetches paginated store data with optional filters.

        Supports filtering by store type, active status, and search conditions.
        Special search types like "datetime" and "day-of-week" allow filtering
        based on business hours.

        Args:
            page (int): Page number.
            per_page (int): Items per page.
            store_type (str): Optional store type filter.
            search_fields (str): Column or custom search type.
            fields_value (str): Search value.
            only_active (bool): Return only active stores if True.

        Returns:
            dict: Contains store data and total page count.
        """
        query = self.db.query(Stores)
        if store_type:
            query = query.filter(func.lower(Stores.store_type) == store_type.lower())
        if only_active:
            query = query.filter(Stores.is_active == only_active)
        
        if search_fields and fields_value:
            if hasattr(Stores, search_fields):
                query = query.filter(getattr(Stores, search_fields).ilike(f"%{fields_value}%"))
            else:
                if search_fields == 'datetime':
                    store_id_list = self._get_store_ids_by_datetime(fields_value)
                elif search_fields == 'day-of-week':
                    store_id_list = self._get_store_ids_by_weekday(fields_value)
                else:
                    self.raise_exception(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid search type.")

                query = query.filter(Stores.id.in_(store_id_list))

        total_items = query.count()
        page_items = (
            query.offset((page - 1) * per_page).limit(per_page).all()
        )
        total_pages = (total_items + per_page - 1) // per_page

        results = []
        
        if page_items:
            for item in page_items:
                results.append({
                    "store_name": item.name,
                    "store_type": item.store_type,
                    "cashbalance": item.cashbalance,
                    "is_active": item.is_active
                })

        return {"stores": results, "total_pages": total_pages}
    
    def get_store_products(
            self, 
            page:int, 
            per_page:int, 
            store_name:str,
            store_type:str,
            product_type:str, 
            search_fields:str,
            fields_value:str,
            only_active:bool,
            reverse:bool = False
        ) -> Dict:
        """
        Retrieve paginated product list for a given store.
        Supports filtering by product type, searchable fields, and active status.
        Optional price sorting via `reverse`.
        
        Args:
            page (int): Page number.
            per_page (int): Items per page.
            store_name (str): Specify store name.
            store_type (str): Specify store type.
            product_type (str): Specify product type.
            search_fields (str): Column search type.
            fields_value (str): Search value.
            only_active (bool): Return only active stores if True.
            reverse (bool): Sort order for price (ascending/descending).
        
        Returns:
            dict: Contains store data and total page count.
        """
        store_query = self.db.query(Stores).filter(
            and_(
                func.lower(Stores.name) == store_name.lower(),
                func.lower(Stores.store_type) == store_type.lower()
            )
        )

        if only_active:
            store_query = store_query.filter(Stores.is_active == only_active)

        store = store_query.first()
        if not store:
            self.raise_exception(status_code=404, detail="Store not found.")

        query = self.db.query(StoresProducts).join(Products).filter(
            StoresProducts.store_id == store.id
        )

        if only_active:
            query = query.filter(Products.is_active == only_active)
        
        query = query.filter(func.lower(Products.product_type) == product_type.lower())

        if search_fields and fields_value:
            query = query.filter(getattr(Products, search_fields).ilike(f"%{fields_value}%"))
        
        order_clause = StoresProducts.price.desc() if reverse else StoresProducts.price.asc()
        query = query.order_by(order_clause)

        total_items = query.count()
        page_items = (
            query.offset((page - 1) * per_page).limit(per_page).all()
        )
        total_pages = (total_items + per_page - 1) // per_page

        results = {
            "store_name": store.name,
            "store_type": store.store_type,
            "is_active": store.is_active,
            "products": [],
            "total_pages": total_pages
        }
        if page_items:
            for item in page_items:
                products = item.product
                results["products"].append({
                    "product_type": products.product_type,
                    "brand": products.brand,
                    "color": products.color,
                    "pack_size": products.pack_size,
                    "price": item.price,
                    "is_active": products.is_active
                })
        
        return results

    def get_store_module(self, store_name:str, store_type:str, only_active:bool=True) -> Stores:
        """
        Retrieve a store module based on store name and type.

        Args:
            store_name (str): The name of the store.
            store_type (str): The type of the store.

        Returns:
            Stores: The store module if found.
        """
        query = self.db.query(Stores).filter(
            and_(
                func.lower(Stores.name) == store_name.lower(),
                func.lower(Stores.store_type) == store_type.lower()
            )
        )

        if only_active:
            query = query.filter(Stores.is_active == only_active)
        
        item = query.first()
        if not item:
            self.raise_exception(status_code=404, detail="Store not found.")
        
        return item
