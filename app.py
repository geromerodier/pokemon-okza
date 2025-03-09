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

# Identifiants de connexion à l'application
APP_USERNAME = os.getenv("APP_USERNAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Identifiants DataForSEO
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# Vérifier que les identifiants d'application sont disponibles
if not APP_USERNAME or not APP_PASSWORD:
    st.error("Les identifiants de l'application ne sont pas définis dans le fichier .env")
    st.stop()

# Gestion de la connexion
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("Connexion")
    username_input = st.text_input("Nom d'utilisateur")
    password_input = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if username_input == APP_USERNAME and password_input == APP_PASSWORD:
            st.session_state.logged_in = True
            st.success("Connexion réussie!")
        else:
            st.error("Identifiants incorrects.")

if not st.session_state.logged_in:
    login()
    st.stop()

# Si connecté, affichage de l'application principale
st.title("Okza")

# --- SECTION 1 : Lancer une nouvelle recherche ---
keyword = st.text_input("Entrez un mot-clé pour lancer une nouvelle recherche :", "")

if st.button("Lancer le processus"):
    if not keyword:
        st.error("Veuillez saisir un mot-clé.")
        st.stop()
    else:
        st.info("Envoi de la tâche...")
        post_url = "https://api.dataforseo.com/v3/merchant/google/products/task_post"
        post_data = [{
            "location_name": "France",
            "language_name": "French",
            "keyword": keyword
        }]
        # Préparation de l'en-tête pour DataForSEO
        credentials_dfseo = f"{DATAFORSEO_USERNAME}:{DATAFORSEO_PASSWORD}"
        encoded_dfseo = base64.b64encode(credentials_dfseo.encode("utf-8")).decode("utf-8")
        headers_dfseo = {
            "Authorization": f"Basic {encoded_dfseo}",
            "Content-Type": "application/json"
        }
        post_response = requests.post(post_url, headers=headers_dfseo, data=json.dumps(post_data))
        result = post_response.json()
        if result.get("tasks") and len(result["tasks"]) > 0:
            task_id = result["tasks"][0]["id"]
            st.success(f"La tâche a été créée avec l'ID : {task_id}")
            # Sauvegarde de l'ID pour usage ultérieur
            with open("task_id.txt", "w", encoding="utf-8") as f:
                f.write(task_id)
        else:
            st.error("Erreur lors de la création de la tâche.")
            st.stop()

        # --- SECTION 2 : Barre de progression et attente ---
        advanced_url = f"https://api.dataforseo.com/v3/merchant/google/products/task_get/advanced/{task_id}"
        progress_bar = st.progress(0)
        status_text = st.empty()
        max_attempts = 20
        attempt = 0
        items_count = 0
        
        while attempt < max_attempts:
            data_resp = requests.get(advanced_url, headers=headers_dfseo).json()
            try:
                items_count = data_resp["tasks"][0]["result"][0]["items_count"]
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

        # --- SECTION 3 : Récupération et affichage du tableau final ---
        final_response = requests.get(advanced_url, headers=headers_dfseo)
        data_resp = final_response.json()
        try:
            items = data_resp["tasks"][0]["result"][0]["items"]
        except (KeyError, IndexError):
            st.error("Erreur : structure JSON inattendue ou aucun item n'a été retourné.")
            items = []
        
        if not items:
            st.warning("Aucun item trouvé.")
        else:
            sorted_items = sorted(items, key=lambda x: float(x.get("price", 0)))
            df = pd.DataFrame([{
                "Title": item.get("title", ""),
                "URL": f'<a href="{item.get("url", "")}" target="_blank">Lien</a>',
                "Price": item.get("price", ""),
                "Currency": item.get("currency", ""),
                "Seller": item.get("seller", "")
            } for item in sorted_items])
            
            st.subheader("Tableau des Items (Prix croissants)")
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Télécharger le tableau en CSV",
                data=csv_data,
                file_name="results_table.csv",
                mime="text/csv"
            )
            
            # Sauvegarde de la recherche dans l'historique
            history_file = "previous_results.csv"
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_history = pd.DataFrame({"recherche": [keyword], "timestamp": [now]})
            if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
                new_history.to_csv(history_file, mode="a", header=False, index=False)
            else:
                new_history.to_csv(history_file, mode="w", header=True, index=False)

# --- SECTION 4 : Affichage de l'historique des recherches ---
st.markdown("<hr>", unsafe_allow_html=True)
st.header("Historique des recherches")
history_file = "previous_results.csv"
if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
    history_df = pd.read_csv(history_file)
    # Si la colonne timestamp existe, trier par date décroissante et n'afficher que les 3 dernières recherches
    if "timestamp" in history_df.columns:
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], errors="coerce")
        history_df = history_df.sort_values("timestamp", ascending=False).head(3)
    st.markdown(history_df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("Aucune recherche précédente n'est disponible.")