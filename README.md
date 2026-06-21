# Suivi de Plantes d'Intérieur

Il s'agit d'une application de répertoire botanique qui vous permet de recenser, d'identifier et de suivre les plantes de votre intérieur. Les végétaux photographiés sont identifiés automatiquement à l'aide de l'API [Pl@ntNet](https://plantnet.org/) et sont stockés localement dans une base de données SQLite unique (images incluses), ce qui rend le projet entièrement portable.

## Fonctionnalités

- **Identification IA :** Téléchargez une photo et obtenez son nom commun et scientifique.
- **Répertoire Local :** Sauvegardez l'historique complet, les notes et les dates d'acquisition.
- **Suivi photographique :** Ajoutez plusieurs photos pour une même plante afin de suivre son évolution dans le temps.
- **Portabilité :** Toutes les données et images (BLOB) sont centralisées dans un seul fichier SQLite.
- **Galerie :** Visualisez les espèces de votre intérieur directement depuis une interface web conviviale propulsée par Streamlit.

## Prérequis

- **Python 3.7+**
- Une clé **API Pl@ntNet**. Vous pouvez l'obtenir en créant un compte sur [my.plantnet.org](https://my.plantnet.org/).

## Installation

1. **Cloner ou télécharger le dépôt** de l'application dans votre système.
2. **Créer un environnement virtuel** (recommandé) :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Mac/Linux
   # venv\Scripts\activate   # Sur Windows
   ```
3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Créez un fichier `.env` à la racine de votre dossier et ajoutez-y votre clé d'API Pl@ntNet de cette manière :

```env
PLANTNET_API_KEY=votre_cle_api_ici
```

## Utilisation

Démarrez l'application web Streamlit avec la commande suivante :

```bash
streamlit run app.py
```

L'interface web s'ouvrira automatiquement dans votre navigateur (par défaut sur `http://localhost:8501`).

## Stack Technologique

- **Interface Utilisateur :** Streamlit
- **Base de données :** SQLite (Images stockées au format `BLOB`)
- **Backend / Logique :** Python (avec `requests` pour les appels API, `Pillow` pour le traitement d'images, `python-dotenv` pour les variables d'environnement)

## Notes de développement
Les images téléversées sont compressées via Pillow en interne ou adaptées dans le flux binaire (io.BytesIO) afin de limiter la taille du fichier base de données SQLite.
