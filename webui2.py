import gradio as gr
import torch
from TTS.api import TTS
import os
import re
from datetime import datetime

# Vérifier si CUDA est disponible
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Utilisation du device: {device}")

# Initialiser le modèle XTTS v2 sur GPU
print("Chargement du modèle XTTS v2...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

def sanitize_filename(text, max_length=50):
    """Crée un nom de fichier valide à partir du texte"""
    # Prendre les premiers mots du texte
    text = text.strip().split('\n')[0]  # Première ligne uniquement
    text = text[:max_length]  # Limiter la longueur
    
    # Remplacer les caractères interdits
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    text = re.sub(r'\s+', '_', text)  # Espaces -> underscores
    text = text.strip('._')  # Enlever les points/underscores au début/fin
    
    return text if text else "output"

def generate_speech(text, speaker_wav, language, temperature, speed, output_dir):
    """Génère la voix clonée avec paramètres avancés"""
    try:
        # Utiliser le répertoire par défaut si vide
        if not output_dir or output_dir.strip() == "":
            output_dir = "C:/tts/outputs"
        
        # Créer le nom de fichier basé sur le texte
        base_name = sanitize_filename(text)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}.wav"
        output_path = os.path.join(output_dir, filename)
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        
        # Configuration avancée
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language=language,
            file_path=output_path,
            temperature=temperature,
            speed=speed
        )
        return output_path, f"✅ Génération réussie !\n📁 Fichier: {filename}\n📂 Dossier: {output_dir}"
    except Exception as e:
        return None, f"❌ Erreur: {str(e)}"

# Interface Gradio améliorée
with gr.Blocks(title="TTS Voice Cloning Pro", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎤 Clonage de Voix XTTS v2 - Version Pro")
    gr.Markdown("**Contrôlez l'expressivité, le rythme et la qualité de votre voix clonée !**")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📝 Paramètres de base")
            text_input = gr.Textbox(
                label="Texte à synthétiser",
                placeholder="Bonsoir... c'est Pascal PRAUD, en direct.\n\nVous aussi, vous avez déjà eu des HÉMORROÏDES ?",
                lines=8,
                value="Bonsoir... c'est Pascal PRAUD, en direct."
            )
            audio_input = gr.Audio(
                label="🎙️ Échantillon vocal (15-30 sec recommandé)",
                type="filepath"
            )
            language_input = gr.Dropdown(
                choices=["fr", "en", "es", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"],
                value="fr",
                label="🌍 Langue"
            )
            
            output_dir_input = gr.Textbox(
                label="📂 Dossier de sortie",
                placeholder="C:/tts/outputs",
                value="C:/tts/outputs",
                info="Laissez vide pour utiliser le dossier par défaut"
            )
            
            gr.Markdown("### 🎚️ Paramètres avancés")
            
            temperature = gr.Slider(
                minimum=0.1,
                maximum=1.0,
                value=0.75,
                step=0.05,
                label="🔥 Temperature (expressivité)",
                info="Plus haut = plus varié et expressif, plus bas = plus stable"
            )
            
            speed = gr.Slider(
                minimum=0.5,
                maximum=2.0,
                value=1.0,
                step=0.1,
                label="⚡ Vitesse",
                info="0.5 = lent, 1.0 = normal, 2.0 = rapide"
            )
            
            generate_btn = gr.Button("🎵 Générer la Voix", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            gr.Markdown("### 🔊 Résultat")
            status_output = gr.Textbox(label="Statut", interactive=False)
            audio_output = gr.Audio(label="Audio généré")
            
            gr.Markdown("### 💡 Conseils pour un meilleur rendu")
            gr.Markdown("""
            **Pour l'échantillon vocal :**
            - ✅ 15-30 secondes suffisent
            - ✅ Parlez avec variation et naturel
            - ✅ Audio clair, sans bruit
            - ✅ Format WAV si possible
            
            **Pour le texte :**
            - ✅ Utilisez `...` pour les pauses
            - ✅ Sautez des lignes entre phrases
            - ✅ MAJUSCULES pour emphases
            - ✅ Points d'exclamation !
            
            **Paramètres recommandés :**
            - 🎭 **Style dramatique** : Temperature 0.85, Speed 0.9
            - 🎙️ **Style podcast** : Temperature 0.75, Speed 1.0
            - 📢 **Style pub** : Temperature 0.65, Speed 1.1
            
            **Exemples de chemins :**
            - `C:/tts/outputs`
            - `D:/mes_audios`
            - `C:/Users/camil/Desktop/voix`
            """)
    
    generate_btn.click(
        fn=generate_speech,
        inputs=[text_input, audio_input, language_input, temperature, speed, output_dir_input],
        outputs=[audio_output, status_output]
    )

print("🚀 Lancement de l'interface avancée...")
demo.launch(share=False, server_port=7860)