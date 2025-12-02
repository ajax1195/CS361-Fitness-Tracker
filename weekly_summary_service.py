from flask import Flask, jsonify, request
from datetime import datetime, date, timedelta
from collections import defaultdict

app = Flask(__name__)

API_VERSION = "v1"


def _parse_iso_datetime(s: str) -> datetime | None:
    try:
        if s.endswith("Z"):
            s = s[:-1]
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _parse_date_yyyy_mm_dd(s: str) -> date | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _validate_items(raw):
    if not isinstance(raw, list):
        return "Field 'items' must be a list.", None

    items = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            return f"Item at index {idx} must be an object.", None

        missing = [k for k in ("id", "completedAt", "durationMin") if k not in item]
        if missing:
            return f"Item at index {idx} missing field(s): {', '.join(missing)}", None

        ts = _parse_iso_datetime(str(item["completedAt"]))
        if ts is None:
            return f"Item {item.get('id')} has invalid completedAt timestamp.", None

        try:
            duration = int(item["durationMin"])
        except (TypeError, ValueError):
            return f"Item {item.get('id')} has invalid durationMin.", None

        items.append(
            {
                "id": str(item["id"]),
                "title": str(item.get("title", "")),
                "completedAt": ts,
                "durationMin": duration,
                "category": str(item.get("category", "Uncategorized")),
            }
        )

    return None, items


def _week_bounds(provided_start: str | None, provided_end: str | None):
    if provided_start:
        start = _parse_date_yyyy_mm_dd(provided_start)
    else:
        today = date.today()
        start = today - timedelta(days=today.weekday())  # Monday
    if start is None:
        start = date.today()

    if provided_end:
        end = _parse_date_yyyy_mm_dd(provided_end)
        if end is None:
            end = start + timedelta(days=6)
    else:
        end = start + timedelta(days=6)

    return start, end


@app.route(f"/{API_VERSION}/weekly-summary", methods=["POST"])
def weekly_summary():
    data = request.get_json(silent=True) or {}
    err, items = _validate_items(data.get("items"))
    if err:
        return jsonify({"error": "INVALID_ITEMS", "message": err}), 400

    week_start, week_end = _week_bounds(data.get("weekStart"), data.get("weekEnd"))

    total_completed = 0
    total_duration = 0
    by_cat_counts = defaultdict(int)
    by_cat_dur = defaultdict(int)

    for it in items:
        d = it["completedAt"].date()
        if week_start <= d <= week_end:
            total_completed += 1
            total_duration += it["durationMin"]
            by_cat_counts[it["category"]] += 1
            by_cat_dur[it["category"]] += it["durationMin"]

    by_category = {
        cat: {"count": by_cat_counts[cat], "durationMin": by_cat_dur[cat]}
        for cat in by_cat_counts
    }

    return (
        jsonify(
            {
                "weekStart": week_start.isoformat(),
                "weekEnd": week_end.isoformat(),
                "totalCompleted": total_completed,
                "totalDurationMin": total_duration,
                "byCategory": by_category,
            }
        ),
        200,
    )


@app.route(f"/{API_VERSION}/health", methods=["GET"])
def health():
    return jsonify(
        {"ok": True, "service": "weekly-progress-summary", "version": API_VERSION}
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8102)
