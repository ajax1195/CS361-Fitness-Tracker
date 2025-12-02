import json
import os
from datetime import datetime
from typing import List, Dict

from urllib.request import urlopen, Request
from urllib.parse import urlencode
import urllib.error

DATA_FILE = "workouts.json"
TYPES = ["Running", "Cycling", "Strength", "Yoga", "Other"]

# Microservice base URLs
QUOTE_SERVICE_BASE = "http://localhost:8000/v1"
OVERDUE_SERVICE_BASE = "http://localhost:8101/v1"
WEEKLY_SERVICE_BASE = "http://localhost:8102/v1"
DAILY_AGENDA_BASE = "http://localhost:5004"


def load_all() -> List[Dict]:
    """Load all workouts from the JSON file"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        # If file corrupts warn user and start fresh
        print("Warning: could not read workouts.json, starting with an empty list.")
        return []


def save_all(items: List[Dict]) -> None:
    """Save all workouts to the JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


# ---------- Helper for microservices ----------

def _workouts_to_items(workouts: List[Dict]) -> List[Dict]:
    """
    Convert stored workouts into generic 'items' for the microservices.
    """
    items: List[Dict] = []
    for idx, w in enumerate(workouts, start=1):
        occurred = w.get("occurredAt", "")
        # Prefer explicit dueDate otherwise derive from occurredAt if present
        due = w.get("dueDate", "")
        if not due and isinstance(occurred, str) and len(occurred) >= 10:
            due = occurred[:10]

        completed = bool(w.get("completed", True))  # default True for old records

        items.append(
            {
                "id": str(idx),
                "title": f"{w.get('type', 'Workout')} ({w.get('durationMin', 0)} min)",
                "occurredAt": occurred,
                "dueDate": due,
                "durationMin": w.get("durationMin", 0),
                "category": w.get("type", "Other"),
                "completed": completed,
            }
        )
    return items


# ---------- User Story 1: Add Workout ----------

def add_workout() -> None:
    """Prompt the user for a workout and save it if valid."""
    print("\n=== Add Workout ===")
    print("Choose a type:")
    for i, t in enumerate(TYPES, start=1):
        print(f"  {i}) {t}")

    # Type
    while True:
        t_in = input("Enter number (1-5): ").strip()
        if t_in.isdigit():
            idx = int(t_in)
            if 1 <= idx <= len(TYPES):
                wtype = TYPES[idx - 1]
                break
        print("Please enter a number between 1 and 5 (e.g., 1 for Running).")

    # Duration
    while True:
        d_in = input("Duration in minutes (positive whole number): ").strip()
        if d_in.isdigit():
            duration = int(d_in)
            if duration > 0:
                break
        print("Duration must be a positive whole number (e.g., 30).")

    # Calories
    while True:
        c_in = input("Calories (optional, whole number; press Enter to skip): ").strip()
        if c_in == "":
            calories = None
            break
        if c_in.isdigit():
            calories = int(c_in)
            break
        print("Calories must be a whole number (e.g., 250) or left blank.")

    # Due date set by the user
    while True:
        due_in = input("Date you want to complete this workout by (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(due_in, "%Y-%m-%d")
            due_date = due_in
            break
        except ValueError:
            print("Please enter a valid date in YYYY-MM-DD format (e.g., 2025-12-01).")

    # Completed flag
    done_in = input("Have you already completed this workout? (y/n, default n): ").strip().lower()
    completed = done_in == "y"

    # Build record
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")  # UTC timestamp
    record = {
        "occurredAt": now_iso,
        "dueDate": due_date,
        "type": wtype,
        "durationMin": duration,
        "calories": calories,
        "completed": completed,
    }

    items = load_all()
    items.append(record)
    # newest first by creation time
    items.sort(key=lambda r: r.get("occurredAt", ""), reverse=True)
    save_all(items)

    print("\nWorkout saved successfully!")
    print(f"- Logged (UTC): {now_iso}")
    print(f"- Type:         {wtype}")
    print(f"- Duration:     {duration} min")
    print(f"- Due by:       {due_date}")
    print(f"- Completed:    {'Yes' if completed else 'No'}")
    print(f"- Calories:     {calories if calories is not None else '—'}")


# ---------- User Story 2: View Workout History ----------

def view_history(items: List[Dict]) -> None:
    """Print all workouts or a friendly empty state."""
    print("\n=== Workout History ===")
    if not items:
        print("No workouts yet. Use 'Add Workout' to create your first entry.")
        return

    print(f"Total workouts: {len(items)}")
    print("-" * 80)
    print(f"{'Logged (UTC)':<20} {'Due Date':<12} {'Type':<10} {'Duration':<10} {'Status':<10} {'Calories':<10}")
    print("-" * 80)
    for r in items:
        logged = r.get("occurredAt", "")
        due = r.get("dueDate", "")
        typ = r.get("type", "")
        dur = r.get("durationMin", 0)
        cal = r.get("calories", None)
        cal_txt = str(cal) if cal is not None else "—"
        status = "Done" if r.get("completed", True) else "Planned"
        print(f"{logged:<20} {due:<12} {typ:<10} {str(dur)+' min':<10} {status:<10} {cal_txt:<10}")


# ---------- User Story 3: Filter by Type ----------

def filter_by_type(items: List[Dict]) -> None:
    """Let the user choose a type and show only those workouts."""
    print("\n=== Filter by Type ===")
    if not items:
        print("No workouts to filter yet.")
        return

    print("Choose a type to view:")
    print("  0) All")
    for i, t in enumerate(TYPES, start=1):
        print(f"  {i}) {t}")

    sel = None
    while True:
        choice = input("Enter number (0-5): ").strip()
        if choice.isdigit():
            n = int(choice)
            if n == 0:
                sel = "All"
                break
            if 1 <= n <= len(TYPES):
                sel = TYPES[n - 1]
                break
        print("Please enter 0 for All, or 1-5 for a specific type.")

    if sel == "All":
        filtered = items
    else:
        filtered = [r for r in items if r.get("type") == sel]

    print(f"\nShowing: {sel}")
    if not filtered:
        print("No workouts match this filter.")
        return

    print("-" * 80)
    print(f"{'Logged (UTC)':<20} {'Due Date':<12} {'Type':<10} {'Duration':<10} {'Status':<10} {'Calories':<10}")
    print("-" * 80)
    for r in filtered:
        logged = r.get("occurredAt", "")
        due = r.get("dueDate", "")
        typ = r.get("type", "")
        dur = r.get("durationMin", 0)
        cal = r.get("calories", None)
        cal_txt = str(cal) if cal is not None else "—"
        status = "Done" if r.get("completed", True) else "Planned"
        print(f"{logged:<20} {due:<12} {typ:<10} {str(dur)+' min':<10} {status:<10} {cal_txt:<10}")
    print(f"\nCount: {len(filtered)}")


# ---------- HTTP helpers ----------

def _http_get_json(path: str, params: Dict[str, str] | None = None) -> Dict:
    """
    Minimal GET JSON helper using urllib
    Raises urllib.error.URLError / HTTPError on network/HTTP problems.
    """
    qs = f"?{urlencode(params)}" if params else ""
    url = f"{QUOTE_SERVICE_BASE}{path}{qs}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=5) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)


def _http_post_json(url: str, payload: dict) -> dict:
    """Send JSON via POST and return parsed JSON response"""
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=5) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text)
    except urllib.error.HTTPError as e:
        try:
            text = e.read().decode("utf-8")
            return json.loads(text)
        except Exception:
            return {"error": "HTTPError", "message": str(e)}
    except urllib.error.URLError as e:
        return {"error": "URLError", "message": str(e)}


