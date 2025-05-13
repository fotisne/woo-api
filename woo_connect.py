from flask import Flask, jsonify
from woocommerce import API
import os

app = Flask(__name__)

# Σύνδεση με WooCommerce μέσω περιβάλλοντος (για Render)
wcapi = API(
    url="https://www.joyfashionhouse.com",
    consumer_key=os.getenv("WC_CONSUMER_KEY"),
    consumer_secret=os.getenv("WC_CONSUMER_SECRET"),
    version="wc/v3"
)

@app.route("/products")
def get_products():
    products = wcapi.get("products", params={"per_page": 70, "status": "publish"}).json()
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
            "categories": [cat["name"] for cat in product["categories"]] if product["categories"] else []
        })

    return jsonify(output)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

