import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("PLANTNET_API_KEY")

# Ajout du paramètre lang=fr pour obtenir les noms communs en français
API_IDENTIFY_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=fr"
API_DISEASE_URL = f"https://my-api.plantnet.org/v2/identify/diseases?api-key={API_KEY}&lang=fr"

def identify_plant(image_bytes):
    if not API_KEY or API_KEY == "votre_cle_api_ici":
        return {"error": "Clé API Pl@ntNet non configurée."}

    files = [
        ('images', ('image.jpg', image_bytes))
    ]
    
    try:
        response = requests.post(API_IDENTIFY_URL, files=files)
        
        if response.status_code == 200:
            json_result = response.json()
            results = []
            
            for result in json_result.get('results', [])[:5]: # Top 5
                species = result.get('species', {})
                
                # Extraction enrichie
                scientific_name = species.get('scientificNameWithoutAuthor', species.get('scientificName', ''))
                common_names = species.get('commonNames', [])
                
                # Gestion sécurisée du dictionnaire/string pour le genre et la famille
                genus_data = species.get('genus', '')
                family_data = species.get('family', '')
                
                genus = genus_data.get('scientificNameWithoutAuthor', genus_data.get('scientificName', '')) if isinstance(genus_data, dict) else str(genus_data)
                family = family_data.get('scientificNameWithoutAuthor', family_data.get('scientificName', '')) if isinstance(family_data, dict) else str(family_data)
                
                # Le score peut être sous 'score' ou 'confidenceScore' selon l'API
                score = result.get('score', result.get('confidenceScore', 0))
                
                results.append({
                    "scientific_name": scientific_name,
                    "common_names": common_names,
                    "genus": genus,
                    "family": family,
                    "score": round(score * 100, 2)
                })
                
            # Récupération du quota restant
            quota = json_result.get('remainingIdentificationRequests', 'Inconnu')
            
            return {"results": results, "quota": quota}
        else:
            return {"error": f"Erreur API: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": str(e)}

def identify_disease(image_bytes):
    """Nouvelle fonction pour interroger l'endpoint des maladies."""
    if not API_KEY or API_KEY == "votre_cle_api_ici":
        return {"error": "Clé API Pl@ntNet non configurée."}

    files = [('images', ('image.jpg', image_bytes))]
    
    try:
        response = requests.post(API_DISEASE_URL, files=files)
        
        if response.status_code == 200:
            json_result = response.json()
            results = []
            
            for result in json_result.get('results', [])[:5]:
                # L'API des maladies utilise souvent la clé 'disease' au lieu de 'species'
                disease_info = result.get('disease', result.get('species', {}))
                score = result.get('score', result.get('confidenceScore', 0))
                
                results.append({
                    "scientific_name": disease_info.get('scientificNameWithoutAuthor', disease_info.get('scientificName', '')),
                    "common_names": disease_info.get('commonNames', []),
                    "genus": disease_info.get('genus', ''),
                    "family": disease_info.get('family', ''),
                    "score": round(score * 100, 2)
                })
                
            quota = json_result.get('remainingIdentificationRequests', 'Inconnu')
            return {"results": results, "quota": quota}
        else:
            return {"error": f"Erreur API: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": str(e)}