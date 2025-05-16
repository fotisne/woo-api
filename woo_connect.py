from flask import Flask, jsonify, request
from woocommerce import API
import os

app = Flask(__name__)

# WooCommerce σύνδεση μέσω μεταβλητών περιβάλλοντος
wcapi = API(
    url="https://www.joyfashionhouse.com",
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
    version="wc/v3"
)

# 🔹 API με pagination για frontend χρήση
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
        color = '-'

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
                    if attr["name"] == "Χρώμα":
                        color = attr["option"]
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

# 🔹 Πλήρες export όλων των προϊόντων για τον agent
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
            color = '-'

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
                        if attr["name"] == "Χρώμα":
                            color = attr["option"]
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

# 🔚 Εκκίνηση του Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
