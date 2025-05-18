# Third party package
from fastapi import APIRouter, Depends

# Import from other folders
from app.v1.authtication.router import router as authtication_router
from app.v1.customers.router import router as customers_router
from app.v1.products.router import router as products_router
from app.v1.stores.router import router as stores_router
from app.v1.transactions.router import router as transactions_router
from app.v1.users.router import router as users_router
from app.dependencies.user import check_admin, get_current_user


router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(get_current_user)]
)

router.include_router(authtication_router, tags=["Authtication"], prefix="/auth")
router.include_router(users_router, tags=["Users"], prefix="/users", dependencies=[Depends(check_admin)])
router.include_router(stores_router, tags=["Stores"], prefix="/stores")
router.include_router(products_router, tags=["Products"], prefix="/products")
router.include_router(customers_router, tags=["Customers"], prefix="/customers")
router.include_router(transactions_router, tags=["Transactions"], prefix="/transactions")
