import os
import time
import json
import base64
import requests
import streamlit as st
import pandas as pd
import datetime
from dotenv import load_dotenv
import csv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()
username = os.getenv("DATAFORSEO_USERNAME")
password = os.getenv("DATAFORSEO_PASSWORD")

if not username or not password:
    st.error("Identifiants DataForSEO manquants dans le fichier .env")
    st.stop()

# Préparation de l'en-tête d'authentification
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
headers = {
    "Authorization": f"Basic {encoded_credentials}",
    "Content-Type": "application/json"
}

# Nom du fichier d'historique
history_file = "previous_results.csv"

# Configuration de la page Streamlit (mode sombre via CSS)
st.set_page_config(page_title="DataForSEO App", layout="wide")
dark_css = """
<style>
  body { background-color: #121212; color: #EEE; }
  .stDataFrame { background-color: #1e1e1e; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #444; padding: 8px; text-align: left; }
  th { background-color: #333; }
  a { color: #4da6ff; }
</style>
"""
st.markdown(dark_css, unsafe_allow_html=True)

st.title("DataForSEO Process")

# Champ de recherche toujours en haut
keyword = st.text_input("Entrez un mot-clé pour lancer une nouvelle recherche :", "")

# Bouton lancer le processus (affiché en haut)
if st.button("Lancer le processus"):
    if not keyword:
        st.error("Veuillez saisir un mot-clé.")
        st.stop()
    else:
        st.info("Envoi de la tâche...")
        # Préparer les données de la tâche
        post_url = "https://api.dataforseo.com/v3/merchant/google/products/task_post"
        post_data = [{
            "location_name": "France",
            "language_name": "French",
            "keyword": keyword
        }]
        post_response = requests.post(post_url, headers=headers, data=json.dumps(post_data))
        result = post_response.json()
        
        if result.get("tasks") and len(result["tasks"]) > 0:
            task_id = result["tasks"][0]["id"]
            st.success(f"La tâche a été créée avec l'ID : {task_id}")
            # Sauvegarde de l'ID dans un fichier pour usage ultérieur
            with open("task_id.txt", "w", encoding="utf-8") as f:
                f.write(task_id)
        else:
            st.error("Erreur lors de la création de la tâche.")
            st.stop()
        
        # Barre de progression et attente de la fin du traitement
        advanced_url = f"https://api.dataforseo.com/v3/merchant/google/products/task_get/advanced/{task_id}"
        progress_bar = st.progress(0)
        status_text = st.empty()
        max_attempts = 20
        attempt = 0
        items_count = 0
        
        while attempt < max_attempts:
            data_resp = requests.get(advanced_url, headers=headers).json()
            try:
                # Tentative d'extraction de items_count dans la structure imbriquée
                items_count = data_resp["tasks"][0]["result"][0].get("items_count", 0)
            except (KeyError, IndexError, TypeError):
                items_count = 0
            
            progress = int((attempt + 1) / max_attempts * 100)
            progress_bar.progress(progress)
            status_text.text(f"Tentative {attempt + 1}/{max_attempts} - Items count : {items_count}")
            
            if items_count > 10:
                progress_bar.progress(100)
                status_text.success(f"La tâche est prête ! Items count : {items_count}")
                break
            
            time.sleep(5)
            attempt += 1
        else:
            st.warning("La tâche n'est toujours pas prête après plusieurs tentatives.")
            st.stop()
        
        # Récupération des données finales
        final_response = requests.get(advanced_url, headers=headers)
        data_resp = final_response.json()
        # Vérification de la présence de la clé "tasks" et des sous-éléments
        if (
            "tasks" in data_resp and 
            isinstance(data_resp["tasks"], list) and len(data_resp["tasks"]) > 0 and
            "result" in data_resp["tasks"][0] and
            isinstance(data_resp["tasks"][0]["result"], list) and len(data_resp["tasks"][0]["result"]) > 0 and
            "items" in data_resp["tasks"][0]["result"][0]
        ):
            items = data_resp["tasks"][0]["result"][0]["items"]
        else:
            st.error("Erreur : structure JSON inattendue ou aucun item n'a été retourné.")
            items = []
        
        if not items:
            st.warning("Aucun item trouvé.")
        else:
            # Tri des items par prix croissant
            sorted_items = sorted(items, key=lambda x: float(x.get("price", 0)))
            # Création d'un DataFrame avec les colonnes souhaitées
            df = pd.DataFrame([{
                "Title": item.get("title", ""),
                "URL": f'<a href="{item.get("url", "")}" target="_blank">Lien</a>',
                "Price": item.get("price", ""),
                "Currency": item.get("currency", ""),
                "Seller": item.get("seller", "")
            } for item in sorted_items])
            
            st.subheader("Tableau des Items (Prix croissants)")
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Bouton pour télécharger le tableau en CSV
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Télécharger le tableau en CSV",
                data=csv_data,
                file_name="results_table.csv",
                mime="text/csv"
            )
            
            # Sauvegarde de la recherche dans l'historique
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_history = pd.DataFrame({
                "recherche": [keyword],
                "timestamp": [now]
            })
            if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
                new_history.to_csv(history_file, mode="a", header=False, index=False)
            else:
                new_history.to_csv(history_file, mode="w", header=True, index=False)

st.markdown("<hr>", unsafe_allow_html=True)

# Affichage par défaut de l'historique complet des recherches
st.header("Historique des recherches")
if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
    history_df = pd.read_csv(history_file)
    # Trier l'historique par date décroissante
    if "timestamp" in history_df.columns:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], errors="coerce")
        history_df = history_df.sort_values("timestamp", ascending=False)
    # Afficher l'historique complet
    st.markdown(history_df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("Aucune recherche précédente n'est disponible.")
