import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("PLANTNET_API_KEY")
API_ENDPOINT = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"

def identify_plant(image_bytes):
    if not API_KEY or API_KEY == "votre_cle_api_ici":
        return {"error": "Clé API Pl@ntNet non configurée."}

    files = [
        ('images', ('image.jpg', image_bytes))
    ]
    
    try:
        req = requests.Request('POST', url=API_ENDPOINT, files=files)
        prepared = req.prepare()
        s = requests.Session()
        response = s.send(prepared)
        
        if response.status_code == 200:
            json_result = response.json()
            results = []
            for result in json_result.get('results', [])[:5]: # Top 5
                species = result.get('species', {})
                scientific_name = species.get('scientificNameWithoutAuthor', '')
                common_names = species.get('commonNames', [])
                
                common_name = common_names[0] if common_names else "Inconnu"
                score = result.get('score', 0)
                
                results.append({
                    "scientific_name": scientific_name,
                    "common_name": common_name,
                    "score": round(score * 100, 2)
                })
            return {"results": results}
        else:
            return {"error": f"Erreur API: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": str(e)}
