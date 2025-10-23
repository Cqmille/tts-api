# 🎤 TTS API - Clonage de Voix avec XTTS v2

API REST et interfaces web Gradio pour le clonage de voix en temps réel, basées sur le modèle XTTS v2 de Coqui TTS.

## ✨ Fonctionnalités

### 🔌 API REST (Flask)
- Endpoint `/api/tts` pour générer de l'audio à partir de texte
- Support multi-voix (bob, pascal)
- Compatible avec Unity et autres clients HTTP
- Health check endpoint `/health`

### 🎨 Interface Web Ultra Pro (Gradio)

**Architecture Modulaire & Professionnelle**
- 🎙️ **Génération de samples TTS** avec contrôle précis
- 🎭 **Support de 4 voix simultanément** avec mémorisation des paramètres
- 🔥 **Génération en rafale** (plusieurs samples d'un coup)
- 📊 **Système de logs en temps réel** pour suivre toutes les opérations
- 🗑️ **Suppression individuelle** avec réordonnancement automatique
- 🔊 **Jusqu'à 20 samples** par session (extensible)
- 💾 **Export ZIP** pour montage vidéo
- 🎚️ **Mémorisation température/vitesse** par voix
- 📝 **Interface compacte** avec hauteur réduite des lecteurs

## 📋 Prérequis

- **Windows** 10/11
- **Python** 3.10 ou supérieur
- **GPU NVIDIA** (optionnel, mais recommandé pour de meilleures performances)
- **Connexion Internet** (pour l'installation)

## 🚀 Installation Rapide

### Étape 1 : Télécharger le projet

```bash
git clone <url-du-repo>
cd tts-api
```

Ou téléchargez et décompressez le ZIP du projet.

### Étape 2 : Installer automatiquement

Double-cliquez sur :
```
setup.bat
```

Le script va :
1. ✅ Vérifier Python
2. ✅ Créer un environnement virtuel
3. ✅ Installer toutes les dépendances
4. ✅ Vérifier l'installation

**Durée estimée : 5-10 minutes** (selon votre connexion)

### Étape 3 : Configurer les échantillons de voix (pour l'API)

Placez vos fichiers audio dans `data/voices/` :
```
data/voices/
├── bob.wav      (voix "bob")
└── pascal.wav   (voix "pascal")
```

**Format recommandé :**
- Format : WAV
- Durée : 15-30 secondes
- Qualité : Audio clair, sans bruit de fond
- Contenu : Parole naturelle et variée

## 🎯 Utilisation

### Lancer l'API

Double-cliquez sur :
```
scripts\launch_api.bat
```

L'API sera disponible sur : `http://localhost:5002`

**Exemple d'utilisation (curl) :**
```bash
curl -X POST http://localhost:5002/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour, ceci est un test", "speaker": "bob"}' \
  --output audio.wav
```

**Exemple d'utilisation (Python) :**
```python
import requests

response = requests.post('http://localhost:5002/api/tts', json={
    'text': 'Bonjour, ceci est un test',
    'speaker': 'bob'
})

with open('audio.wav', 'wb') as f:
    f.write(response.content)
```

### Lancer l'Interface Web Ultra Pro

**Windows :**
Double-cliquez sur :
```
start_ultra_pro.bat
```
Ou depuis le dossier scripts :
```
scripts\launch_ui.bat
```

**Linux/Mac :**
```bash
./start_ultra_pro.sh
```

L'interface sera disponible sur : `http://localhost:7860`

**Fonctionnalités clés :**
- Génération de samples individuels ou en rafale
- Gestion dynamique jusqu'à 20 samples
- Suppression individuelle avec boutons dédiés
- Logs en temps réel des opérations
- Export ZIP de tous les samples

## 📁 Structure du Projet

```
tts-api/
├── 📁 src/                      Code source
│   ├── webui_ultra_pro.py      Interface Ultra Pro (principale)
│   ├── tts_api.py              API Flask
│   └── 📁 modules/              Modules refactorisés
│       ├── audio_manager.py    Gestion TTS et audio
│       ├── sample_manager.py   Gestion des samples
│       ├── ui_components.py    Composants UI
│       └── utils.py            Fonctions utilitaires
│
├── 📁 config/                   Configuration
│   └── settings.py             Paramètres centralisés
│
├── 📁 data/                     Données
│   ├── voices/                 Échantillons de voix
│   ├── outputs/                Fichiers générés
│   └── temp/                   Fichiers temporaires
│       └── dialogue/           Samples en cours
│
├── 📁 scripts/                  Scripts de lancement
│   ├── launch_api.bat          Lancer l'API
│   └── launch_ui.bat           Lancer l'interface
│
├── start_ultra_pro.sh          Script Linux/Mac
├── setup.bat                   Installation automatique
├── requirements.txt            Dépendances Python
└── README.md                   Ce fichier
```

## ⚙️ Configuration

Le fichier `config/settings.py` contient tous les paramètres :

```python
# Ports
API_PORT = 5002
GRADIO_PORT = 7860

# Chemins des dossiers
DATA_DIR = PROJECT_ROOT / "data"
VOICES_DIR = DATA_DIR / "voices"
OUTPUTS_DIR = DATA_DIR / "outputs"

# Configuration TTS
TTS_CONFIG = {
    "model": "tts_models/multilingual/multi-dataset/xtts_v2",
    "default_language": "fr",
    "default_temperature": 0.75,
    "default_speed": 1.0
}

# Langues supportées (16)
SUPPORTED_LANGUAGES = [
    "fr", "en", "es", "de", "it", "pt", "pl", "tr",
    "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"
]
```

## 💡 Conseils pour de Meilleurs Résultats

### Pour les Échantillons Vocaux
- ✅ **Durée** : 15-30 secondes suffisent
- ✅ **Qualité** : Audio clair, sans bruit
- ✅ **Variation** : Parlez naturellement avec des intonations
- ✅ **Format** : WAV recommandé

### Pour la Génération de Texte
- ✅ Utilisez `...` pour les pauses naturelles
- ✅ Sautez des lignes entre phrases importantes
- ✅ MAJUSCULES pour les emphases
- ✅ Points d'exclamation pour l'enthousiasme !

### Paramètres Recommandés

**Style Dramatique**
- Temperature : 0.85
- Speed : 0.9

**Style Podcast**
- Temperature : 0.75
- Speed : 1.0

**Style Publicité**
- Temperature : 0.65
- Speed : 1.1

## 🔧 Dépannage

### Python n'est pas reconnu
1. Téléchargez Python depuis https://www.python.org/downloads/
2. **IMPORTANT** : Cochez "Add Python to PATH" lors de l'installation
3. Redémarrez votre ordinateur
4. Relancez `setup.bat`

### Erreur "CUDA not available"
- **C'est normal** si vous n'avez pas de GPU NVIDIA
- Le programme fonctionnera sur CPU (plus lent mais fonctionnel)

### L'installation des dépendances échoue
1. Vérifiez votre connexion Internet
2. Relancez `setup.bat`
3. Si le problème persiste, installez manuellement :
   ```bash
   cd tts-api
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### L'API ne trouve pas les voix
- Vérifiez que vos fichiers sont bien dans `data/voices/`
- Vérifiez les noms : `bob.wav` et `pascal.wav`
- Format supporté : WAV