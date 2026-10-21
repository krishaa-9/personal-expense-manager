import pytest
from expense_manager.services import ExpenseManager
from expense_manager.cli import main


@pytest.fixture
def mgr():
    m = ExpenseManager(":memory:")
    yield m
    m.close()


def test_add_and_get(mgr):
    e = mgr.add_expense("12.50", "Food", "lunch", "2026-01-05")
    assert e.amount_cents == 1250 and e.category == "food"
    assert mgr.get_expense(e.id).description == "lunch"


@pytest.mark.parametrize("amount", ["0", "-5", "abc", ""])
def test_invalid_amount(mgr, amount):
    with pytest.raises(ValueError):
        mgr.add_expense(amount, "food")


def test_invalid_date_and_category(mgr):
    with pytest.raises(ValueError):
        mgr.add_expense("5", "food", date="05-01-2026")
    with pytest.raises(ValueError):
        mgr.add_expense("5", "  ")


def test_float_precision(mgr):
    for _ in range(3):
        mgr.add_expense("0.10", "misc", date="2026-01-01")
    assert mgr.total() == 30


def test_update_and_delete(mgr):
    e = mgr.add_expense("10", "food", date="2026-01-01")
    mgr.update_expense(e.id, amount="20", category="travel")
    got = mgr.get_expense(e.id)
    assert got.amount_cents == 2000 and got.category == "travel"
    mgr.delete_expense(e.id)
    with pytest.raises(KeyError):
        mgr.get_expense(e.id)


def test_filters(mgr):
    mgr.add_expense("10", "food", "pizza", "2026-01-10")
    mgr.add_expense("20", "travel", "bus", "2026-02-10")
    assert len(mgr.list_expenses(category="food")) == 1
    assert len(mgr.list_expenses(month="2026-02")) == 1
    assert len(mgr.list_expenses(search="piz")) == 1
    assert len(mgr.list_expenses(start="2026-01-15")) == 1


def test_budget_status(mgr):
    mgr.set_budget("food", "100")
    mgr.add_expense("60", "food", date="2026-03-01")
    mgr.add_expense("50", "food", date="2026-03-15")
    mgr.add_expense("500", "food", date="2026-04-01")  # other month
    s = mgr.budget_status("2026-03")[0]
    assert s.spent_cents == 11000 and s.exceeded and s.percent_used == 110.0


def test_budget_update_overwrites(mgr):
    mgr.set_budget("food", "100"); mgr.set_budget("food", "200")
    assert mgr.budget_status("2026-01")[0].limit_cents == 20000


def test_reports(mgr):
    mgr.add_expense("30", "food", date="2026-01-01")
    mgr.add_expense("70", "rent", date="2026-01-02")
    mgr.add_expense("10", "food", date="2026-02-01")
    assert mgr.summary_by_category("2026-01")[0] == ("rent", 7000)
    assert mgr.monthly_totals(2026) == [("2026-01", 10000), ("2026-02", 1000)]


def test_csv_roundtrip(mgr, tmp_path):
    mgr.add_expense("12.34", "food", "a, b", "2026-01-01")
    f = tmp_path / "out.csv"
    assert mgr.export_csv(f) == 1
    other = ExpenseManager(":memory:")
    assert other.import_csv(f) == 1
    assert other.list_expenses()[0].description == "a, b"


def test_cli_flow(tmp_path, capsys):
    db = str(tmp_path / "t.db")
    assert main(["--db", db, "add", "25.5", "food", "-d", "lunch", "--date", "2026-01-01"]) == 0
    assert main(["--db", db, "list"]) == 0
    assert "lunch" in capsys.readouterr().out
    assert main(["--db", db, "delete", "999"]) == 1
