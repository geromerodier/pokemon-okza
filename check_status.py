import os
import requests
import base64
import time
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupération des identifiants depuis le .env
username = os.getenv("DATAFORSEO_USERNAME")
password = os.getenv("DATAFORSEO_PASSWORD")

# Préparation de l'en-tête d'authentification
encoded_credentials = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {encoded_credentials}",
    "Content-Type": "application/json"
}

# Lecture de l'ID de la tâche depuis "task_id.txt"
with open("task_id.txt", "r") as f:
    task_id = f.read().strip()

# Construction de l'URL avancée
advanced_url = f"https://api.dataforseo.com/v3/merchant/google/products/task_get/advanced/{task_id}"

print("Vérification de l'état de la tâche...")
while True:
    data = requests.get(advanced_url, headers=headers).json()
    try:
        # Extraction de items_count dans la structure imbriquée
        items_count = data["tasks"][0]["result"][0]["items_count"]
    except (KeyError, IndexError):
        items_count = 0

    if items_count > 10:
        print(f"La tâche est prête ! Nombre de résultats retournés : {items_count}")
        break
    else:
        print("La tâche n'est pas encore prête. Nouvelle vérification dans 5 secondes...")
        time.sleep(5)