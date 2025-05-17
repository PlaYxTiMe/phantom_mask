# Language native package
import os
import json
import random
import logging
import argparse
from typing import List, Dict
from datetime import datetime, timezone

# Third party package
from sqlalchemy import inspect
from sqlalchemy.orm import Session

# Import from other folders
from app import modules
from core.database import Base, engine, SessionLocal
from core.config import settings
from lib.etl_utils import parse_schedule, parse_product_string
from lib.etl_schemas import StoreData, CustomerData


# Setting up logging
etl_logger = logging.getLogger("etl_error")
etl_logger.setLevel(logging.INFO)

if not etl_logger.handlers:
    file_handler = logging.FileHandler("etl_error.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    etl_logger.addHandler(file_handler)


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")


def is_db_initialized() -> bool:
    """
    Check if the database has been initialized by checking if the Users table exists.
    """
    inspector = inspect(engine)
    return inspector.has_table(modules.Users.__tablename__)


def insert_default_user() -> None:
    """
    Insert the default admin user into the database.
    """
    with SessionLocal() as db:
        try:
            # Check if the default user already exists
            existing_user = db.query(modules.Users).filter(modules.Users.account == settings.ACCOUNT).first()
            if existing_user:
                print("Default user already exists.")
                return

            # Create a new user
            new_user = modules.Users(
                account=settings.ACCOUNT,
                password=settings.PASSWORD,
                nickname=settings.ACCOUNT,
                registered_time=datetime.now(timezone.utc),
                is_admin=True
            )
            db.add(new_user)
            db.commit()
            print("Default user created successfully.")
        except Exception as e:
            db.rollback()
            print(f"Error occurred while creating default user, check etl.log for details.")
            etl_logger.error(f"Error occurred while inserting default user: {e}", exc_info=True)


def get_or_create_store(
        db: Session,
        store_name: str,
        store_type: str,
        cash_balance: int,
        is_active: bool
    ) -> Dict:
    """
    Get or create a store in the database.
    :param db: Database session
    :param store_name: Name of the store
    :param store_type: Type of the store
    :param cash_balance: Cash balance of the store
    :param is_active: Whether the store is active
    """

    store_to_add = []

    store = db.query(modules.Stores).filter(
        modules.Stores.name == store_name,
        modules.Stores.store_type == store_type
    ).first()
    if not store:
        # Create a new store
        store = modules.Stores(
            name=store_name,
            store_type=store_type,
            cashbalance=cash_balance,
            is_active=is_active
        )
        store_to_add.append(store)
    else:
        if is_active:
            # Update the store's cash balance & is_active if it already exists
            store.cashbalance = cash_balance
            store.is_active = is_active
    
    return {"store": store, "store_to_add": store_to_add}


def get_or_create_product(
        db: Session,
        product_type: str,
        brand: str,
        color: str,
        pack_size: int,
        is_active: bool
    ) -> Dict:
    """
    Get or create a product in the database.
    :param db: Database session
    :param product_type: Type of the product
    :param brand: Brand of the product
    :param color: Color of the product
    :param pack_size: Pack size of the product
    :param is_active: Whether the product is active
    """

    product_to_add = []

    product = db.query(modules.Products).filter(
        modules.Products.brand == brand,
        modules.Products.color == color,
        modules.Products.pack_size == pack_size,
        modules.Products.product_type == product_type
    ).first()
    if not product:
        # Create a new product
        product = modules.Products(
            product_type=product_type,
            brand=brand,
            color=color,
            pack_size=pack_size,
            is_active=is_active
        )
        product_to_add.append(product)
    else:
        if is_active:
            # Update the product's is_active status if it already exists
            product.is_active = is_active
    return {"product": product, "product_to_add": product_to_add}


def store_etl(original_data:List[StoreData], data_type:str, db:Session) -> None:
    """
    Extract, Transform, Load (ETL) process for store data.
    :param original_data: List of dictionaries containing store data
    :param data_type: Type of data to import (e.g., "pharmacy")
    :param db: Database session
    """
    try:
        # Cache dict - used to avoid duplicate insertions
        exists_stores = {}
        exists_products = {}
        exists_opentimes = {}

        # Add collections in batches
        stores_to_add = []
        products_to_add = []
        opentimes_to_add = []
        stores_products_to_add = []
        stores_opentimes_to_add = []
        
        for data in original_data:
            store_name = data.name
            store_type = data_type
            key = (store_name, store_type)

            if key in exists_stores:
                store = exists_stores[key]
            else:
                store_creation = get_or_create_store(
                    db,
                    store_name,
                    store_type,
                    data.cashBalance,
                    True
                )
                store = store_creation["store"]
                stores_to_add.extend(store_creation["store_to_add"])
                exists_stores[key] = store

            products = data.masks
            for pro in products:
                product_type = "mask"
                price = pro.price

                # Parse the product string to extract brand, color, and pack size
                product_details = parse_product_string(pro.name)
                product_key = (
                    product_details["brand"], 
                    product_details["color"], 
                    product_details["pack_size"], 
                    product_type
                )

                if product_key in exists_products:
                    product = exists_products[product_key]
                else:
                    product_creation = get_or_create_product(
                        db,
                        product_type,
                        product_details["brand"],
                        product_details["color"],
                        product_details["pack_size"],
                        True
                    )
                    product = product_creation["product"]
                    products_to_add.extend(product_creation["product_to_add"])
                    exists_products[product_key] = product
                
                # Create the relationship between store and product by ORM
                store_product = modules.StoresProducts(
                    store=store,
                    product=product,
                    price=price
                )
                stores_products_to_add.append(store_product)

            open_timestring = data.openingHours
            # Parse the opening hours string
            timestring_parse = parse_schedule(open_timestring)
            
            for row in timestring_parse:
                opentime_key = (row["day_of_week"], row["start_time"], row["end_time"])
                # Check if the opening time already exists
                if opentime_key not in exists_opentimes:
                    opentime = modules.Opentime(
                        week_day=row["day_of_week"],
                        start_time=row["start_time"],
                        end_time=row["end_time"]
                    )
                    opentimes_to_add.append(opentime)
                    exists_opentimes[opentime_key] = opentime
                else:
                    opentime = exists_opentimes[opentime_key]
                
                # Create the relationship between store and opening time by ORM
                store_opentime = modules.StoresOpentime(
                    store=store,
                    opentime=opentime
                )
                stores_opentimes_to_add.append(store_opentime)

        db.add_all(
            stores_to_add + 
            products_to_add + 
            opentimes_to_add + 
            stores_products_to_add + 
            stores_opentimes_to_add
        )
        db.commit()
    except Exception as e:
        db.rollback()
        etl_logger.error(f"Error occurred during ETL process: {e}", exc_info=True)
        raise SystemExit(f"Error occurred during ETL process, check etl.log for details.")


def customer_etl(original_data:List[CustomerData], db:Session) -> None:
    """
    Extract, Transform, Load (ETL) process for customer data.
    :param original_data: List of dictionaries containing customer data
    :param db: Database session
    """
    
    exists_numbers = set()
    exists_stores = {}
    exists_products = {}

    customers_to_add = []
    stores_to_add = []
    products_to_add = []
    transactions_to_add = []

    try:
        for data in original_data:
            customer_name = data.name
            cash_balance = data.cashBalance
            
            while True:
                phone_number = '09' + ''.join(random.choices("0123456789", k=8))
                if phone_number not in exists_numbers:
                    exists_numbers.add(phone_number)
                    break
            
            customer = modules.Customers(
                name=customer_name,
                phone_number=phone_number,
                cashbalance=cash_balance,
                registered_time=datetime.now(timezone.utc),
                registered_by=1
            )
            customers_to_add.append(customer)

            purchase_histories = data.purchaseHistories
            for history in purchase_histories:
                store_name = history.pharmacyName
                store_type = "pharmacy"
                product_name = history.maskName
                product_type = "mask"
                transaction_amount = history.transactionAmount
                transaction_date = datetime.strptime(history.transactionDate, "%Y-%m-%d %H:%M:%S")

                store_key = (store_name, store_type)
                if store_key in exists_stores:
                    store = exists_stores[store_key]
                else:
                    store_creation = get_or_create_store(
                        db,
                        store_name,
                        store_type,
                        0,
                        False
                    )
                    store = store_creation["store"]
                    stores_to_add.extend(store_creation["store_to_add"])
                    exists_stores[store_key] = store
                
                prase_products = parse_product_string(product_name)
                product_key = (
                    prase_products["brand"],
                    prase_products["color"],
                    prase_products["pack_size"],
                    product_type
                )

                if product_key in exists_products:
                    product = exists_products[product_key]
                else:
                    product_creation = get_or_create_product(
                        db,
                        product_type,
                        prase_products["brand"],
                        prase_products["color"],
                        prase_products["pack_size"],
                        False
                    )
                    product = product_creation["product"]
                    products_to_add.extend(product_creation["product_to_add"])
                    exists_products[product_key] = product
                
                transactions = modules.Transactions(
                    transactions_type="purchase",
                    customer=customer,
                    store=store,
                    product=product,
                    unit=1,
                    amount=transaction_amount,
                    transactions_date=transaction_date,
                    description="Imported from JSON",
                    by_user=1
                )
                transactions_to_add.append(transactions)
        
        db.add_all(
            customers_to_add +
            stores_to_add +
            products_to_add +
            transactions_to_add
        )
        db.commit()
    except Exception as e:
        db.rollback()
        etl_logger.error(f"Error occurred during customer ETL process: {e}", exc_info=True)
        raise SystemExit(f"Error occurred during customer ETL process, check etl.log for details.")


def run_etl(file_path: str, data_type: str) -> None:
    """
    Run the ETL process for the given file and data type.
    :param file_path: Path to the JSON file containing data to import
    :param data_type: Type of data to import (e.g., "pharmacy", "customer")
    """
    # This list should be updated if new stores type are added
    stores_type_list = ["pharmacy"]

    if not os.path.exists(file_path):
        raise SystemExit(f"Error: File {file_path} does not exist.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            original_data = json.load(file)
    except Exception as e:
        raise SystemExit(f"Error: Failed to read file {file_path}. {e}")

    with SessionLocal() as db:
        if data_type in stores_type_list:
            try:
                validated_data = [StoreData(**data) for data in original_data]
            except Exception as e:
                etl_logger.error(f"Error occurred during data validation: {e}", exc_info=True)
                raise SystemExit(f"Error occurred during data validation, check etl.log for details.")
            store_etl(validated_data, data_type, db)
        elif data_type == "customer":
            try:
                validated_data = [CustomerData(**data) for data in original_data]
            except Exception as e:
                etl_logger.error(f"Error occurred during data validation: {e}", exc_info=True)
                raise SystemExit(f"Error occurred during data validation, check etl.log for details.")
            customer_etl(validated_data, db)
        else:
            raise SystemExit(f"Error: Unsupported data type '{data_type}'. Supported types are: pharmacy, customer.")
    print(f"ETL process for {data_type} completed successfully.")


def parse_arguments() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Initialize the database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for the init command
    init_parser = subparsers.add_parser("init", help="Initialize the database")

    # Subparser for the import command
    import_parser = subparsers.add_parser("import", help="Import data into the database")
    import_parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the file containing data to import"
    )
    import_parser.add_argument(
        "--type",
        type=str,
        required=True,
        choices=["pharmacy", "customer"]
    )
    return parser


def main() -> None:
    """
    Main entry point for the ETL script.
    Handles command execution based on parsed arguments.
    """
    parser = parse_arguments()
    args = parser.parse_args()

    if args.command == 'init':
        init_db()
        insert_default_user()
    elif args.command == "import":
        if not is_db_initialized():
            raise SystemExit("Error: Default user does not exist. Please run 'init' command first.")
        run_etl(args.file, args.type)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
