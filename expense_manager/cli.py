"""Command-line interface."""
import argparse
import sys

from . import __version__
from .models import fmt
from .services import ExpenseManager


def _table(expenses):
    if not expenses:
        print("No expenses found.")
        return
    print(f"{'ID':<5}{'Date':<12}{'Category':<15}{'Amount':>12}  Description")
    print("-" * 62)
    for e in expenses:
        print(f"{e.id:<5}{e.date:<12}{e.category:<15}{fmt(e.amount_cents):>12}  {e.description}")
    print("-" * 62)
    print(f"{'Total':<32}{fmt(sum(e.amount_cents for e in expenses)):>12}")


def _bar(pct, width=20):
    filled = min(width, int(width * pct / 100))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def build_parser():
    p = argparse.ArgumentParser(prog="expense-manager", description="Personal Expense Manager")
    p.add_argument("--db", help="path to SQLite database (default: ~/.expense_manager/expenses.db)")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="add an expense")
    a.add_argument("amount"); a.add_argument("category")
    a.add_argument("-d", "--description", default=""); a.add_argument("--date", help="YYYY-MM-DD")

    l = sub.add_parser("list", help="list expenses")
    l.add_argument("-c", "--category"); l.add_argument("-m", "--month", help="YYYY-MM")
    l.add_argument("--start"); l.add_argument("--end"); l.add_argument("-s", "--search")

    e = sub.add_parser("edit", help="edit an expense")
    e.add_argument("id", type=int); e.add_argument("--amount"); e.add_argument("--category")
    e.add_argument("--description"); e.add_argument("--date")

    d = sub.add_parser("delete", help="delete an expense"); d.add_argument("id", type=int)

    b = sub.add_parser("budget", help="manage monthly budgets")
    bs = b.add_subparsers(dest="budget_cmd", required=True)
    bset = bs.add_parser("set"); bset.add_argument("category"); bset.add_argument("limit")
    brm = bs.add_parser("remove"); brm.add_argument("category")
    bst = bs.add_parser("status"); bst.add_argument("-m", "--month")

    r = sub.add_parser("report", help="spending reports")
    r.add_argument("-m", "--month", help="YYYY-MM (default: all time)")
    r.add_argument("--yearly", type=int, nargs="?", const=0, help="monthly totals for a year")

    x = sub.add_parser("export", help="export to CSV"); x.add_argument("path")
    i = sub.add_parser("import", help="import from CSV"); i.add_argument("path")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    mgr = ExpenseManager(args.db)
    try:
        if args.command == "add":
            ex = mgr.add_expense(args.amount, args.category, args.description, args.date)
            print(f"Added #{ex.id}: {fmt(ex.amount_cents)} on {ex.category} ({ex.date})")
        elif args.command == "list":
            _table(mgr.list_expenses(args.category, args.month, args.start, args.end, args.search))
        elif args.command == "edit":
            ex = mgr.update_expense(args.id, args.amount, args.category, args.description, args.date)
            print(f"Updated #{ex.id}: {fmt(ex.amount_cents)} on {ex.category} ({ex.date})")
        elif args.command == "delete":
            mgr.delete_expense(args.id); print(f"Deleted #{args.id}")
        elif args.command == "budget":
            if args.budget_cmd == "set":
                mgr.set_budget(args.category, args.limit)
                print(f"Budget for '{args.category.lower()}' set to {args.limit}/month")
            elif args.budget_cmd == "remove":
                mgr.remove_budget(args.category); print("Budget removed")
            else:
                statuses = mgr.budget_status(args.month)
                if not statuses:
                    print("No budgets set. Use: budget set <category> <limit>")
                for s in statuses:
                    flag = "  OVER BUDGET!" if s.exceeded else ""
                    print(f"{s.category:<14}{_bar(s.percent_used)} {s.percent_used:>6}%  "
                          f"{fmt(s.spent_cents)} / {fmt(s.limit_cents)}{flag}")
        elif args.command == "report":
            if args.yearly is not None:
                rows = mgr.monthly_totals(args.yearly or None)
                for m, t in rows:
                    print(f"{m}  {fmt(t):>12}")
                print(f"{'Total':<7}  {fmt(sum(t for _, t in rows)):>12}")
            else:
                total = mgr.total(args.month)
                print(f"Spending report ({args.month or 'all time'})")
                for cat, t in mgr.summary_by_category(args.month):
                    pct = 100 * t / total
                    print(f"{cat:<15}{fmt(t):>12}  {pct:5.1f}% {_bar(pct)}")
                print(f"{'TOTAL':<15}{fmt(total):>12}")
        elif args.command == "export":
            print(f"Exported {mgr.export_csv(args.path)} expenses to {args.path}")
        elif args.command == "import":
            print(f"Imported {mgr.import_csv(args.path)} expenses from {args.path}")
    except (ValueError, KeyError, FileNotFoundError) as err:
        print(f"Error: {err.args[0] if err.args else err}", file=sys.stderr)
        return 1
    finally:
        mgr.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
