from flask import Flask, jsonify, request
import unicodedata
import json
import os
from rapidfuzz import fuzz

app = Flask(__name__)

# 🔹 Normalize helper (χωρίς τόνους, πεζά, χωρίς σημεία στίξης)
def normalize(text):
    return ''.join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != 'Mn'
    )

# 🔹 Φόρτωσε το JSON με τα προϊόντα (π.χ. από export)
with open("products-full.json", "r", encoding="utf-8") as f:
    LOCAL_PRODUCTS = json.load(f)

# 🔍 Αναζήτηση προϊόντων με fuzzy λογική
@app.route("/search")
def search():
    query = request.args.get("query", "")
    if not query:
        return jsonify([])

    normalized_query = normalize(query)
    results = []

    for product in LOCAL_PRODUCTS:
        combined_text = normalize(" ".join([
            product.get("name", ""),
            product.get("short_description", ""),
            product.get("description", ""),
            product.get("color", ""),
            " ".join(product.get("categories", [])),
            " ".join(product.get("available_sizes", []))
        ]))

        # Υπολόγισε πόσο “κοντά” είναι το query με το προϊόν
        score = fuzz.partial_ratio(normalized_query, combined_text)

        if score >= 80:  # Κατώφλι για fuzzy match — μπορείς να το αλλάξεις
            results.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "color": product.get("color"),
                "permalink": product.get("permalink")
            })

    return jsonify(results)

# 🔧 Test route
@app.route("/health")
def health():
    return jsonify({"status": "ok", "products_loaded": len(LOCAL_PRODUCTS)})

# ▶️ Τρέξε το API
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
