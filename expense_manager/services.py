"""Business logic for the expense manager."""
import csv
from datetime import date as _date, datetime

from .database import connect
from .models import BudgetStatus, Expense, to_cents


def _norm_date(value) -> str:
    if value is None:
        return _date.today().isoformat()
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")


def _norm_cat(category: str) -> str:
    category = (category or "").strip().lower()
    if not category:
        raise ValueError("Category cannot be empty")
    return category


def _norm_month(month) -> str:
    if month is None:
        return _date.today().strftime("%Y-%m")
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%Y-%m")
    except ValueError:
        raise ValueError("Month must be in YYYY-MM format")


def _row_to_expense(r) -> Expense:
    return Expense(r["id"], r["amount_cents"], r["category"], r["description"], r["date"])


class ExpenseManager:
    def __init__(self, db_path=None):
        self.conn = connect(db_path)

    # ---------- CRUD ----------
    def add_expense(self, amount, category, description="", date=None) -> Expense:
        cents, cat, d = to_cents(amount), _norm_cat(category), _norm_date(date)
        cur = self.conn.execute(
            "INSERT INTO expenses (amount_cents, category, description, date) VALUES (?,?,?,?)",
            (cents, cat, description.strip(), d),
        )
        self.conn.commit()
        return Expense(cur.lastrowid, cents, cat, description.strip(), d)

    def get_expense(self, expense_id: int) -> Expense:
        r = self.conn.execute("SELECT * FROM expenses WHERE id=?", (expense_id,)).fetchone()
        if r is None:
            raise KeyError(f"Expense {expense_id} not found")
        return _row_to_expense(r)

    def update_expense(self, expense_id, amount=None, category=None, description=None, date=None) -> Expense:
        current = self.get_expense(expense_id)
        cents = to_cents(amount) if amount is not None else current.amount_cents
        cat = _norm_cat(category) if category is not None else current.category
        desc = description.strip() if description is not None else current.description
        d = _norm_date(date) if date is not None else current.date
        self.conn.execute(
            "UPDATE expenses SET amount_cents=?, category=?, description=?, date=? WHERE id=?",
            (cents, cat, desc, d, expense_id),
        )
        self.conn.commit()
        return Expense(expense_id, cents, cat, desc, d)

    def delete_expense(self, expense_id: int) -> None:
        self.get_expense(expense_id)
        self.conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        self.conn.commit()

    def list_expenses(self, category=None, month=None, start=None, end=None, search=None):
        sql, params = "SELECT * FROM expenses WHERE 1=1", []
        if category:
            sql += " AND category=?"; params.append(_norm_cat(category))
        if month:
            sql += " AND substr(date,1,7)=?"; params.append(_norm_month(month))
        if start:
            sql += " AND date>=?"; params.append(_norm_date(start))
        if end:
            sql += " AND date<=?"; params.append(_norm_date(end))
        if search:
            sql += " AND description LIKE ?"; params.append(f"%{search}%")
        sql += " ORDER BY date DESC, id DESC"
        return [_row_to_expense(r) for r in self.conn.execute(sql, params)]

    # ---------- Budgets ----------
    def set_budget(self, category, monthly_limit) -> None:
        cat, cents = _norm_cat(category), to_cents(monthly_limit)
        self.conn.execute(
            "INSERT INTO budgets (category, monthly_limit_cents) VALUES (?,?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit_cents=excluded.monthly_limit_cents",
            (cat, cents),
        )
        self.conn.commit()

    def remove_budget(self, category) -> None:
        self.conn.execute("DELETE FROM budgets WHERE category=?", (_norm_cat(category),))
        self.conn.commit()

    def budget_status(self, month=None):
        m = _norm_month(month)
        rows = self.conn.execute(
            """SELECT b.category, b.monthly_limit_cents,
                      COALESCE(SUM(e.amount_cents),0) AS spent
               FROM budgets b
               LEFT JOIN expenses e
                 ON e.category=b.category AND substr(e.date,1,7)=?
               GROUP BY b.category ORDER BY b.category""",
            (m,),
        ).fetchall()
        return [BudgetStatus(r["category"], r["monthly_limit_cents"], r["spent"]) for r in rows]

    # ---------- Reports ----------
    def total(self, month=None) -> int:
        sql, params = "SELECT COALESCE(SUM(amount_cents),0) FROM expenses", []
        if month:
            sql += " WHERE substr(date,1,7)=?"; params.append(_norm_month(month))
        return self.conn.execute(sql, params).fetchone()[0]

    def summary_by_category(self, month=None):
        """Returns [(category, total_cents)] sorted by highest spend."""
        sql, params = "SELECT category, SUM(amount_cents) t FROM expenses", []
        if month:
            sql += " WHERE substr(date,1,7)=?"; params.append(_norm_month(month))
        sql += " GROUP BY category ORDER BY t DESC"
        return [(r["category"], r["t"]) for r in self.conn.execute(sql, params)]

    def monthly_totals(self, year=None):
        year = str(year or _date.today().year)
        rows = self.conn.execute(
            "SELECT substr(date,1,7) m, SUM(amount_cents) t FROM expenses "
            "WHERE substr(date,1,4)=? GROUP BY m ORDER BY m", (year,),
        )
        return [(r["m"], r["t"]) for r in rows]

    # ---------- Import / Export ----------
    def export_csv(self, path) -> int:
        expenses = self.list_expenses()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "date", "category", "amount", "description"])
            for e in reversed(expenses):
                w.writerow([e.id, e.date, e.category, f"{e.amount:.2f}", e.description])
        return len(expenses)

    def import_csv(self, path) -> int:
        count = 0
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.add_expense(row["amount"], row["category"],
                                 row.get("description", ""), row.get("date") or None)
                count += 1
        return count

    def close(self):
        self.conn.close()
