"""Request and response schemas shared by the CRUD endpoints."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer


class AccountInput(BaseModel):
    """All editable fields; PUT requires a complete replacement."""

    model_config = ConfigDict(extra="forbid")

    account_holder: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    account_type: Literal["checking", "savings"]
    balance: Decimal = Field(
        ge=0, max_digits=12, decimal_places=2, allow_inf_nan=False,
        description="Nonnegative amount, at most 10 integer digits and 2 decimal places.",
    )

    @field_serializer("balance", when_used="json")
    def serialize_balance(self, value: Decimal) -> str:
        """Use an exact two-decimal JSON string for money."""
        return format(value, ".2f")


class Account(AccountInput):
    """An account's ID is assigned by the server."""

    id: int = Field(gt=0)
