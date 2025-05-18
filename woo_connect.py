from flask import Flask, jsonify, request
from woocommerce import API
import unicodedata
import os
import json
import requests

app = Flask(__name__)

# 🔐 WooCommerce σύνδεση (χρησιμοποιείται μόνο για τα live endpoints)
wcapi = API(
    url="https://www.joyfashionhouse.com",
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
    version="wc/v3"
)

# 🔠 Normalize Greek text
def normalize(text):
    return ''.join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != 'Mn'
    )

# 🎨 Εξαγωγή χρώματος
def extract_color(product):
    if product["type"] == "variable":
        variations = wcapi.get(f"products/{product['id']}/variations").json()
        for v in variations:
            for attr in v.get("attributes", []):
                if attr["name"].lower() == "χρώμα":
                    return attr["option"]
    return "-"

# 📦 Endpoint: /products (με pagination)
@app.route("/products")
def get_products():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
    except ValueError:
        return jsonify({"error": "Invalid page or per_page parameter"}), 400

    products = wcapi.get("products", params={"per_page": per_page, "page": page, "status": "publish"}).json()
    output = []

    for product in products:
        short_desc = product.get("short_description", "").strip()
        desc = product.get("description", "").strip()
        price = 0.0
        regular_price = 0.0
        sale_price = 0.0
        sizes = []
        color = extract_color(product)

        if product["type"] == "variable":
            variations = wcapi.get(f"products/{product['id']}/variations").json()
            for v in variations:
                price = v.get("price", "—")
                regular_price = v.get("regular_price", "—")
                sale_price = v.get("sale_price", "—")
                available = v.get("stock_status") == "instock"
                for attr in v["attributes"]:
                    if attr["name"] == "Μέγεθος" and available:
                        sizes.append(attr["option"])
        else:
            if product.get("stock_status") == "instock":
                sizes.append("ONE SIZE")

        output.append({
            "name": product['name'],
            "id": product['id'],
            "short_description": short_desc if short_desc else "—",
            "description": desc if desc else "—",
            "price": price,
            "regular_price": regular_price,
            "sale_price": sale_price,
            "color": color,
            "available_sizes": sizes,
            "image": product["images"][0]["src"] if product["images"] else None,
            "categories": [cat["name"] for cat in product["categories"]] if product["categories"] else [],
            "permalink": product.get("permalink")
        })

    return jsonify(output)

# 📦 Endpoint: /products-full (όλα τα προϊόντα)
@app.route("/products-full")
def get_all_products():
    all_products = []
    page = 1

    while True:
        response = wcapi.get("products", params={"per_page": 50, "page": page, "status": "publish"})
        products = response.json()
        if not products:
            break

        for product in products:
            short_desc = product.get("short_description", "").strip()
            desc = product.get("description", "").strip()
            price = 0.0
            regular_price = 0.0
            sale_price = 0.0
            sizes = []
            color = extract_color(product)

            if product["type"] == "variable":
                variations = wcapi.get(f"products/{product['id']}/variations").json()
                for v in variations:
                    price = v.get("price", "—")
                    regular_price = v.get("regular_price", "—")
                    sale_price = v.get("sale_price", "—")
                    available = v.get("stock_status") == "instock"
                    for attr in v["attributes"]:
                        if attr["name"] == "Μέγεθος" and available:
                            sizes.append(attr["option"])
            else:
                if product.get("stock_status") == "instock":
                    sizes.append("ONE SIZE")

            all_products.append({
                "name": product['name'],
                "id": product['id'],
                "short_description": short_desc if short_desc else "—",
                "description": desc if desc else "—",
                "price": price,
                "regular_price": regular_price,
                "sale_price": sale_price,
                "color": color,
                "available_sizes": sizes,
                "image": product["images"][0]["src"] if product["images"] else None,
                "categories": [cat["name"] for cat in product["categories"]] if product["categories"] else [],
                "permalink": product.get("permalink")
            })

        page += 1

    return jsonify(all_products)

# 🧠 ΝΕΟ: Αναζήτηση προϊόντων με βάση local JSON από GitHub
PRODUCTS_JSON_URL = "https://raw.githubusercontent.com/fotisne/woo-api/main/products-full.json"
LOCAL_PRODUCTS = requests.get(PRODUCTS_JSON_URL).json()

@app.route("/search")
def search():
    query = request.args.get("query", "")
    if not query:
        return jsonify([])

    keywords = [normalize(k) for k in query.split()]
    results = []

    for product in LOCAL_PRODUCTS:
        name = normalize(product.get("name", ""))
        if all(k in name for k in keywords):
            results.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "color": product.get("color"),
                "permalink": product.get("permalink")
            })

    return jsonify(results)

# 🏁 Εκκίνηση Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
