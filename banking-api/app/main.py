"""A small, single-process in-memory REST API."""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Response, status

from app.models import Account, AccountInput

AccountId = Annotated[int, Path(gt=0, description="Positive account ID")]
NOT_FOUND = {404: {"description": "Account does not exist"}}


def create_app() -> FastAPI:
    """Create an independent app and fresh hard-coded sample accounts."""
    api = FastAPI(
        title="Banking REST API",
        version="1.0.0",
        description="Training CRUD backend. Data is in memory and resets on restart.",
    )
    accounts: dict[int, Account] = {
        1: Account(id=1, account_holder="Avery Johnson", account_type="checking", balance="1250.50"),
        2: Account(id=2, account_holder="Jordan Patel", account_type="savings", balance="8400.00"),
        3: Account(id=3, account_holder="Morgan Lee", account_type="checking", balance="675.25"),
    }
    next_id = 4

    def require_account(account_id: int) -> Account:
        if account_id not in accounts:
            raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
        return accounts[account_id]

    @api.get("/", tags=["Status"])
    async def welcome() -> dict[str, str]:
        return {"message": "Welcome to the Banking REST API", "status": "ok", "docs": "/docs"}

    @api.get("/accounts", response_model=list[Account], tags=["Accounts"])
    async def list_accounts() -> list[Account]:
        return list(accounts.values())

    @api.get("/accounts/{id}", response_model=Account, responses=NOT_FOUND, tags=["Accounts"])
    async def get_account(id: AccountId) -> Account:
        return require_account(id)

    @api.post("/accounts", response_model=Account, status_code=status.HTTP_201_CREATED, tags=["Accounts"])
    async def create_account(payload: AccountInput, response: Response) -> Account:
        nonlocal next_id
        account = Account(id=next_id, **payload.model_dump())
        accounts[next_id] = account
        next_id += 1
        response.headers["Location"] = f"/accounts/{account.id}"
        return account

    @api.put("/accounts/{id}", response_model=Account, responses=NOT_FOUND, tags=["Accounts"])
    async def update_account(id: AccountId, payload: AccountInput) -> Account:
        require_account(id)
        accounts[id] = Account(id=id, **payload.model_dump())
        return accounts[id]

    @api.delete("/accounts/{id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND, tags=["Accounts"])
    async def delete_account(id: AccountId) -> Response:
        require_account(id)
        del accounts[id]
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return api


app = create_app()
