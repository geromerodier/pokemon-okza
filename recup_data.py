import os
import requests
import json
import base64
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupération des identifiants depuis le .env
username = os.getenv("DATAFORSEO_USERNAME")
password = os.getenv("DATAFORSEO_PASSWORD")

# Préparation de l'en-tête d'authentification
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {encoded_credentials}",
    "Content-Type": "application/json"
}

# Lecture du task_id depuis le fichier "task_id.txt"
try:
    with open("task_id.txt", "r", encoding="utf-8") as f:
        task_id = f.read().strip()
except Exception as e:
    print("Erreur lors de la lecture de task_id.txt :", e)
    exit(1)

advanced_url = f"https://api.dataforseo.com/v3/merchant/google/products/task_get/advanced/{task_id}"

# Appel à l'API
response = requests.get(advanced_url, headers=headers)
data = response.json()

# Extraction des items depuis la structure JSON (on suppose que c'est data["tasks"][0]["result"][0]["items"])
try:
    items = data["tasks"][0]["result"][0]["items"]
except (KeyError, IndexError):
    print("Erreur : structure JSON inattendue ou aucun item n'a été retourné.")
    items = []

# Tri des items par prix croissant (conversion en float pour assurer le tri numérique)
sorted_items = sorted(items, key=lambda x: float(x.get("price", 0)))

# Construction du tableau HTML avec les données issues de "items"
html = """
<html>
  <head>
    <meta charset="utf-8">
    <title>Tableau des Items DataForSEO</title>
    <style>
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
      th { background-color: #f2f2f2; }
    </style>
  </head>
  <body>
    <h1>Tableau des Items (Prix croissants)</h1>
    <table>
      <tr>
        <th>Title</th>
        <th>URL</th>
        <th>Price</th>
        <th>Currency</th>
        <th>Seller</th>
      </tr>
"""

for item in sorted_items:
    title    = item.get("title", "")
    url_item = item.get("url", "")
    price    = item.get("price", "")
    currency = item.get("currency", "")
    seller   = item.get("seller", "")
    
    html += f"""
      <tr>
        <td>{title}</td>
        <td><a href="{url_item}" target="_blank">Lien</a></td>
        <td>{price}</td>
        <td>{currency}</td>
        <td>{seller}</td>
      </tr>
    """

html += """
    </table>
  </body>
</html>
"""

# Enregistrement du tableau HTML dans un fichier
with open("results_table.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Le tableau HTML trié par prix croissant a été sauvegardé dans 'results_table.html'")