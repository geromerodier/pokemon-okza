import os
import requests
import json
import base64
import csv
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupération des identifiants depuis le .env
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# Lecture du mot-clé depuis le fichier CSV (avec un header "keyword")
try:
    with open("mot-cle.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        row = next(reader)  # lecture de la première ligne
        keyword = row["keyword"]
except Exception as e:
    print("Erreur lors de la lecture de mot-cle.csv :", e)
    exit(1)

# Encodage des identifiants en base64
credentials = f"{DATAFORSEO_USERNAME}:{DATAFORSEO_PASSWORD}"
encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

# En-têtes HTTP
headers = {
    "Authorization": f"Basic {encoded_credentials}",
    "Content-Type": "application/json"
}

# URL de l'API pour créer une tâche
post_url = "https://api.dataforseo.com/v3/merchant/google/products/task_post"

# Données de la tâche avec le mot-clé défini dans le CSV
post_data = [
    {
        "location_name": "France",
        "language_name": "French",
        "keyword": keyword
    }
]

print("Envoi de la tâche...")
post_response = requests.post(post_url, headers=headers, data=json.dumps(post_data))
result = post_response.json()
print("Réponse POST:")
print(json.dumps(result, indent=4))

# Extraction de l'ID de la tâche créée
if result.get("tasks") and len(result["tasks"]) > 0:
    task_id = result["tasks"][0]["id"]
    print("La tâche a été créée avec l'ID :", task_id)
    # Enregistrement de l'ID dans un fichier pour usage ultérieur
    with open("task_id.txt", "w") as f:
        f.write(task_id)
else:
    print("Erreur lors de la création de la tâche.")