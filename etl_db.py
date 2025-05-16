# Language native package
import sys
import json
import argparse
from datetime import datetime

# Third party package
from sqlalchemy import inspect
from sqlalchemy.orm import Session

# Import from other folders
from app import modules
from core.database import Base, engine, SessionLocal
from core.config import settings
from lib.etl_utils import parse_schedule, parse_product_string


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
    db = SessionLocal()
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
            registered_time=datetime.now(),
            is_admin=True
        )
        db.add(new_user)
        db.commit()
        print("Default user created successfully.")
    finally:
        db.close()


def store_etl(original_data:list, data_type:str, db:Session) -> None:
    """
    Extract, Transform, Load (ETL) process for store data.
    :param original_data: List of dictionaries containing store data
    :param data_type: Type of data to import (e.g., "pharmacy", "customer")
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
            store_name = data.get("name")
            store_type = data_type
            key = (store_name, store_type)

            # Check if the store already exists
            if key not in exists_stores:
                store = modules.Stores(
                    name=store_name,
                    store_type=store_type,
                    cashbalance=data.get("cashBalance", 0)
                )
                stores_to_add.append(store)
                exists_stores[key] = store
            else:
                store = exists_stores[key]

            products = data.get("masks", [])
            for pro in products:
                product_type = "mask"
                price = pro.get("price", 0)

                # Parse the product string to extract brand, color, and pack size
                product_details = parse_product_string(pro.get("name"))
                product_key = (
                    product_details["brand"], 
                    product_details["color"], 
                    product_details["pack_size"], 
                    product_type
                )

                # Check if the product already exists
                if product_key not in exists_products:
                    product = modules.Products(
                        product_type=product_type,
                        brand=product_details["brand"],
                        color=product_details["color"],
                        pack_size=product_details["pack_size"],
                    )
                    products_to_add.append(product)
                    exists_products[product_key] = product
                else:
                    product = exists_products[product_key]
                
                # Create the relationship between store and product by ORM
                store_product = modules.StoresProducts(
                    store=store,
                    product=product,
                    price=price
                )
                stores_products_to_add.append(store_product)

            open_timestring = data.get("openingHours")
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
        print(f"Error occurred: {e}")
    finally:
        db.close()


stores_type_list = ["pharmacy"]
def run_etl(file_path: str, data_type: str) -> None:
    """
    Run the ETL process for the given file and data type.
    :param file_path: Path to the JSON file containing data to import
    :param data_type: Type of data to import (e.g., "pharmacy", "customer")
    """
    with open(file_path, "r", encoding="utf-8") as file:
        original_data = json.load(file)
    db = SessionLocal()

    if data_type in stores_type_list:
        store_etl(original_data, data_type, db)
    elif data_type == "customer":
        pass


def parse_args() -> None:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Initialize the database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize the database")

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


def main() -> None:
    parse_args()


if __name__ == "__main__":
    main()
