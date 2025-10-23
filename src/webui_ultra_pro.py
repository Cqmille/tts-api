"""TTS Ultra Pro - Interface Gradio refactorisée"""
import gradio as gr
import sys
import os

# Ajouter le dossier parent au path pour importer config et modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import *
from modules.audio_manager import AudioManager
from modules.sample_manager import SampleManager
from modules.ui_components import create_help_popup

# Initialisation
audio_manager = AudioManager()
sample_manager = SampleManager(str(TEMP_DIALOGUE_DIR))

# Variables globales pour les composants dynamiques
audio_components = []


def refresh_ui():
    """Refresh all UI components"""
    return (
        sample_manager.get_samples_html(),
        sample_manager.get_logs_html(),
        create_audio_gallery()
    )


def create_audio_gallery():
    """Create dynamic audio gallery with delete buttons"""
    if not sample_manager.samples:
        return []

    gallery = []
    for sample in sample_manager.samples:
        gallery.append({
            "audio": sample["audio_path"],
            "label": f"Sample {sample['number']} - {sample['voice_name']}",
            "index": sample["number"] - 1
        })
    return gallery


def add_sample_handler(text, voice_sel, voice_name, lang, temp, spd, v1, v2, v3, v4):
    """Handle adding a new sample"""
    voice_map = {"Voix 1": v1, "Voix 2": v2, "Voix 3": v3, "Voix 4": v4}
    selected_voice = voice_map.get(voice_sel)

    # Check if batch generation (multiple paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    if len(paragraphs) > 1:
        # Batch generation
        sample_manager.add_log(f"Génération en rafale: {len(paragraphs)} samples", "info")
        results = sample_manager.add_samples_batch(
            paragraphs, selected_voice, voice_name, lang, temp, spd, audio_manager
        )
        status = f"✅ {len(results)} samples générés en rafale !"
        preview = results[-1][0] if results else None
    else:
        # Single generation
        preview, status = sample_manager.add_sample(
            text, selected_voice, voice_name, lang, temp, spd, audio_manager
        )

    # Update audio players
    audio_outputs = []
    for sample in sample_manager.samples:
        audio_outputs.append(sample["audio_path"])

    # Pad with None for empty slots
    while len(audio_outputs) < 20:
        audio_outputs.append(None)

    return [status, preview, get_sample_display_html(), sample_manager.get_logs_html()] + audio_outputs[:20]


def delete_sample_handler(sample_index):
    """Handle sample deletion"""
    success, status = sample_manager.remove_sample(sample_index)

    # Update audio players
    audio_outputs = []
    for sample in sample_manager.samples:
        audio_outputs.append(sample["audio_path"])

    # Pad with None for empty slots
    while len(audio_outputs) < 20:
        audio_outputs.append(None)

    return [status, get_sample_display_html(), sample_manager.get_logs_html()] + audio_outputs[:20]


def clear_all_handler():
    """Clear all samples"""
    success, status = sample_manager.clear_all()

    # Clear all audio players
    audio_outputs = [None] * 20

    return [status, get_sample_display_html(), sample_manager.get_logs_html()] + audio_outputs


def export_handler(output_dir):
    """Handle export to ZIP"""
    if not output_dir or output_dir.strip() == "":
        output_dir = str(OUTPUTS_DIR)

    zip_path, status = sample_manager.export_to_zip(output_dir)
    return status, zip_path


def voice_changed_handler(voice_sel, v1, v2, v3, v4):
    """Load saved settings when voice changes"""
    voice_map = {"Voix 1": v1, "Voix 2": v2, "Voix 3": v3, "Voix 4": v4}
    selected_voice = voice_map.get(voice_sel)

    if selected_voice:
        from modules.utils import get_voice_name
        voice_name = get_voice_name(selected_voice)
        settings = sample_manager.get_voice_settings(voice_name)
        return settings["temperature"], settings["speed"]

    return TTS_CONFIG["default_temperature"], TTS_CONFIG["default_speed"]


def create_audio_gallery_components():
    """Create dynamic audio components list"""
    components = []
    for sample in sample_manager.samples:
        components.append((
            sample["audio_path"],
            f"Sample {sample['number']} - {sample['voice_name']}",
            sample["number"] - 1
        ))
    return components


def get_sample_display_html():
    """Create compact HTML display for samples"""
    if not sample_manager.samples:
        return "<div style='padding: 15px; text-align: center; color: #666; font-size: 14px;'>Aucun sample généré</div>"

    html = "<div style='display: flex; flex-direction: column; gap: 6px;'>"
    for sample in sample_manager.samples:
        html += f"""
        <div style='padding: 8px 12px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    border-radius: 6px; display: flex; justify-content: space-between; align-items: center;'>
            <div style='color: white; font-weight: bold; font-size: 13px;'>
                🎬 Sample {sample['number']}
            </div>
            <div style='color: white; font-size: 12px;'>
                🎙️ {sample['voice_name']}
            </div>
            <div style='color: rgba(255,255,255,0.9); font-size: 11px; font-style: italic;'>
                {sample['text'][:40]}{'...' if len(sample['text']) > 40 else ''}
            </div>
        </div>
        """
    html += "</div>"
    return html


