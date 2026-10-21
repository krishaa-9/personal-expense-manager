"""Domain models. Money is stored as integer cents to avoid float errors."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


def to_cents(amount) -> int:
    try:
        value = Decimal(str(amount))
    except InvalidOperation:
        raise ValueError(f"Invalid amount: {amount!r}")
    if value <= 0:
        raise ValueError("Amount must be greater than zero")
    return int((value * 100).quantize(Decimal("1")))


def fmt(cents: int) -> str:
    return f"{cents / 100:,.2f}"


@dataclass
class Expense:
    id: int
    amount_cents: int
    category: str
    description: str
    date: str

    @property
    def amount(self) -> float:
        return self.amount_cents / 100


@dataclass
class BudgetStatus:
    category: str
    limit_cents: int
    spent_cents: int

    @property
    def remaining_cents(self) -> int:
        return self.limit_cents - self.spent_cents

    @property
    def percent_used(self) -> float:
        return round(100 * self.spent_cents / self.limit_cents, 1)

    @property
    def exceeded(self) -> bool:
        return self.spent_cents > self.limit_cents