# ---------- Quotes microservice ----------

def motivational_quote() -> None:
    """
    Calls the Motivational Quote Generator microservice and prints a quote.
    """
    print("\n=== Motivation ===")
    cat = input("Optional category (press Enter to skip): ").strip()
    params = {"category": cat} if cat else None

    try:
        data = _http_get_json("/quote", params=params)
        print("\n“" + data.get("quote", "") + "”")
        print(" — " + data.get("author", "Unknown"))
        print(f"(category: {data.get('category','?')}, lang: {data.get('lang','?')})")
    except urllib.error.HTTPError as e:
        # Handles contract errors 404 NOT_FOUND or 400 UNSUPPORTED_PARAMETER
        try:
            err_json = json.loads(e.read().decode("utf-8"))
            msg = err_json.get("message", str(e))
        except Exception:
            msg = str(e)
        print(f"\nCould not fetch a quote (HTTP {e.code}): {msg}")
    except urllib.error.URLError as e:
        print("\nCould not reach the quote service. Is it running on http://localhost:8000?")
        print(f"Network error: {e.reason}")
    except Exception as e:
        print("\nUnexpected error while fetching quote:", e)


# ---------- Overdue & At-Risk microservice ----------

def show_overdue_items() -> None:
    """Call the Overdue microservice and print any overdue workouts."""
    workouts = load_all()
    items = _workouts_to_items(workouts)

    payload = {
        "items": [
            {
                "id": it["id"],
                "title": it["title"],
                "dueDate": it["dueDate"],
                "completed": it["completed"],
            }
            for it in items
        ]
    }

    result = _http_post_json(f"{OVERDUE_SERVICE_BASE}/overdue", payload)
    print("\n=== Overdue Workouts (Microservice) ===")

    if "overdue" not in result:
        print("Error from microservice:", result)
        return

    if not result["overdue"]:
        print("No overdue workouts found. Nice work staying on track!")
        return

    for row in result["overdue"]:
        print(
            f"- {row['title']} (due {row['dueDate']}, "
            f"{row['daysOverdue']} days overdue)"
        )


