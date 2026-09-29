from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["Accounts"])
# all routes start with /api/v1
# Route functions take in request data and calls the service methods
# UserService Depends(...) is dependency injection so each route has access to the same instance of the service

router.post("/") # Create a new customer
def create_customer(request: CreateCustomerRequest, user_service: UserService = Depends(get_user_service)):
    return user_service.create_customer(request)

router.get("/customers") # Get list of all customers
def get_customers(user_service: UserService = Depends(get_user_service)):
    return user_service.get_customers()

router.get("/customers/{id}") # Get specific customer by id
def get_customer_by_id(customer_id: int, user_service: UserService = Depends(get_user_service)):
    return user_service.get_customer_by_id(customer_id)

router.put("/customers/{id}") # Update a customer's info by id
def update_customer(customer_id: int, request: UpdateCustomerRequest, user_service: UserService = Depends(get_user_service)):
    return user_service.update_customer(customer_id, request)

router.delete("/customers/{id}") # Delete customer by id
def delete_customer(customer_id: int, user_service: UserService = Depends(get_user_service)):
    return user_service.delete_customer(customer_id)

router.post("/accounts") # Create a new bank account 
def create_account(request: CreateAccountRequest, user_service: UserService = Depends(get_user_service)):
    return user_service.create_account(request)

router.post("/transactions/transfer") # Transfer funds between accounts
def transfer_funds(request: TransferFundsRequest, user_service: UserService = Depends(get_user_service)):
    return user_service.transfer_funds(request)