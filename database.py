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
            categorie TEXT,
            famille TEXT,
            genre TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plant_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER,
            image_blob BLOB,
            date_photo TEXT,
            FOREIGN KEY(plant_id) REFERENCES plants(id) ON DELETE CASCADE
        )
    ''')
    
    # Migrations des bases existantes (ajouts silencieux des nouvelles colonnes)
    try:
        cursor.execute("ALTER TABLE plants ADD COLUMN categorie TEXT DEFAULT 'Autre'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE plants ADD COLUMN famille TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE plants ADD COLUMN genre TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
        
    # Migration des anciennes images
    try:
        cursor.execute("SELECT id, image_blob, date_plantation FROM plants WHERE image_blob IS NOT NULL")
        old_images = cursor.fetchall()
        for p_id, img_blob, date_plantation in old_images:
            cursor.execute("INSERT INTO plant_photos (plant_id, image_blob, date_photo) VALUES (?, ?, ?)", (p_id, img_blob, date_plantation))
        cursor.execute("UPDATE plants SET image_blob = NULL")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def _resize_image(image_bytes, max_size=(800, 800)):
    image = Image.open(io.BytesIO(image_bytes))
    image.thumbnail(max_size)
    output = io.BytesIO()
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(output, format='JPEG', quality=85)
    return output.getvalue()

def save_plant(nom_commun, nom_scientifique, date_plantation, image_bytes, notes, famille="", genre=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO plants (nom_commun, nom_scientifique, date_plantation, image_blob, notes, categorie, famille, genre)
        VALUES (?, ?, ?, NULL, ?, 'Autre', ?, ?)
    ''', (nom_commun, nom_scientifique, date_plantation, notes, famille, genre))
    
    plant_id = cursor.lastrowid
    
    if image_bytes:
        resized_image = _resize_image(image_bytes)
        cursor.execute('''
            INSERT INTO plant_photos (plant_id, image_blob, date_photo)
            VALUES (?, ?, ?)
        ''', (plant_id, resized_image, date_plantation))
    
    conn.commit()
    conn.close()

def add_plant_photo(plant_id, image_bytes, date_photo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    resized_image = _resize_image(image_bytes)
    cursor.execute('''
        INSERT INTO plant_photos (plant_id, image_blob, date_photo)
        VALUES (?, ?, ?)
    ''', (plant_id, resized_image, date_photo))
    conn.commit()
    conn.close()

def get_all_plants():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Récupération incluant la famille et le genre
    cursor.execute('SELECT id, nom_commun, nom_scientifique, date_plantation, notes, categorie, famille, genre FROM plants')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for p in rows:
        result.append({
            'id': p[0],
            'nom_commun': p[1],
            'nom_scientifique': p[2],
            'date_plantation': p[3],
            'notes': p[4],
            'categorie': p[5] if len(p) > 5 else "Autre",
            'famille': p[6] if len(p) > 6 else "",
            'genre': p[7] if len(p) > 7 else ""
        })
    return result

def get_plant_photos(plant_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, image_blob, date_photo FROM plant_photos WHERE plant_id = ? ORDER BY date_photo DESC, id DESC', (plant_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'blob': r[1], 'date': r[2]} for r in rows]

def delete_plant(plant_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM plant_photos WHERE plant_id = ?', (plant_id,))
    cursor.execute('DELETE FROM plants WHERE id = ?', (plant_id,))
    conn.commit()
    conn.close()