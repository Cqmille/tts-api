# 🎙️ Échantillons de Voix

Placez vos fichiers audio de référence ici pour utiliser l'API avec des voix prédéfinies.

## 📋 Fichiers Attendus

Pour que l'API fonctionne avec les voix configurées, ajoutez :

- `bob.wav` - Voix "bob"
- `pascal.wav` - Voix "pascal"

## ✅ Format Recommandé

- **Format** : WAV (16-bit PCM recommandé)
- **Durée** : 15-30 secondes
- **Qualité** : Audio clair, sans bruit de fond
- **Contenu** : Parole naturelle et variée

## 💡 Conseils

### Pour un Meilleur Clonage
1. **Audio de qualité** : Utilisez un bon microphone
2. **Variation tonale** : Parlez avec des intonations naturelles
3. **Pas de silence** : Évitez les longs silences
4. **Pas de bruit** : Enregistrez dans un environnement calme

### Exemples de Texte à Lire
```
Bonjour, je m'appelle [Nom].
J'aime parler de différents sujets avec passion et enthousiasme.
Parfois, je parle calmement... et d'autres fois, avec beaucoup d'énergie !
Est-ce que vous m'entendez bien ? Parfait !
```

## 🔧 Ajouter une Nouvelle Voix

Pour ajouter une nouvelle voix "marie" :

1. Ajoutez `marie.wav` dans ce dossier
2. Modifiez `config/settings.py` :
```python
VOICE_SAMPLES = {
    "bob": str(VOICES_DIR / "bob.wav"),
    "pascal": str(VOICES_DIR / "pascal.wav"),
    "marie": str(VOICES_DIR / "marie.wav")  # Nouvelle voix
}
```

3. Utilisez-la dans l'API :
```bash
curl -X POST http://localhost:5002/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour", "speaker": "marie"}'
```

## ⚠️ Note Importante

Les fichiers audio dans ce dossier sont **ignorés par Git** (voir `.gitignore`). Cela signifie qu'ils ne seront pas versionnés et restent locaux à votre machine.
