import gradio as gr
import torch
from TTS.api import TTS

# Initialiser le modèle XTTS v2
print("Chargement du modèle XTTS v2...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

def generate_speech(text, speaker_wav, language):
    """Génère la voix clonée"""
    try:
        output_path = "C:/tts/gradio_output.wav"
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language=language,
            file_path=output_path
        )
        return output_path
    except Exception as e:
        return f"Erreur: {str(e)}"

# Interface Gradio
with gr.Blocks(title="TTS Voice Cloning") as demo:
    gr.Markdown("# 🎤 Clonage de Voix avec XTTS v2")
    gr.Markdown("Upload un échantillon vocal et génère du texte avec cette voix !")
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Texte à synthétiser",
                placeholder="Entrez votre texte ici...",
                lines=5
            )
            audio_input = gr.Audio(
                label="Échantillon vocal (votre voix)",
                type="filepath"
            )
            language_input = gr.Dropdown(
                choices=["fr", "en", "es", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"],
                value="fr",
                label="Langue"
            )
            generate_btn = gr.Button("🎵 Générer", variant="primary")
        
        with gr.Column():
            audio_output = gr.Audio(label="Résultat")
    
    generate_btn.click(
        fn=generate_speech,
        inputs=[text_input, audio_input, language_input],
        outputs=audio_output
    )
    
    gr.Markdown("### Astuce : Pour de meilleurs résultats, utilisez un échantillon vocal clair de 6 secondes minimum.")

print("Lancement de l'interface...")
demo.launch(share=False, server_port=7860)