import requests

BASE = "http://localhost:8000/v1"

print("Testing /health...")
print(requests.get(f"{BASE}/health").json())

print("\nTesting /categories...")
print(requests.get(f"{BASE}/categories").json())

print("\nTesting /quote with no filters...")
print(requests.get(f"{BASE}/quote").json())

print("\nTesting /quote with category = perseverance")
print(requests.get(f"{BASE}/quote", params={"category": "perseverance"}).json())
