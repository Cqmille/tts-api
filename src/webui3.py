import gradio as gr
import torch
from TTS.api import TTS
import os
import re
import sys
from datetime import datetime
import zipfile
import shutil

# Ajouter le dossier parent au path pour importer config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import *

# Vérifier si CUDA est disponible
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Utilisation du device: {device}")

# Initialiser le modèle XTTS v2 sur GPU
print("Chargement du modèle XTTS v2...")
tts = TTS(TTS_CONFIG["model"]).to(device)

# Stockage global des parties du dialogue
dialogue_parts = []
temp_audio_dir = str(TEMP_DIALOGUE_DIR)

def sanitize_filename(text, max_length=50):
    """Crée un nom de fichier valide à partir du texte"""
    text = text.strip().split('\n')[0]
    text = text[:max_length]
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    text = re.sub(r'\s+', '_', text)
    text = text.strip('._')
    return text if text else "output"

def get_voice_name(speaker_wav_path):
    """Extrait un nom de voix depuis le chemin du fichier"""
    if not speaker_wav_path:
        return "Voix_Inconnue"
    return os.path.splitext(os.path.basename(speaker_wav_path))[0]

def add_dialogue_part(text, voice_sample, voice_name, language, temperature, speed):
    """Ajoute une partie au dialogue"""
    global dialogue_parts
    
    try:
        if not text or not text.strip():
            return "❌ Le texte ne peut pas être vide", None, build_dialogue_display()
        
        if not voice_sample:
            return "❌ Veuillez sélectionner un échantillon vocal", None, build_dialogue_display()
        
        # Générer le nom de fichier
        part_number = len(dialogue_parts) + 1
        base_name = sanitize_filename(text, max_length=30)
        safe_voice_name = sanitize_filename(voice_name if voice_name else get_voice_name(voice_sample))
        filename = f"part_{part_number:03d}_{safe_voice_name}_{base_name}.wav"
        output_path = os.path.join(temp_audio_dir, filename)
        
        # Générer l'audio
        tts.tts_to_file(
            text=text,
            speaker_wav=voice_sample,
            language=language,
            file_path=output_path,
            temperature=temperature,
            speed=speed
        )
        
        # Ajouter aux parties
        dialogue_parts.append({
            "number": part_number,
            "text": text,
            "voice_name": safe_voice_name,
            "audio_path": output_path,
            "filename": filename
        })
        
        status = f"✅ Partie {part_number} ajoutée avec succès !\n🎙️ Voix: {safe_voice_name}\n📝 Texte: {text[:50]}..."
        return status, output_path, build_dialogue_display()
        
    except Exception as e:
        return f"❌ Erreur: {str(e)}", None, build_dialogue_display()

def build_dialogue_display():
    """Construit l'affichage HTML du dialogue"""
    if not dialogue_parts:
        return "<div style='padding: 20px; text-align: center; color: #666;'>Aucune partie ajoutée pour le moment</div>"
    
    html = "<div style='font-family: Arial, sans-serif;'>"
    for part in dialogue_parts:
        html += f"""
        <div style='margin: 15px 0; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                <span style='font-weight: bold; color: white; font-size: 16px;'>
                    🎬 Partie {part['number']} - 🎙️ {part['voice_name']}
                </span>
                <span style='background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 15px; 
                            color: white; font-size: 12px;'>
                    {part['filename']}
                </span>
            </div>
            <div style='background: rgba(255,255,255,0.95); padding: 12px; border-radius: 8px; 
                        color: #333; font-size: 14px; line-height: 1.6;'>
                "{part['text']}"
            </div>
        </div>
        """
    html += "</div>"
    return html

def get_audio_players():
    """Retourne la liste des chemins audio pour les players"""
    return [part["audio_path"] for part in dialogue_parts] if dialogue_parts else []

