# Fish Speech API Documentation

**Base URL:** `http://localhost:7870`  
**Version:** 1.5.0

---

## Endpoints

### 1. Génération TTS

#### `POST /v1/tts`
Génère de l'audio à partir de texte.

**Request Body:**
```json
{
  "text": "Bonjour, ceci est un test.",
  "reference_id": "ma_voix",
  "chunk_length": 200,
  "format": "wav",
  "temperature": 0.8,
  "top_p": 0.8,
  "repetition_penalty": 1.1,
  "max_new_tokens": 1024,
  "normalize": true,
  "streaming": false,
  "seed": null
}
```

**Paramètres:**
| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `text` | string | *requis* | Texte à synthétiser |
| `reference_id` | string | null | ID de la voix de référence |
| `temperature` | float | 0.8 | Créativité (0.1-1.0). Plus bas = plus stable |
| `top_p` | float | 0.8 | Nucleus sampling |
| `repetition_penalty` | float | 1.1 | Pénalité de répétition |
| `max_new_tokens` | int | 1024 | Limite de tokens générés |
| `chunk_length` | int | 200 | Longueur des chunks de texte |
| `format` | string | "wav" | Format de sortie |
| `normalize` | bool | true | Normaliser l'audio |
| `streaming` | bool | false | Mode streaming |
| `seed` | int | null | Seed pour reproductibilité |

**Réponse:** Fichier audio (WAV)

**Exemple curl:**
```bash
curl -X POST http://localhost:7870/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour !", "reference_id": "ma_voix"}' \
  --output output.wav
```

---

### 2. Gestion des Voix de Référence

#### `POST /v1/references/add`
Ajoute une nouvelle voix de référence.

**Request Body:** (multipart/form-data)
| Champ | Type | Description |
|-------|------|-------------|
| `id` | string | Identifiant unique de la voix |
| `audio` | file | Fichier audio WAV (10-30 secondes) |
| `text` | string | Transcription exacte de l'audio |

**Exemple curl:**
```bash
curl -X POST http://localhost:7870/v1/references/add \
  -F "id=pascal" \
  -F "audio=@sample.wav" \
  -F "text=Bonjour, ceci est le texte exact prononcé dans l'audio."
```

---

#### `GET /v1/references/list`
Liste toutes les voix de référence disponibles.

**Exemple curl:**
```bash
curl http://localhost:7870/v1/references/list
```

**Réponse:**
```json
["pascal", "bob", "marie"]
```

---

#### `DELETE /v1/references/delete`
Supprime une voix de référence.

**Request Body:**
```json
{
  "reference_id": "pascal"
}
```

**Exemple curl:**
```bash
curl -X DELETE http://localhost:7870/v1/references/delete \
  -H "Content-Type: application/json" \
  -d '{"reference_id": "pascal"}'
```

---

#### `POST /v1/references/update`
Renomme une voix de référence.

**Request Body:**
```json
{
  "old_reference_id": "ancien_nom",
  "new_reference_id": "nouveau_nom"
}
```

---

### 3. VQGAN (Avancé)

#### `POST /v1/vqgan/encode`
Encode un audio en tokens VQGAN.

**Request Body:**
```json
{
  "audios": ["base64_encoded_audio"]
}
```

#### `POST /v1/vqgan/decode`
Décode des tokens VQGAN en audio.

**Request Body:**
```json
{
  "tokens": [[[0, 1, 2, ...]]]
}
```

---

## Contrôle des Émotions

Ajoutez des marqueurs dans le texte pour contrôler l'émotion :

**Émotions de base:**
```
(angry) (sad) (excited) (surprised) (satisfied) (delighted) 
(scared) (worried) (upset) (nervous) (frustrated) (depressed)
(empathetic) (embarrassed) (disgusted) (moved) (proud) (relaxed)
(grateful) (confident) (interested) (curious) (confused) (joyful)
```

**Émotions avancées:**
```
(disdainful) (unhappy) (anxious) (hysterical) (indifferent) 
(impatient) (guilty) (scornful) (panicked) (furious) (reluctant)
(keen) (disapproving) (negative) (denying) (astonished) (serious)
(sarcastic) (conciliative) (comforting) (sincere) (sneering)
(hesitating) (yielding) (painful) (awkward) (amused)
```

**Marqueurs de ton:**
```
(in a hurry tone) (shouting) (screaming) (whispering) (soft tone)
```

**Effets spéciaux:**
```
(laughing) (chuckling) (sobbing) (crying loudly) (sighing) (panting)
(groaning) (crowd laughing) (background laughter) (audience laughing)
```

**Exemple:**
```json
{
  "text": "(excited) Bonjour ! (whispering) Je vais te dire un secret...",
  "reference_id": "ma_voix"
}
```

---

## Conseils pour les Voix de Référence

- **Durée idéale:** 10-30 secondes
- **Format:** WAV, mono ou stéréo, 44.1kHz ou 48kHz
- **Qualité:** Audio clair, sans bruit de fond
- **Transcription:** Doit correspondre exactement à ce qui est dit
- **Contenu:** Parole naturelle avec intonations variées

---

## Paramètres Recommandés

| Style | Temperature | Top_p | Description |
|-------|-------------|-------|-------------|
| Stable | 0.5 | 0.7 | Voix cohérente, peu de variation |
| Normal | 0.8 | 0.8 | Équilibre naturel |
| Expressif | 0.9 | 0.9 | Plus de variation et d'émotion |
