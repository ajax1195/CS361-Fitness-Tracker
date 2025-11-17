from flask import Flask, jsonify, request
from datetime import datetime, timezone

app = Flask(__name__)

def parse_iso8601(s: str):
    try:
        if len(s) == 10:  # YYYY-MM-DD
            dt = datetime.strptime(s, "%Y-%m-%d")
        else:
            try:
                dt = datetime.fromisoformat(s)
            except ValueError:
                dt = datetime.strptime(s, "%Y-%m-%dT%H:%M")
        return dt.astimezone().astimezone(timezone.utc)
    except Exception:
        return None

@app.get("/countdown")
def countdown():
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": "Missing 'date' query param."}), 400

    target = parse_iso8601(date_str)
    if target is None:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD or ISO 8601."}), 400

    now = datetime.now(timezone.utc)
    delta = target - now
    total = int(delta.total_seconds())

    s = abs(total)
    days, rem = divmod(s, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    if total >= 0:
        status = "UPCOMING"
        human = f"{days}d {hours}h {minutes}m {seconds}s remaining"
    else:
        status = "PAST_DUE"
        human = f"Past due by {days}d {hours}h {minutes}m {seconds}s"

    return jsonify({
        "status": status,
        "human": human,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds
    }), 200

if __name__ == "__main__":
    app.run(port=5002, debug=True)