# Interface Gradio
with gr.Blocks(title="TTS Ultra Pro", theme=gr.themes.Soft(), css="""
    .compact-audio audio { height: 35px !important; }
    .compact-row { margin: 4px 0 !important; padding: 6px !important; }
""") as demo:
    gr.Markdown("# 🎬 TTS Ultra Pro")
    gr.Markdown("**Interface professionnelle de génération TTS multi-voix**")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 🎙️ Génération de Sample")

            # Content input
            text_input = gr.Textbox(
                label="📝 Texte du sample",
                placeholder="Entrez votre texte ici...\n\nSéparez par des lignes vides pour générer plusieurs samples en rafale",
                lines=6
            )

            # Voice selection
            voice_selector = gr.Radio(
                choices=["Voix 1", "Voix 2", "Voix 3", "Voix 4"],
                value="Voix 1",
                label="🎭 Voix à utiliser"
            )

            voice_name_input = gr.Textbox(
                label="🏷️ Nom de la voix (optionnel)",
                placeholder="Ex: Pascal, Marie, Narrateur...",
                info="Laissez vide pour utiliser le nom du fichier"
            )

            # Parameters
            with gr.Row():
                language_input = gr.Dropdown(
                    choices=SUPPORTED_LANGUAGES,
                    value=TTS_CONFIG["default_language"],
                    label="🌍 Langue"
                )

            with gr.Row():
                temperature = gr.Slider(
                    minimum=0.1, maximum=1.0, value=TTS_CONFIG["default_temperature"], step=0.05,
                    label="🔥 Température"
                )
                speed = gr.Slider(
                    minimum=0.5, maximum=2.0, value=TTS_CONFIG["default_speed"], step=0.1,
                    label="⚡ Vitesse"
                )

            # Buttons
            with gr.Row():
                add_btn = gr.Button("➕ Générer Sample", variant="primary", size="lg")
                help_btn = gr.Button("❓ Aide", variant="secondary", size="lg")

            status_add = gr.Textbox(label="Statut", interactive=False, lines=2)
            preview_audio = gr.Audio(label="🎧 Prévisualisation du dernier sample", elem_classes=["compact-audio"])

            # Voice samples section (moved to bottom)
            gr.Markdown("---")
            gr.Markdown("## 📂 Configuration des Voix")
            with gr.Accordion("Échantillons Vocaux", open=False):
                gr.Markdown("*Uploadez vos échantillons vocaux (un par voix)*")
                voice_sample_1 = gr.Audio(label="🎤 Voix 1", type="filepath")
                voice_sample_2 = gr.Audio(label="🎤 Voix 2", type="filepath")
                voice_sample_3 = gr.Audio(label="🎤 Voix 3", type="filepath")
                voice_sample_4 = gr.Audio(label="🎤 Voix 4", type="filepath")

        # Right column - Samples & Logs
        with gr.Column(scale=1):
            gr.Markdown("## 📊 Logs")
            logs_display = gr.HTML(value=sample_manager.get_logs_html())

            gr.Markdown("## 🔊 Samples Générés")
            sample_list_display = gr.HTML(value=get_sample_display_html())

            # Export section (moved to top)
            gr.Markdown("### 📦 Export")
            with gr.Row():
                export_btn = gr.Button("💾 Télécharger ZIP", variant="primary", size="lg")
                clear_btn = gr.Button("🗑️ Tout effacer", variant="stop", size="lg")

            status_export = gr.Textbox(label="Statut Export", interactive=False, lines=2)
            download_file = gr.File(label="📥 Fichier ZIP")

            # Audio players in accordion (closed by default)
            with gr.Accordion("🎵 Lecteurs Audio", open=False):
                gr.Markdown("*Lecteurs audio pour écouter et gérer vos samples*")

                # Create 20 audio players with delete buttons
                audio_players = []
                delete_buttons = []

                for i in range(20):
                    with gr.Row(elem_classes=["compact-row"]):
                        with gr.Column(scale=5):
                            audio = gr.Audio(
                                label=f"Sample {i+1}",
                                interactive=False,
                                elem_classes=["compact-audio"]
                            )
                            audio_players.append(audio)
                        with gr.Column(scale=1, min_width=40):
                            delete_btn = gr.Button(
                                "🗑️",
                                variant="secondary",
                                size="sm"
                            )
                            delete_buttons.append(delete_btn)

    # Help modal
    with gr.Accordion("💡 Guide d'utilisation", open=False) as help_accordion:
        gr.Markdown(create_help_popup())

    # Event handlers
    add_btn.click(
        fn=add_sample_handler,
        inputs=[text_input, voice_selector, voice_name_input, language_input,
                temperature, speed, voice_sample_1, voice_sample_2, voice_sample_3, voice_sample_4],
        outputs=[status_add, preview_audio, sample_list_display, logs_display] + audio_players
    )

    help_btn.click(
        fn=lambda: gr.update(open=True),
        outputs=[help_accordion]
    )

    export_btn.click(
        fn=lambda: export_handler(str(OUTPUTS_DIR)),
        outputs=[status_export, download_file]
    )

    clear_btn.click(
        fn=clear_all_handler,
        outputs=[status_export, sample_list_display, logs_display] + audio_players
    )

    # Delete buttons handlers
    for i, delete_btn in enumerate(delete_buttons):
        delete_btn.click(
            fn=lambda idx=i: delete_sample_handler(idx),
            outputs=[status_export, sample_list_display, logs_display] + audio_players
        )

    # Voice change handler to load saved settings
    voice_selector.change(
        fn=voice_changed_handler,
        inputs=[voice_selector, voice_sample_1, voice_sample_2, voice_sample_3, voice_sample_4],
        outputs=[temperature, speed]
    )


if __name__ == "__main__":
    print("🚀 Lancement de TTS Ultra Pro...")
    try:
        demo.launch(**GRADIO_CONFIG)
    except OSError as e:
        if "Cannot find empty port" in str(e):
            print(f"⚠️  Port {GRADIO_CONFIG.get('server_port', 7860)} occupé, recherche d'un port disponible...")
            from config.settings import GRADIO_CONFIG_AUTO_PORT
            demo.launch(**GRADIO_CONFIG_AUTO_PORT)
        else:
            raise
