import math

from database.db import get_db


def get_recent_transactions(user_id, limit=10):
    """Return the user's most recent expenses, newest-first, as a list of
    sqlite3.Row (each with date, description, category, amount)."""
    conn = get_db()
    transactions = conn.execute(
        """
        SELECT date, description, category, amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    return transactions


def get_summary_stats(user_id):
    """Return {"total_spent": float, "transaction_count": int, "top_category": str}
    for the user. If the user has no expenses: total_spent=0.0, transaction_count=0,
    top_category="—" (em dash)."""
    conn = get_db()

    totals = conn.execute(
        "SELECT SUM(amount) AS total_spent, COUNT(*) AS transaction_count "
        "FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    top_category_row = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,),
    ).fetchone()

    conn.close()

    total_spent = totals["total_spent"] if totals["total_spent"] is not None else 0.0
    transaction_count = totals["transaction_count"] or 0
    top_category = top_category_row["category"] if top_category_row else "—"

    return {
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "top_category": top_category,
    }


def get_category_breakdown(user_id):
    """Return a list of {"name": str, "total": float, "percent": int} for the user,
    one entry per category that has at least one expense, ordered by total descending.
    percent values are integers that sum to exactly 100 across the list (largest-
    remainder method: floor each exact percentage, then distribute the leftover
    points one each to the categories with the largest fractional remainders). If the
    user has no expenses, return an empty list."""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return []

    grand_total = sum(row["total"] for row in rows)

    categories = []
    remainders = []
    for row in rows:
        raw_percent = (row["total"] / grand_total) * 100 if grand_total else 0
        base_percent = math.floor(raw_percent)
        remainder = raw_percent - base_percent
        categories.append(
            {"name": row["category"], "total": row["total"], "percent": base_percent}
        )
        remainders.append(remainder)

    leftover = 100 - sum(cat["percent"] for cat in categories)

    order = sorted(range(len(categories)), key=lambda i: remainders[i], reverse=True)
    for i in order[:leftover]:
        categories[i]["percent"] += 1

    return categories
