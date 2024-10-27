from enum import Enum

from ._base import BaseModel


class Currency(Enum):
    NONE = "NONE"
    USD = "USD"
    CNY = "CNY"
    EUR = "EUR"


class Pricing(BaseModel):
    currency: Currency
    multiplier: int = 1000000
    input: float
    """actual price is input / multiplier per token"""
    output: float
