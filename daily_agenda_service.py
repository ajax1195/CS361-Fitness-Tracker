# daily_agenda_service.py
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

TIME_FMT = "%H:%M"


def parse_time(t_str: str) -> datetime:
    return datetime.strptime(t_str, TIME_FMT)


def schedule_tasks(date_str: str, workday_start: str, workday_end: str, tasks):
    day_start = parse_time(workday_start)
    day_end = parse_time(workday_end)

    current = day_start
    blocks = []
    unscheduled = []

    # Simple greedy scheduling: tasks in the order given
    for t in tasks:
        duration = int(t.get("duration_minutes", 0))
        if duration <= 0:
            continue

        block_end = current + timedelta(minutes=duration)
        if block_end <= day_end:
            blocks.append({
                "task_id": t["id"],
                "title": t["title"],
                "start": current.strftime(TIME_FMT),
                "end": block_end.strftime(TIME_FMT),
                "unscheduled": False,
            })
            current = block_end
        else:
            unscheduled.append({
                "task_id": t["id"],
                "title": t["title"],
                "unscheduled": True,
            })

    return blocks, unscheduled


@app.post("/agenda/generate")
def generate_agenda():
    data = request.get_json() or {}
    date = data.get("date")
    workday_start = data.get("workday_start")
    workday_end = data.get("workday_end")
    tasks = data.get("tasks", [])

    if not date or not workday_start or not workday_end:
        return jsonify({"error": "date, workday_start, and workday_end are required"}), 400

    try:
        parse_time(workday_start)
        parse_time(workday_end)
    except Exception:
        return jsonify({"error": "workday_start and workday_end must be HH:MM"}), 400

    blocks, unscheduled = schedule_tasks(date, workday_start, workday_end, tasks)

    return jsonify({
        "date": date,
        "blocks": blocks,
        "unscheduled": unscheduled,
    })


if __name__ == "__main__":
    # Different port again
    app.run(port=5004)

