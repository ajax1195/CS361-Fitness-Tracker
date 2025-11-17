from flask import Flask, jsonify, request
import random

app = Flask(__name__)

API_VERSION = "v1"

QUOTES = [
    {"text": "The secret of getting ahead is getting started.", "author": "Mark Twain", "category": "productivity", "lang": "en"},
    {"text": "It always seems impossible until it’s done.", "author": "Nelson Mandela", "category": "perseverance", "lang": "en"},
    {"text": "You miss 100% of the shots you don’t take.", "author": "Wayne Gretzky", "category": "courage", "lang": "en"},
    {"text": "Small steps every day.", "author": "Unknown", "category": "habit", "lang": "en"},
    {"text": "Fall seven times, stand up eight.", "author": "Japanese Proverb", "category": "perseverance", "lang": "en"},
]

def pick_quote(category=None, lang=None):
    pool = QUOTES
    if category:
        pool = [q for q in pool if q["category"].lower() == category.lower()]
    if lang:
        pool = [q for q in pool if q["lang"].lower() == lang.lower()]
    if not pool:
        return None
    return random.choice(pool)

@app.route(f"/{API_VERSION}/quote", methods=["GET"])
def get_quote():
    """
    GET /v1/quote?category={string}&lang={string}
    Returns: 200 JSON { quote, author, category, lang, service, version }
    Errors: 404 if no quote matches filters, 400 if unsupported params
    """
    category = request.args.get("category")
    lang = request.args.get("lang")

    # contract: only these two query params are accepted
    allowed = {"category", "lang"}
    if any(k not in allowed for k in request.args.keys()):
        return jsonify({"error": "UNSUPPORTED_PARAMETER", "message": "Only 'category' and 'lang' are supported."}), 400

    q = pick_quote(category, lang)
    if not q:
        return jsonify({"error": "NOT_FOUND", "message": "No quote matches the filters."}), 404

    return jsonify({
        "quote": q["text"],
        "author": q["author"],
        "category": q["category"],
        "lang": q["lang"],
        "service": "motivational-quote-generator",
        "version": API_VERSION
    }), 200

@app.route(f"/{API_VERSION}/categories", methods=["GET"])
def get_categories():
    cats = sorted({q["category"] for q in QUOTES})
    return jsonify({"categories": cats, "count": len(cats)}), 200

@app.route(f"/{API_VERSION}/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "motivational-quote-generator", "version": API_VERSION}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)