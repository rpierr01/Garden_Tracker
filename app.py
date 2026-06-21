import streamlit as st
import io
from PIL import Image, ImageOps
from database import init_db, save_plant, get_all_plants, get_plant_photos, delete_plant, add_plant_photo
from plantnet_api import identify_plant, identify_disease
import datetime

# Initialisation de la base de données
init_db()

st.set_page_config(page_title="Suivi de Plantes d'Intérieur", layout="wide")

# Fonction pour convertir une date AAAA-MM-JJ au format français JJ/MM/AAAA
def format_date_fr(date_str):
    if not date_str:
        return "Inconnue"
    try:
        # Tente de lire le format standard AAAA-MM-JJ et le convertit en JJ/MM/AAAA
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        # En cas d'erreur ou si la date est déjà modifiée, on retourne la chaîne brute
        return date_str

# Affichage du quota dans la barre latérale si disponible
if 'api_quota' not in st.session_state:
    st.session_state['api_quota'] = "Inconnu"

# MENU DE NAVIGATION DANS LA BARRE LATÉRALE GAUCHE
with st.sidebar:
    st.title("🌿 Navigation")
    page = st.radio(
        "Aller à :",
        ["➕ Ajouter une plante", "🖼️ Mes Plantes", "🩺 Soigner une maladie"]
    )
    
    st.divider()
    
    st.title("📊 Informations API")
    st.metric(label="Requêtes restantes", value=st.session_state['api_quota'])
    st.caption("Le quota se met à jour après chaque identification Pl@ntNet.")

st.title("🪴 Suivi de Plantes d'Intérieur")

# AFFICHAGE DU CONTENU EN FONCTION DE LA PAGE SÉLECTIONNÉE
if page == "➕ Ajouter une plante":
    st.header("Nouvelle Plante")
    
    uploaded_file = st.file_uploader("Prendre une photo ou uploader une image", type=['png', 'jpg', 'jpeg'], key="upload_nouvelle")
    
    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
        
        out_io = io.BytesIO()
        image_format = image.format if image.format else 'JPEG'
        if image.mode in ("RGBA", "P") and image_format == "JPEG":
            image = image.convert("RGB")
        image.save(out_io, format=image_format)
        corrected_image_bytes = out_io.getvalue()
        
        col_img, _ = st.columns([1, 1])
        with col_img:
            st.image(image, caption='Image sélectionnée', use_container_width=True)
        
        if 'identification_results' not in st.session_state or st.session_state.get('last_uploaded') != uploaded_file.name:
            with st.spinner('Analyse par Pl@ntNet en cours...'):
                res = identify_plant(image_bytes)
                st.session_state['identification_results'] = res
                st.session_state['last_uploaded'] = uploaded_file.name
                
                if "quota" in res:
                    st.session_state['api_quota'] = res["quota"]
        
        res = st.session_state['identification_results']
        
        if "error" in res:
            st.error(res["error"])
            default_scientific, default_common, default_family, default_genus = "", "", "", ""
        else:
            st.success("Identification terminée !")
            options = res["results"]
            if options:
                option_strings = []
                for o in options:
                    primary_name = o['common_names'][0] if o['common_names'] else "Inconnu"
                    option_strings.append(f"{primary_name} ({o['scientific_name']}) - {o['score']}%")
                
                selected_option = st.selectbox("Résultats de l'identification :", option_strings)
                selected_index = option_strings.index(selected_option)
                
                selected_data = options[selected_index]
                default_scientific = selected_data["scientific_name"]
                default_common = ", ".join(selected_data["common_names"]) if selected_data["common_names"] else ""
                default_family = selected_data["family"]
                default_genus = selected_data["genus"]
            else:
                st.warning("Aucune plante reconnue.")
                default_scientific, default_common, default_family, default_genus = "", "", "", ""
        
        st.subheader("Informations de la plante")
        with st.container(border=True):
            with st.form("plant_form"):
                nom_commun = st.text_input("Nom(s) Commun(s)", value=default_common)
                nom_scientifique = st.text_input("Nom Scientifique", value=default_scientific)
                
                col1, col2 = st.columns(2)
                with col1:
                    famille = st.text_input("Famille Botanique", value=default_family)
                with col2:
                    genre = st.text_input("Genre", value=default_genus)
                    
                # Ajout de format="DD/MM/YYYY" pour l'affichage en français dans le calendrier
                date_plantation = st.date_input("Date de plantation", value=datetime.date.today(), format="DD/MM/YYYY")
                notes = st.text_area("Notes", placeholder="Lieu, état de la plante, etc.")
                
                submitted = st.form_submit_button("Sauvegarder ma plante", use_container_width=True)
                if submitted:
                    if nom_commun and nom_scientifique:
                        save_plant(nom_commun, nom_scientifique, str(date_plantation), corrected_image_bytes, notes, famille, genre)
                        st.success("Plante enregistrée avec succès ! Allez dans le menu 'Mes Plantes' pour la voir.")
                        if 'identification_results' in st.session_state:
                             del st.session_state['identification_results']
                    else:
                        st.error("Veuillez renseigner le nom commun et scientifique.")

