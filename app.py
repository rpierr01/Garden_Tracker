import streamlit as st
import io
from PIL import Image, ImageOps
from database import init_db, save_plant, get_all_plants, get_plant_image, delete_plant
from plantnet_api import identify_plant
import datetime

# Initialisation de la base de données
init_db()

st.set_page_config(page_title="GardenTracker", layout="wide")

st.title("🌿 GardenTracker")

tab1, tab2 = st.tabs(["➕ Ajouter une plante", "🖼️ Galerie"])

CATEGORIES = ["Arbre", "Fleur", "Plante verte", "Buisson", "Potager", "Autre"]

with tab1:
    st.header("Nouvelle Plante")
    
    uploaded_file = st.file_uploader("Prendre une photo ou uploader une image", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
        
        # Récupération des octets de l'image corrigée (orientée et sans EXIF) pour l'enregistrement
        out_io = io.BytesIO()
        image_format = image.format if image.format else 'JPEG'
        # Convertir en RGB si l'image est en PNG avec format JPEG par défaut
        if image.mode in ("RGBA", "P") and image_format == "JPEG":
            image = image.convert("RGB")
        image.save(out_io, format=image_format)
        corrected_image_bytes = out_io.getvalue()
        
        st.image(image, caption='Image sélectionnée', use_container_width=True)
        
        # Identification API (stockée dans session_state pour éviter les rechargements)
        if 'identification_results' not in st.session_state or st.session_state.get('last_uploaded') != uploaded_file.name:
            with st.spinner('Analyse par Pl@ntNet en cours...'):
                res = identify_plant(image_bytes)
                st.session_state['identification_results'] = res
                st.session_state['last_uploaded'] = uploaded_file.name
        
        res = st.session_state['identification_results']
        
        if "error" in res:
            st.error(res["error"])
            default_scientific = ""
            default_common = ""
        else:
            st.success("Identification terminée !")
            options = res["results"]
            if options:
                # Créer une liste déroulante pour choisir parmi les suggestions
                option_strings = [f"{o['common_name']} ({o['scientific_name']}) - {o['score']}%" for o in options]
                selected_option = st.selectbox("Résultats de l'identification :", option_strings)
                selected_index = option_strings.index(selected_option)
                
                default_scientific = options[selected_index]["scientific_name"]
                default_common = options[selected_index]["common_name"]
            else:
                st.warning("Aucune plante reconnue.")
                default_scientific = ""
                default_common = ""
        
        st.subheader("Informations de la plante")
        with st.form("plant_form"):
            nom_commun = st.text_input("Nom Commun", value=default_common)
            nom_scientifique = st.text_input("Nom Scientifique", value=default_scientific)
            categorie = st.selectbox("Catégorie", CATEGORIES)
            date_plantation = st.date_input("Date de plantation", value=datetime.date.today())
            notes = st.text_area("Notes", placeholder="Lieu, état de la plante, etc.")
            
            submitted = st.form_submit_button("Sauvegarder")
            if submitted:
                if nom_commun and nom_scientifique:
                    save_plant(nom_commun, nom_scientifique, str(date_plantation), corrected_image_bytes, notes, categorie)
                    st.success("Plante enregistrée avec succès !")
                    # Reset identification state
                    if 'identification_results' in st.session_state:
                         del st.session_state['identification_results']
                else:
                    st.error("Veuillez renseigner le nom commun et scientifique.")

with tab2:
    st.header("Mon Jardin")
    
    # Filtre par catégorie
    filter_categories = st.multiselect("Filtrer par catégorie :", CATEGORIES, default=[])
    
    plants = get_all_plants()
    
    # Application du filtre
    if filter_categories:
        plants = [p for p in plants if p.get('categorie') in filter_categories]
    
    if not plants:
        st.info("Aucune plante dans votre jardin pour le moment.")
    else:
        # Affichage sous forme de grille 4 colonnes
        cols = st.columns(4)
        for index, p in enumerate(plants):
            col = cols[index % 4]
            with col:
                st.subheader(p["nom_commun"])
                st.caption(f"_{p['nom_scientifique']}_")
                st.markdown(f"**Catégorie:** {p.get('categorie', 'Autre')}")
                
                # Chargement de l'image à la demande
                img_bytes = get_plant_image(p["id"])
                if img_bytes:
                    img = Image.open(io.BytesIO(img_bytes))
                    img = ImageOps.exif_transpose(img)
                    st.image(img, use_container_width=True)
                
                st.write(f"**Planté le :** {p['date_plantation']}")
                if p["notes"]:
                    st.write(f"**Notes :** {p['notes']}")
                
                if st.button("🗑️ Supprimer", key=f"del_{p['id']}"):
                    delete_plant(p["id"])
                    st.rerun()

                st.divider()
