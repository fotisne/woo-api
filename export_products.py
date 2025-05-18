import json
import os
from woocommerce import API

# 🔐 WooCommerce API σύνδεση
wcapi = API(
    url="https://www.joyfashionhouse.com",
   consumer_key="ck_d4c3aab55f4192ff737a1cac745c70db1fa8451c",
consumer_secret="cs_7b88b5452edea933245a96a456814c1471202b65",
    version="wc/v3"
)

all_products = []
page = 1

while page <= 100:  # όριο ασφαλείας
    print(f"🔄 Fetching page {page}...")
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

# 💾 Αποθήκευση στο τοπικό αρχείο
with open("products-full.json", "w", encoding="utf-8") as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)

print(f"✅ Exported {len(all_products)} προϊόντα στο products-full.json")