def clear_dialogue():
    """Efface tout le dialogue"""
    global dialogue_parts
    dialogue_parts = []
    
    # Nettoyer les fichiers temporaires
    if os.path.exists(temp_audio_dir):
        for file in os.listdir(temp_audio_dir):
            try:
                os.remove(os.path.join(temp_audio_dir, file))
            except:
                pass
    
    return "🗑️ Dialogue effacé", build_dialogue_display(), *[None]*10

def export_dialogue(output_dir):
    """Exporte tout le dialogue en ZIP"""
    global dialogue_parts

    try:
        if not dialogue_parts:
            return "❌ Aucune partie à exporter", None

        if not output_dir or output_dir.strip() == "":
            output_dir = str(OUTPUTS_DIR)

        os.makedirs(output_dir, exist_ok=True)

        # Créer le nom du ZIP
        timestamp = datetime.now().strftime(FILE_CONFIG["timestamp_format"])
        zip_filename = f"dialogue_{timestamp}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        # Créer le ZIP
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for part in dialogue_parts:
                zipf.write(part["audio_path"], part["filename"])
        
        status = f"✅ Export réussi !\n📦 {len(dialogue_parts)} fichiers exportés\n📁 Fichier: {zip_filename}\n📂 Dossier: {output_dir}"
        return status, zip_path
        
    except Exception as e:
        return f"❌ Erreur lors de l'export: {str(e)}", None

def remove_last_part():
    """Supprime la dernière partie ajoutée"""
    global dialogue_parts
    
    if not dialogue_parts:
        return "❌ Aucune partie à supprimer", build_dialogue_display(), *[None]*10
    
    removed = dialogue_parts.pop()
    try:
        if os.path.exists(removed["audio_path"]):
            os.remove(removed["audio_path"])
    except:
        pass
    
    audio_list = get_audio_players() + [None] * (10 - len(dialogue_parts))
    return f"🗑️ Partie {removed['number']} supprimée", build_dialogue_display(), *audio_list[:10]

