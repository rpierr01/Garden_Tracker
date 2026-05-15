import sqlite3
import io
from PIL import Image

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_commun TEXT,
            nom_scientifique TEXT,
            date_plantation TEXT,
            image_blob BLOB,
            notes TEXT,
            categorie TEXT
        )
    ''')
    
    # Ajout de la colonne categorie pour les bases de données existantes
    try:
        cursor.execute("ALTER TABLE plants ADD COLUMN categorie TEXT DEFAULT 'Autre'")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def _resize_image(image_bytes, max_size=(800, 800)):
    image = Image.open(io.BytesIO(image_bytes))
    image.thumbnail(max_size)
    output = io.BytesIO()
    # Sauvegarde en JPEG (ou selon le format d'origine, on force JPEG pour compresser)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(output, format='JPEG', quality=85)
    return output.getvalue()

def save_plant(nom_commun, nom_scientifique, date_plantation, image_bytes, notes, categorie="Autre"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Redimensionnement de l'image
    resized_image = _resize_image(image_bytes)
    
    cursor.execute('''
        INSERT INTO plants (nom_commun, nom_scientifique, date_plantation, image_blob, notes, categorie)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nom_commun, nom_scientifique, date_plantation, resized_image, notes, categorie))
    
    conn.commit()
    conn.close()

def get_all_plants():
    # Ne récupère pas l'image pour éviter de surcharger la mémoire
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, nom_commun, nom_scientifique, date_plantation, notes, categorie FROM plants ORDER BY id DESC')
    plants = cursor.fetchall()
    conn.close()
    
    result = []
    for p in plants:
        result.append({
            'id': p[0],
            'nom_commun': p[1],
            'nom_scientifique': p[2],
            'date_plantation': p[3],
            'notes': p[4],
            'categorie': p[5] if len(p) > 5 else "Autre"
        })
    return result

def get_plant_image(plant_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT image_blob FROM plants WHERE id = ?', (plant_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0]:
        return row[0]
    return None

def delete_plant(plant_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM plants WHERE id = ?', (plant_id,))
    conn.commit()
    conn.close()