def show_at_risk_items() -> None:
    """Call the At-Risk endpoint and print workouts due soon."""
    workouts = load_all()
    items = _workouts_to_items(workouts)

    payload = {
        "items": [
            {
                "id": it["id"],
                "title": it["title"],
                "dueDate": it["dueDate"],
                "completed": it["completed"],
            }
            for it in items
        ],
        "riskWindowDays": 5,
    }

    result = _http_post_json(f"{OVERDUE_SERVICE_BASE}/atrisk", payload)
    print("\n=== At-Risk Workouts (Microservice) ===")

    if "atRisk" not in result:
        print("Error from microservice:", result)
        return

    if not result["atRisk"]:
        print("No at-risk workouts in the next few days.")
        return

    for row in result["atRisk"]:
        print(
            f"- {row['title']} (due {row['dueDate']}, "
            f"{row['daysRemaining']} days remaining, risk={row['risk']})"
        )


# ---------- Weekly Summary microservice ----------

def show_weekly_summary() -> None:
    """Call the Weekly Summary microservice and show stats for the current week."""
    workouts = load_all()
    items = _workouts_to_items(workouts)

    payload_items = [
        {
            "id": it["id"],
            "completedAt": it["occurredAt"],
            "durationMin": it["durationMin"],
            "category": it["category"],
        }
        for it in items
        if it["completed"] and it["occurredAt"]
    ]

    payload = {"items": payload_items}

    result = _http_post_json(f"{WEEKLY_SERVICE_BASE}/weekly-summary", payload)
    print("\n=== Weekly Progress Summary (Microservice) ===")

    if "totalCompleted" not in result:
        print("Error from microservice:", result)
        return

    print(f"Week: {result['weekStart']} to {result['weekEnd']}")
    print(f"Total workouts completed: {result['totalCompleted']}")
    print(f"Total minutes: {result['totalDurationMin']}")

    if result.get("byCategory"):
        print("\nBy category:")
        for cat, info in result["byCategory"].items():
            print(f"- {cat}: {info['count']} workouts, {info['durationMin']} minutes")



def show_daily_agenda() -> None:
    """Call Daily Agenda microservice and print the schedule."""
    workouts = load_all()
    if not workouts:
        print("\nNo workouts found. Add some workouts first.")
        return

    print("\n=== Generate Daily Agenda ===")
    date_str = input("Date for agenda (YYYY-MM-DD, blank = today): ").strip()
    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    workday_start = input("Workday start (HH:MM, default 09:00): ").strip() or "09:00"
    workday_end = input("Workday end (HH:MM, default 17:00): ").strip() or "17:00"

    items = _workouts_to_items(workouts)

    tasks = [
        {
            "id": it["id"],
            "title": it["title"],
            "duration_minutes": it["durationMin"],
        }
        for it in items
        if it["durationMin"] > 0
    ]

    payload = {
        "date": date_str,
        "workday_start": workday_start,
        "workday_end": workday_end,
        "tasks": tasks,
    }

    result = _http_post_json(f"{DAILY_AGENDA_BASE}/agenda/generate", payload)

    if "blocks" not in result:
        print("\nError from Daily Agenda service:", result)
        return

    print(f"\n=== Daily Agenda for {result.get('date', date_str)} ===")
    if not result["blocks"]:
        print("No tasks could be scheduled in the workday window.")
    else:
        print("Scheduled blocks:")
        for block in result["blocks"]:
            print(
                f"- {block['start']}–{block['end']}: {block['title']} "
                f"(task {block['task_id']})"
            )

    if result.get("unscheduled"):
        print("\nUnscheduled tasks (did not fit):")
        for u in result["unscheduled"]:
            print(f"- {u['title']} (task {u['task_id']})")
    else:
        print("\nAll tasks fit into the workday window!")


# ---------- Menu main loop ----------

def main_menu():
    """Simple numbered menu to provide an explicit path."""
    while True:
        print("\n=== Fitness Tracker ===")
        print("1) Add Workout")
        print("2) View History")
        print("3) Filter by Type")
        print("4) Get Motivation")
        print("5) Show Overdue Workouts")
        print("6) Show At-Risk Workouts")
        print("7) Weekly Progress Summary")
        print("8) Generate Daily Agenda")
        print("9) Quit")
        choice = input("Choose an option (1-9): ").strip()

        if choice == "1":
            add_workout()
        elif choice == "2":
            items = load_all()
            items.sort(key=lambda r: r.get("occurredAt", ""), reverse=True)
            view_history(items)
        elif choice == "3":
            items = load_all()
            items.sort(key=lambda r: r.get("occurredAt", ""), reverse=True)
            filter_by_type(items)
        elif choice == "4":
            motivational_quote()
        elif choice == "5":
            show_overdue_items()
        elif choice == "6":
            show_at_risk_items()
        elif choice == "7":
            show_weekly_summary()
        elif choice == "8":
            show_daily_agenda()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Please enter a number from 1 to 9.")


if __name__ == "__main__":
    main_menu()