# Interface Gradio Ultra Pro
with gr.Blocks(title="TTS Dialogue Studio Ultra Pro", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎬 TTS Dialogue Studio - Version Ultra Pro")
    gr.Markdown("**Créez des dialogues multi-voix avec prévisualisation en temps réel !**")
    
    with gr.Row():
        # Colonne de gauche - Création
        with gr.Column(scale=1):
            gr.Markdown("## 🎙️ Nouvelle Partie")
            
            with gr.Accordion("📂 Échantillons Vocaux", open=True):
                gr.Markdown("*Uploadez vos différents échantillons vocaux (un par personnage)*")
                voice_sample_1 = gr.Audio(label="🎤 Voix 1", type="filepath")
                voice_sample_2 = gr.Audio(label="🎤 Voix 2", type="filepath")
                voice_sample_3 = gr.Audio(label="🎤 Voix 3", type="filepath")
                voice_sample_4 = gr.Audio(label="🎤 Voix 4", type="filepath")
            
            gr.Markdown("### ✍️ Contenu de la partie")
            
            voice_selector = gr.Radio(
                choices=["Voix 1", "Voix 2", "Voix 3", "Voix 4"],
                value="Voix 1",
                label="🎭 Voix à utiliser pour cette partie"
            )
            
            voice_name_input = gr.Textbox(
                label="🏷️ Nom de la voix (optionnel)",
                placeholder="Ex: Pascal, Marie, Narrateur...",
                info="Laissez vide pour utiliser le nom du fichier"
            )
            
            text_input = gr.Textbox(
                label="📝 Texte de cette partie",
                placeholder="Entrez le texte pour cette partie du dialogue...",
                lines=4
            )
            
            with gr.Row():
                language_input = gr.Dropdown(
                    choices=SUPPORTED_LANGUAGES,
                    value=TTS_CONFIG["default_language"],
                    label="🌍 Langue",
                    scale=1
                )
                temperature = gr.Slider(
                    minimum=0.1, maximum=1.0, value=TTS_CONFIG["default_temperature"], step=0.05,
                    label="🔥 Temperature", scale=1
                )
                speed = gr.Slider(
                    minimum=0.5, maximum=2.0, value=TTS_CONFIG["default_speed"], step=0.1,
                    label="⚡ Vitesse", scale=1
                )
            
            with gr.Row():
                add_btn = gr.Button("➕ Ajouter cette partie", variant="primary", size="lg", scale=2)
                remove_btn = gr.Button("🗑️ Supprimer dernière", variant="secondary", size="lg", scale=1)
            
            status_add = gr.Textbox(label="Statut", interactive=False, lines=3)
            preview_audio = gr.Audio(label="🎧 Prévisualisation de la dernière partie ajoutée")
        
        # Colonne de droite - Visualisation et Export
        with gr.Column(scale=1):
            gr.Markdown("## 🎬 Dialogue Complet")
            
            dialogue_display = gr.HTML(
                value=build_dialogue_display(),
                label="Parties du dialogue"
            )
            
            gr.Markdown("### 🔊 Lecteurs Audio (Parties 1-10)")
            gr.Markdown("*Cliquez sur Play pour écouter chaque partie individuellement*")
            
            audio_players = []
            for i in range(10):
                audio_players.append(gr.Audio(label=f"Partie {i+1}", interactive=False))
            
            gr.Markdown("### 📦 Export")
            
            output_dir_input = gr.Textbox(
                label="📂 Dossier de sortie",
                value=str(OUTPUTS_DIR),
                placeholder=str(OUTPUTS_DIR)
            )
            
            with gr.Row():
                export_btn = gr.Button("💾 Télécharger tout en ZIP", variant="primary", size="lg", scale=2)
                clear_btn = gr.Button("🗑️ Tout effacer", variant="stop", size="lg", scale=1)
            
            status_export = gr.Textbox(label="Statut Export", interactive=False, lines=3)
            download_file = gr.File(label="📥 Fichier ZIP à télécharger")
            
            gr.Markdown("""
            ### 💡 Guide d'utilisation
            
            **Workflow :**
            1. 📤 Uploadez vos échantillons vocaux (jusqu'à 4 voix différentes)
            2. 🎭 Sélectionnez la voix pour la partie actuelle
            3. ✍️ Écrivez le texte de cette partie
            4. ➕ Cliquez sur "Ajouter cette partie"
            5. 🔊 Écoutez la partie générée dans les lecteurs
            6. 🔁 Répétez pour chaque partie du dialogue
            7. 💾 Téléchargez tout en ZIP quand c'est prêt !
            
            **Astuces :**
            - Utilisez `...` pour les pauses naturelles
            - MAJUSCULES pour les emphases
            - Nommez vos voix pour mieux vous y retrouver
            - Les fichiers sont numérotés automatiquement pour le montage
            """)
    
    # Logique des boutons
    def add_part_logic(text, voice_sel, voice_name, lang, temp, spd, v1, v2, v3, v4):
        voice_map = {"Voix 1": v1, "Voix 2": v2, "Voix 3": v3, "Voix 4": v4}
        selected_voice = voice_map.get(voice_sel)
        
        status, preview, display = add_dialogue_part(text, selected_voice, voice_name, lang, temp, spd)
        audio_list = get_audio_players() + [None] * (10 - len(dialogue_parts))
        return status, preview, display, *audio_list[:10]
    
    add_btn.click(
        fn=add_part_logic,
        inputs=[text_input, voice_selector, voice_name_input, language_input, temperature, speed,
                voice_sample_1, voice_sample_2, voice_sample_3, voice_sample_4],
        outputs=[status_add, preview_audio, dialogue_display] + audio_players
    )
    
    remove_btn.click(
        fn=remove_last_part,
        outputs=[status_add, dialogue_display] + audio_players
    )
    
    export_btn.click(
        fn=export_dialogue,
        inputs=[output_dir_input],
        outputs=[status_export, download_file]
    )
    
    clear_btn.click(
        fn=clear_dialogue,
        outputs=[status_export, dialogue_display] + audio_players
    )

print("🚀 Lancement du Dialogue Studio Ultra Pro...")
demo.launch(**GRADIO_CONFIG)