from flask import Flask, jsonify, request
import unicodedata
import json
import os
from rapidfuzz import fuzz
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 🔹 Normalize helper (χωρίς τόνους, πεζά)
def normalize(text):
    text = ''.join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != 'Mn'
    )
    return text.replace("ς", "σ")

# 🔹 Φορτώνουμε προϊόντα
with open("products-full.json", "r", encoding="utf-8") as f:
    LOCAL_PRODUCTS = json.load(f)

# 🔍 Fuzzy αναζήτηση
@app.route("/search")
def search():
    query = request.args.get("query", "")
    if not query:
        return jsonify([])

    norm_query = normalize(query)
    results = []

    for product in LOCAL_PRODUCTS:
        searchable = " ".join([
            product.get("name", ""),
            product.get("short_description", ""),
            product.get("description", ""),
            product.get("color", ""),
            " ".join(product.get("categories", [])),
            " ".join(product.get("available_sizes", []))
        ])
        searchable_norm = normalize(searchable)

        score = fuzz.partial_ratio(norm_query, searchable_norm)

        if score > 70:  # 🎯 φέρνει πιο κοντινά νοηματικά
            results.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "color": product.get("color"),
                "permalink": product.get("permalink")
            })

    return jsonify(results)

# ✅ Έλεγχος υγείας
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "products_loaded": len(LOCAL_PRODUCTS)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