elif page == "🖼️ Mes Plantes":
    st.header("Mes Plantes")
    
    plants = get_all_plants()
    familles_disponibles = sorted(list(set([p.get('famille') for p in plants if p.get('famille')])))
    
    filter_familles = st.multiselect("Filtrer par famille taxonomique :", familles_disponibles, default=[], placeholder="Choisissez des options...")
    st.write("") 
    
    if filter_familles:
        plants = [p for p in plants if p.get('famille') in filter_familles]
    
    if not plants:
        st.info("Aucune plante enregistrée ou correspondant à vos filtres.")
    else:
        cols = st.columns(3, gap="large")
        for index, p in enumerate(plants):
            col = cols[index % 3]
            with col:
                with st.container(border=True):
                    st.subheader(p["nom_commun"].split(",")[0] if p["nom_commun"] else "Inconnue")
                    st.caption(f"_{p['nom_scientifique']}_")
                    
                    meta_info = ""
                    if p.get('famille'): meta_info += f"**Famille:** {p['famille']}"
                    if p.get('genre'): meta_info += f" | **Genre:** {p['genre']}" if meta_info else f"**Genre:** {p['genre']}"
                    if meta_info:
                        st.markdown(meta_info)
                    
                    # Application du format français pour la date de plantation
                    st.write(f"**Planté/Acquis le :** {format_date_fr(p['date_plantation'])}")
                    if p["notes"]:
                        st.write(f"**Notes :** {p['notes']}")
                    
                    images_data = get_plant_photos(p["id"])
                    
                    if images_data:
                        latest_img = Image.open(io.BytesIO(images_data[0]['blob']))
                        latest_img = ImageOps.exif_transpose(latest_img)
                        # Application du format français pour la date de la photo principale
                        st.image(latest_img, caption=f"Le {format_date_fr(images_data[0]['date'])}", use_container_width=True)
                        
                        if len(images_data) > 1:
                            with st.expander("Voir l'historique des photos"):
                                for img_data in images_data[1:]:
                                    # Application du format français pour les photos de l'historique
                                    st.caption(f"Au {format_date_fr(img_data['date'])}")
                                    past_img = Image.open(io.BytesIO(img_data['blob']))
                                    past_img = ImageOps.exif_transpose(past_img)
                                    st.image(past_img, use_container_width=True)
                    
                    with st.expander("📸 Ajouter une photo"):
                        new_photo_file = st.file_uploader("Nouvelle photo", type=['png', 'jpg', 'jpeg'], key=f"upload_{p['id']}", label_visibility="collapsed")
                        if st.button("Enregistrer", key=f"btn_add_img_{p['id']}", use_container_width=True):
                            if new_photo_file is not None:
                                img_bytes = new_photo_file.getvalue()
                                img_to_correct = Image.open(io.BytesIO(img_bytes))
                                img_to_correct = ImageOps.exif_transpose(img_to_correct)
                                out_io = io.BytesIO()
                                image_format = img_to_correct.format if img_to_correct.format else 'JPEG'
                                if img_to_correct.mode in ("RGBA", "P") and image_format == "JPEG":
                                    img_to_correct = img_to_correct.convert("RGB")
                                img_to_correct.save(out_io, format=image_format)
                                add_plant_photo(p["id"], out_io.getvalue(), str(datetime.date.today()))
                                st.success("Photo ajoutée !")
                                st.rerun()
                            else:
                                st.error("Veuillez sélectionner une image.")
                    
                    if st.button("🗑️ Supprimer", key=f"del_{p['id']}", type="secondary", use_container_width=True):
                        delete_plant(p["id"])
                        st.rerun()

elif page == "🩺 Soigner une maladie":
    st.header("🩺 Diagnostic des maladies")
    st.write("Votre plante fait grise mine ? Prenez en photo les feuilles ou les tiges affectées pour identifier le problème.")
    
    uploaded_disease = st.file_uploader("Uploader une photo de la zone malade", type=['png', 'jpg', 'jpeg'], key="upload_maladie")
    
    if uploaded_disease is not None:
        disease_bytes = uploaded_disease.getvalue()
        d_image = Image.open(io.BytesIO(disease_bytes))
        
        col_diag_1, col_diag_2 = st.columns([1, 2])
        with col_diag_1:
            st.image(ImageOps.exif_transpose(d_image), caption='Photo à analyser', use_container_width=True)
            diagnostique_btn = st.button("Lancer le diagnostic IA", use_container_width=True, type="primary")
            
        with col_diag_2:
            if diagnostique_btn:
                with st.spinner("Recherche des pathogènes en cours..."):
                    d_res = identify_disease(disease_bytes)
                    
                    if "quota" in d_res:
                        st.session_state['api_quota'] = d_res["quota"]
                    
                    if "error" in d_res:
                        st.error(d_res["error"])
                    else:
                        if d_res["results"]:
                            st.success("Diagnostic terminé !")
                            for maladie in d_res["results"]:
                                with st.container(border=True):
                                    nom_c = ", ".join(maladie["common_names"]) if maladie["common_names"] else "Nom commun inconnu"
                                    st.markdown(f"### 🦠 {nom_c} ({maladie['score']}%)")
                                    st.markdown(f"**Nom Scientifique:** {maladie['scientific_name']}")
                                    if maladie['family'] or maladie['genus']:
                                        st.markdown(f"**Pathogène:** Famille: {maladie['family']} | Genre: {maladie['genus']}")
                        else:
                            st.success("Aucune maladie connue identifiée sur cette photo.")