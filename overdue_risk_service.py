from flask import Flask, jsonify, request
from datetime import datetime, date

app = Flask(__name__)

API_VERSION = "v1"


def _parse_date_yyyy_mm_dd(s: str) -> date | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_today(s: str | None) -> date:
    """Use provided 'today' date if valid, otherwise real current date."""
    if not s:
        return date.today()
    d = _parse_date_yyyy_mm_dd(s)
    return d or date.today()


def _validate_items(raw):
    if not isinstance(raw, list):
        return "Field 'items' must be a list.", None

    items = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            return f"Item at index {idx} must be an object.", None

        missing = [k for k in ("id", "title", "dueDate", "completed") if k not in item]
        if missing:
            return f"Item at index {idx} missing field(s): {', '.join(missing)}", None

        d = _parse_date_yyyy_mm_dd(str(item["dueDate"]))
        if d is None:
            return f"Item {item.get('id')} has invalid dueDate (expected YYYY-MM-DD).", None

        completed = bool(item["completed"])

        items.append(
            {
                "id": str(item["id"]),
                "title": str(item["title"]),
                "dueDate": d,
                "completed": completed,
            }
        )

    return None, items


@app.route(f"/{API_VERSION}/overdue", methods=["POST"])
def find_overdue():
    data = request.get_json(silent=True) or {}
    err, items = _validate_items(data.get("items"))
    if err:
        return jsonify({"error": "INVALID_ITEMS", "message": err}), 400

    today = _parse_today(data.get("today"))

    overdue = []
    for it in items:
        if not it["completed"] and it["dueDate"] < today:
            days_overdue = (today - it["dueDate"]).days
            overdue.append(
                {
                    "id": it["id"],
                    "title": it["title"],
                    "dueDate": it["dueDate"].isoformat(),
                    "daysOverdue": days_overdue,
                    "status": "overdue",
                }
            )

    return jsonify({"today": today.isoformat(), "overdue": overdue}), 200


@app.route(f"/{API_VERSION}/atrisk", methods=["POST"])
def find_at_risk():
    data = request.get_json(silent=True) or {}
    err, items = _validate_items(data.get("items"))
    if err:
        return jsonify({"error": "INVALID_ITEMS", "message": err}), 400

    today = _parse_today(data.get("today"))
    risk_window = int(data.get("riskWindowDays", 5))

    result = []
    for it in items:
        if it["completed"]:
            continue

        days_remaining = (it["dueDate"] - today).days
        if 0 <= days_remaining <= risk_window:
            if days_remaining == 0:
                level = "high"
            elif days_remaining <= 2:
                level = "medium"
            else:
                level = "low"
            result.append(
                {
                    "id": it["id"],
                    "title": it["title"],
                    "dueDate": it["dueDate"].isoformat(),
                    "daysRemaining": days_remaining,
                    "risk": level,
                }
            )

    return jsonify({"today": today.isoformat(), "atRisk": result}), 200


@app.route(f"/{API_VERSION}/health", methods=["GET"])
def health():
    return jsonify(
        {"ok": True, "service": "overdue-and-at-risk-detector", "version": API_VERSION}
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8101)
