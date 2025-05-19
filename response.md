# Response
## Please login before using the API. Endpoint: /api/v1/auth/token
## A. Required Information
### A.1. Requirement Completion Rate
- [x] List all pharmacies open at a specific time and on a day of the week if requested.
  - Endpoint: [GET] /api/v1/stores/get_stores
  - If no parameters are provided, the API returns all stores. To maintain flexibility, I added a new parameter store_type to the stores, so that other types of stores can also be supported in the future. This API supports pagination and search functionality. The search can filter stores based on date or day of the week (please use English abbreviations for the days) within their business hours.
- [x] List all masks sold by a given pharmacy, sorted by mask name or price.
  - Endpoint: [GET] /api/v1/stores/products_by_store
  - The store name, store type (pharmacy), and product type (mask) must be provided to list all products available at the specified store. This API supports pagination and advanced search features, allowing further filtering by product type, brand, and color. The search results can also be sorted by price in ascending or descending order based on the reverse parameter.
- [x] List all pharmacies with more or less than x mask products within a price range.
  - Endpoint: [GET] /api/v1/products/get_store_by_product_price
  - You must provide the product type (mask), unit price, and a comparison condition (gt, lt, ge, etc.). The API will return a list of stores and their products that match the given price condition. You can also apply additional filtering based on the store type.
- [x] The top x users by total transaction amount of masks within a date range.
  - Endpoint: [GET] /api/v1/transactions/top-by-transactions
  - A new field transactions_type has been added to the transactions data, allowing flexible tracking of various transaction types (e.g., recharge, refund, etc.). When using this API, you must provide the transaction type (purchase), product type (mask), and a time range (start–end). You can also specify rank_scope to determine the number of top-ranking results to return (e.g., top 10, top 5, etc.).
- [x] The total number of masks and dollar value of transactions within a date range.
  - Endpoint: [GET] /api/v1/transactions/summary_by_transactions
  - You must provide the transaction type (purchase), product type (mask), and a time range. The API will return all matching transaction records along with the total amount and quantity summed from those transactions.(The transaction records will be sorted by transaction time in descending order.)
- [x] Search for pharmacies or masks by name, ranked by relevance to the search term.
  - Endpoint: [GET] /api/v1/products/get_products
  - You must provide the product type (e.g., mask). Pagination is supported, and you can further refine the search based on attributes like brand or color. The search results will be sorted and categorized by brand and color.
- [x] Process a user purchases a mask from a pharmacy, and handle all relevant data changes in an atomic transaction.
  - [POST] /api/v1/transactions/purchase
  - This API requires multiple parameters. Customer information can be retrieved from the /api/v1/customers/get_customers endpoint. For testing purposes, the remaining parameters can be conveniently filled using data from pharmacies.json.
### A.2. API Document
> Import [this](https://drive.google.com/file/d/1iy_5vEVW3tP59tzZroXny3_Pwd7vLoOr/view?usp=sharing) json file to Postman.
> API Document Endpoint: /docs or /redoc
> [Google document](https://docs.google.com/document/d/1hyj0xzWqWRY8QMrLK--tMldoir4IJ38TKA56C93HXV4/edit?tab=t.0)

### A.3. Import Data Commands
Please run these two script commands to migrate the data into the database.

Please navigate to the project directory, create a virtual environment, and install the required packages.

```bash
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

After installing the packages, please run the following command.
```bash
$ python etl_db.py init
$ python etl_db.py import --file [PATH_TO_FILE/pharmacies.json] --type pharmacy
$ python etl_db.py import --file [PATH_TO_FILE/user.json] --type customer
```
You can import either of the two files first, or even import them after the server has started.

### A.4. Start server

If it's in the testing environment, please use:
```bash
$ uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-config log.ini
```

## B. Bonus Information

>  If you completed the bonus requirements, please fill in your task below.

### B.2. Dockerized
My Dockerfile and docker-compose.yml are both inside the [Github](https://github.com/PlaYxTiMe/phantom_mask/tree/devlop). Before using docker-compose.yml, move it to the same level as the project folder. This way, other services can also use the same docker-compose in the future.

On the local machine, please follow the commands below to build it.

```bash
$ sudo su
$ docker-compose up -d --build
```

Two methods to use ETL to load the database:

1.Enter the container directly and run the command.
```bash
$ docker exec -it phantom_api_server bash
$ python etl_db.py init
$ python etl_db.py import --file [PATH_TO_FILE/pharmacies.json] --type pharmacy
$ python etl_db.py import --file [PATH_TO_FILE/user.json] --type customer
```

2.Since the files are mounted to the local machine, you can also create a virtual environment locally, install the packages, and run the ETL script to update the database inside the container simultaneously.
```bash
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ python etl_db.py init
$ python etl_db.py import --file [PATH_TO_FILE/pharmacies.json] --type pharmacy
$ python etl_db.py import --file [PATH_TO_FILE/user.json] --type customer
```

### B.3. Demo Site Url

The demo site is ready on [my AWS demo site](https://api.kurocat.space/); you can try any APIs on this demo site.

Please login before using any API.

## C. Other Information

### C.1. Other
The account credentials for the demo site will be sent to HR via email. For flexibility, I have added several additional APIs, although not all of them are fully implemented yet—you can refer to the documentation for details. To facilitate testing, the token validity on the demo site has been extended to 300 minutes. Thank you.

- --
