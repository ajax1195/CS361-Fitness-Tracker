# CS361-Fitness-Tracker
## Fitness Tracker Implements 3 user stories for Milestone #1:

- Add a workout (type, duration, calories) with validation and persistence
- View workout history (newest first)
- Filter workouts by type (Running, Cycling, Strength, Yoga, Other)
- Data is saved to workouts.json in the same folder (simple JSON list).

### Inclusivity + Usability touches (kept simple for CLI):

-Clear, plain-language prompts and errors (IH #1, IH #3)
- Explicit path via numbered menu (IH #6)
- No color-only cues; all messages are textual

##Motivational Quote Generator Microservice

This microservice returns motivational quotes over a simple REST API. This is a microservice that Sheryll Hernandez and I worked on together. 
It is designed so other programs (like our team’s Fitness Tracker, Media app, etc.) can request a quote and display it to their users.

## How to Run
**Install Flask**
```
pip install flask
```

**Start the service**:

```
python quote_services.py
```
You should see:
Running on http://127.0.0.1:8000

You can now open:
http://localhost:8000/v1/health

Each main application can request quotes by making a GET call to:
```
GET http://localhost:8000/v1/quote
```

Or for a filtered quote:

```
GET http://localhost:8000/v1/quote?category=<category>
```
## 1. Communication Contract 
This section describes exactly how programs should request and receive data from this microservice.

## 2. Base URL

When running locally with the default settings:

```
http://localhost:8000/v1
```

Successful Response (200)
```
{
  "quote": "It always seems impossible until it’s done.",
  "author": "Nelson Mandela",
  "category": "perseverance",
  "lang": "en",
  "service": "motivational-quote-generator",
  "version": "v1"
}
```
#Error Responses

```
{
  "error": "UNSUPPORTED_PARAMETER",
  "message": "Only 'category' and 'lang' are supported."
}
```
This error occurs when the request includes unsupported parameters. The only valid parameters are 'category' and 'lang'.

#404 Not Found - no quote matches filters
```
{
  "error": "NOT_FOUND",
  "message": "No quote matches the filters."
}
```
This error occurs when no quote exists that matches the filter criteria.


```
import requests

BASE = "http://localhost:8000/v1"

r = requests.get(f"{BASE}/quote")
print(r.json())

r = requests.get(f"{BASE}/quote", params={"category": "perseverance"})
print(r.json())
```
### GET /v1/categories
Returns all valid categories that the client can use with /quote.

Example:
GET http://localhost:8000/v1/categories

Response:
```
{
  "categories": ["courage", "habit", "perseverance", "productivity"],
  "count": 4
}
``` 
### GET /health

Purpose: Simple health check to ensure the service is up and running.

#Response (200):
```
{
  "ok": true,
  "service": "motivational-quote-generator",
  "version": "v1"
}
```

### How to Request Data 
```
import requests

BASE = "http://localhost:8000/v1"

# Random quote
resp = requests.get(f"{BASE}/quote")
print(resp.json())

# Filtered quote
resp = requests.get(f"{BASE}/quote", params={"category": "perseverance"})
print(resp.json())

# All categories
resp = requests.get(f"{BASE}/categories")
print(resp.json())

```

### UML Sequence Diagram 
![UML Sequence Diagram](UML-diagram.png)

### Notes for Teammates
- All responses are returned as JSON.
- The service runs on http://localhost:8000/v1 by default.
- Only two query parameters are supported on /quote: 'category' and 'lang'.
- Use GET /v1/categories to see valid category names.
