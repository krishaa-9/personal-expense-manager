# 💰 Personal expense manager

![CI](https://github.com/krishaa-9/expense-manager/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A command-line application to track personal expenses, set monthly category budgets, and view spending reports. Built with Python and SQLite — **zero runtime dependencies**.

> Software Engineering Implementation Project

## ✨ Features

- **CRUD** – add, list, edit and delete expenses
- **Filtering** – by category, month, date range, or description keyword
- **Budgets** – set monthly limits per category with usage bars and over-budget alerts
- **Reports** – category breakdown with percentages, and year-wise monthly totals
- **CSV import / export** – back up your data or move it to Excel
- **Accurate money handling** – amounts stored as integer cents (no floating-point errors)
- **Input validation** – clear error messages for bad amounts, dates and categories
- **Tested** – 14 automated tests + GitHub Actions CI

## 🚀 Quick Start

```bash
git clone https://github.com/krishaa-9/personal-expense-manager.git
cd personal-expense-manager
python -m expense_manager --help
```

Requires Python 3.9+. For running tests: `pip install -r requirements.txt`.

## 📖 Usage

```bash
# Add expenses (amount, category, optional description/date)
python -m expense_manager add 450 food -d "Groceries" --date 2026-10-02
python -m expense_manager add 1500 rent

# List and filter
python -m expense_manager list
python -m expense_manager list -c food -m 2026-10
python -m expense_manager list -s "bus"

# Edit / delete
python -m expense_manager edit 1 --amount 475
python -m expense_manager delete 2

# Budgets
python -m expense_manager budget set food 500
python -m expense_manager budget status -m 2026-10
python -m expense_manager budget remove food

# Reports
python -m expense_manager report -m 2026-10
python -m expense_manager report --yearly 2026

# CSV
python -m expense_manager export backup.csv
python -m expense_manager import backup.csv
```

Use `--db path/to/file.db` to choose a database file (default: `~/.expense_manager/expenses.db`).

### Sample output

```
$ python -m expense_manager budget status -m 2026-10
food          [####################]  114.0%  570.00 / 500.00  OVER BUDGET!
transport     [################....]   80.0%  800.00 / 1,000.00

$ python -m expense_manager report -m 2026-10
Spending report (2026-10)
rent               1,500.00   52.3% [##########..........]
transport            800.00   27.9% [#####...............]
food                 570.00   19.9% [###.................]
TOTAL              2,870.00
```

## 🏗️ Architecture

Layered design with separation of concerns:

```
expense_manager/
├── cli.py        # Presentation layer – argument parsing & output
├── services.py   # Business logic – validation, budgets, reports
├── models.py     # Domain objects & money helpers
└── database.py   # Persistence layer – SQLite schema & connection
```

See [docs/DESIGN.md](docs/DESIGN.md) for requirements, use cases, ER diagram and test plan.

## 🧪 Running Tests

```bash
pip install -r requirements.txt
pytest -v
```

## 🔮 Future Enhancements

- Web UI (Flask / React) and charts
- Recurring expenses & income tracking
- Multi-user support with authentication
- Currency conversion

## 📄 License

MIT – see [LICENSE](LICENSE).
