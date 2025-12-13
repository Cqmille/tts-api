"""TTS Ultra Pro - Interface Gradio avec support multi-moteur (XTTS v2 + Fish Speech)"""
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

# Try to initialize Fish Speech as default if available
_fish_speech_default = audio_manager.init_fish_speech_if_available()

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


def engine_changed_handler(engine_name):
    """Handle engine selection change"""
    success = audio_manager.set_engine(engine_name)

    if not success and engine_name == "fish_speech":
        sample_manager.add_log("Fish Speech non disponible - vérifiez que le serveur tourne sur http://127.0.0.1:7870", "error")
        # Reset to XTTS
        audio_manager.set_engine("xtts_v2")
        engine_name = "xtts_v2"

    is_xtts = (engine_name == "xtts_v2")
    is_fish = (engine_name == "fish_speech")

    # Get available languages for the selected engine
    if is_xtts:
        languages = SUPPORTED_LANGUAGES
    else:
        languages = FISH_SPEECH_LANGUAGES

    sample_manager.add_log(f"Moteur changé: {engine_name}", "info")

    return (
        gr.update(visible=is_xtts),          # speed slider (XTTS only)
        gr.update(visible=is_fish),          # top_p slider (Fish Speech only)
        gr.update(visible=is_fish),          # repetition_penalty slider (Fish Speech only)
        gr.update(choices=languages, value=languages[0] if languages else "fr"),  # language dropdown
        sample_manager.get_logs_html(),      # logs
        get_engine_status_html(engine_name)  # engine status
    )


def get_engine_status_html(engine_name):
    """Generate HTML status for current engine"""
    if engine_name == "xtts_v2":
        return """
        <div style='padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 8px; color: white;'>
            <strong>🔧 Moteur actif: XTTS v2 (Coqui)</strong><br>
            <small>Paramètres: Température, Vitesse</small>
        </div>
        """
    else:
        return """
        <div style='padding: 10px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    border-radius: 8px; color: white;'>
            <strong>🐟 Moteur actif: Fish Speech (OpenAudio S1-mini)</strong><br>
            <small>Paramètres: Température, Top P, Pénalité répétition</small>
        </div>
        """


def add_sample_handler(text, voice_sel, voice_name, lang, temp, spd, top_p, rep_pen, v1, v2, v3, v4):
    """Handle adding a new sample"""
    voice_map = {"Voix 1": v1, "Voix 2": v2, "Voix 3": v3, "Voix 4": v4}
    selected_voice = voice_map.get(voice_sel)

    # Check if batch generation (multiple paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    if len(paragraphs) > 1:
        # Batch generation
        sample_manager.add_log(f"Génération en rafale: {len(paragraphs)} samples", "info")
        results = sample_manager.add_samples_batch(
            paragraphs, selected_voice, voice_name, lang, temp, spd, audio_manager,
            top_p, rep_pen
        )
        status = f"✅ {len(results)} samples générés en rafale !"
        preview = results[-1][0] if results else None
    else:
        # Single generation
        preview, status = sample_manager.add_sample(
            text, selected_voice, voice_name, lang, temp, spd, audio_manager,
            top_p, rep_pen
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
        return (
            settings.get("temperature", TTS_CONFIG["default_temperature"]),
            settings.get("speed", TTS_CONFIG["default_speed"]),
            settings.get("top_p", 0.7),
            settings.get("repetition_penalty", 1.2)
        )

    return TTS_CONFIG["default_temperature"], TTS_CONFIG["default_speed"], 0.7, 1.2


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
        engine_badge = "🔧 XTTS" if sample.get("engine", "xtts_v2") == "xtts_v2" else "🐟 Fish"
        html += f"""
        <div style='padding: 8px 12px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    border-radius: 6px; display: flex; justify-content: space-between; align-items: center;'>
            <div style='color: white; font-weight: bold; font-size: 13px;'>
                🎬 Sample {sample['number']}
            </div>
            <div style='color: white; font-size: 12px;'>
                🎙️ {sample['voice_name']} | {engine_badge}
            </div>
            <div style='color: rgba(255,255,255,0.9); font-size: 11px; font-style: italic;'>
                {sample['text'][:40]}{'...' if len(sample['text']) > 40 else ''}
            </div>
        </div>
        """
    html += "</div>"
    return html


def check_fish_speech_status():
    """Check Fish Speech server status and return info"""
    engines = audio_manager.get_available_engines()
    fish_info = next((e for e in engines if e["name"] == "fish_speech"), None)

    if fish_info and fish_info["available"]:
        return "✅ Fish Speech disponible sur http://127.0.0.1:7870"
    else:
        return "⚠️ Fish Speech non disponible - Vérifiez que le serveur tourne"


# =========================================================================
# Fish Speech Reference Management
# =========================================================================

def get_fish_references_html():
    """Generate HTML list of Fish Speech references"""
    refs = audio_manager.fish_speech_list_references()

    if not refs:
        return """
        <div style='padding: 15px; text-align: center; color: #666; background: #f5f5f5; border-radius: 8px;'>
            <p>🐟 Aucun profil vocal Fish Speech configuré</p>
            <small>Ajoutez un profil ci-dessous pour utiliser Fish Speech</small>
        </div>
        """

    html = "<div style='display: flex; flex-direction: column; gap: 8px;'>"
    for ref in refs:
        html += f"""
        <div style='padding: 10px 15px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    border-radius: 8px; display: flex; justify-content: space-between; align-items: center;'>
            <div style='color: white;'>
                <strong>🐟 {ref}</strong>
            </div>
            <div style='color: rgba(255,255,255,0.8); font-size: 12px;'>
                Profil vocal actif
            </div>
        </div>
        """
    html += "</div>"
    return html


def get_fish_references_choices():
    """Get list of Fish Speech references for dropdown"""
    refs = audio_manager.fish_speech_list_references()
    return refs if refs else []


def add_fish_reference_handler(ref_id, audio_file, transcript):
    """Handle adding a new Fish Speech reference"""
    if not ref_id or not ref_id.strip():
        return "❌ L'ID du profil est requis", get_fish_references_html(), gr.update(choices=get_fish_references_choices())

    if not audio_file:
        return "❌ Le fichier audio est requis", get_fish_references_html(), gr.update(choices=get_fish_references_choices())

    if not transcript or not transcript.strip():
        return "❌ La transcription est obligatoire pour Fish Speech", get_fish_references_html(), gr.update(choices=get_fish_references_choices())

    # Clean the reference ID (remove spaces, special chars)
    clean_id = ref_id.strip().lower().replace(" ", "_")

    success, message = audio_manager.fish_speech_add_reference(clean_id, audio_file, transcript)

    if success:
        sample_manager.add_log(f"Profil Fish Speech '{clean_id}' ajouté", "success")
        return f"✅ {message}", get_fish_references_html(), gr.update(choices=get_fish_references_choices())
    else:
        sample_manager.add_log(f"Erreur ajout profil: {message}", "error")
        return f"❌ {message}", get_fish_references_html(), gr.update(choices=get_fish_references_choices())


def delete_fish_reference_handler(ref_id):
    """Handle deleting a Fish Speech reference"""
    if not ref_id:
        return "❌ Sélectionnez un profil à supprimer", get_fish_references_html(), gr.update(choices=get_fish_references_choices())

    success, message = audio_manager.fish_speech_delete_reference(ref_id)

    if success:
        sample_manager.add_log(f"Profil Fish Speech '{ref_id}' supprimé", "success")
        return f"✅ {message}", get_fish_references_html(), gr.update(choices=get_fish_references_choices())
    else:
        sample_manager.add_log(f"Erreur suppression profil: {message}", "error")
        return f"❌ {message}", get_fish_references_html(), gr.update(choices=get_fish_references_choices())


def refresh_fish_references_handler():
    """Refresh the Fish Speech references list"""
    return get_fish_references_html(), gr.update(choices=get_fish_references_choices())


# Interface Gradio
with gr.Blocks(title="TTS Ultra Pro", theme=gr.themes.Soft(), css="""
    .compact-audio audio { height: 35px !important; }
    .compact-row { margin: 4px 0 !important; padding: 6px !important; }
    .engine-selector { margin-bottom: 15px !important; }
""") as demo:
    gr.Markdown("# 🎬 TTS Ultra Pro - Multi-Engine")
    gr.Markdown("**Interface professionnelle de génération TTS multi-voix avec support XTTS v2 et Fish Speech**")

    with gr.Row():
        with gr.Column(scale=1):
            # Engine selection section
            gr.Markdown("## 🔧 Sélection du Moteur TTS")

            with gr.Group(elem_classes=["engine-selector"]):
                # Default to Fish Speech if available, otherwise XTTS
                _default_engine = "fish_speech" if _fish_speech_default else "xtts_v2"
                engine_selector = gr.Radio(
                    choices=[
                        ("XTTS v2 (Coqui) - Voice cloning haute qualité", "xtts_v2"),
                        ("Fish Speech (OpenAudio S1-mini) - Rapide, expressif", "fish_speech")
                    ],
                    value=_default_engine,
                    label="🎯 Moteur TTS",
                    info="Choisissez le moteur de synthèse vocale"
                )
                engine_status = gr.HTML(value=get_engine_status_html(_default_engine))
                fish_status_info = gr.Markdown(value=check_fish_speech_status())

            gr.Markdown("---")
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

            # Language selection
            with gr.Row():
                # Use Fish Speech languages if it's the default engine
                _default_languages = FISH_SPEECH_LANGUAGES if _fish_speech_default else SUPPORTED_LANGUAGES
                language_input = gr.Dropdown(
                    choices=_default_languages,
                    value=TTS_CONFIG["default_language"],
                    label="🌍 Langue"
                )

            # Common parameter: Temperature (both engines)
            temperature = gr.Slider(
                minimum=0.1, maximum=1.0, value=TTS_CONFIG["default_temperature"], step=0.05,
                label="🔥 Température",
                info="Créativité de génération (plus haut = plus varié)"
            )

            # XTTS-specific parameter: Speed
            speed = gr.Slider(
                minimum=0.5, maximum=2.0, value=TTS_CONFIG["default_speed"], step=0.1,
                label="⚡ Vitesse (XTTS uniquement)",
                info="Vitesse de parole",
                visible=not _fish_speech_default  # Hidden if Fish Speech is default
            )

            # Fish Speech-specific parameters
            top_p = gr.Slider(
                minimum=0.1, maximum=1.0, value=0.7, step=0.05,
                label="🎲 Top P (Fish Speech)",
                info="Nucleus sampling - diversité des choix",
                visible=_fish_speech_default  # Visible if Fish Speech is default
            )

            repetition_penalty = gr.Slider(
                minimum=1.0, maximum=2.0, value=1.2, step=0.1,
                label="🔄 Pénalité répétition (Fish Speech)",
                info="Évite les répétitions dans la génération",
                visible=_fish_speech_default  # Visible if Fish Speech is default
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
            with gr.Accordion("Échantillons Vocaux (XTTS)", open=False):
                gr.Markdown("*Uploadez vos échantillons vocaux (un par voix) - WAV recommandé, 10-30 secondes*")
                voice_sample_1 = gr.Audio(label="🎤 Voix 1", type="filepath")
                voice_sample_2 = gr.Audio(label="🎤 Voix 2", type="filepath")
                voice_sample_3 = gr.Audio(label="🎤 Voix 3", type="filepath")
                voice_sample_4 = gr.Audio(label="🎤 Voix 4", type="filepath")

            # Fish Speech Reference Management
            with gr.Accordion("🐟 Gestion des Profils Fish Speech", open=False):
                gr.Markdown("""
                **Important:** Fish Speech nécessite de créer un profil vocal avant de générer.
                Le profil inclut l'audio de référence ET la transcription de ce qui est dit.
                """)

                # List of existing references
                fish_refs_display = gr.HTML(value=get_fish_references_html())

                gr.Markdown("### ➕ Ajouter un nouveau profil")

                with gr.Row():
                    fish_ref_id = gr.Textbox(
                        label="🏷️ ID du profil",
                        placeholder="Ex: pascal, marie, narrateur...",
                        info="Identifiant unique (sans espaces)",
                        scale=1
                    )

                fish_ref_audio = gr.Audio(
                    label="🎤 Fichier audio de référence",
                    type="filepath",
                    info="WAV recommandé, 10-30 secondes de parole claire"
                )

                fish_ref_text = gr.Textbox(
                    label="📝 Transcription (OBLIGATOIRE)",
                    placeholder="Tapez exactement ce qui est dit dans l'audio...",
                    lines=3,
                    info="Le texte exact prononcé dans l'échantillon audio"
                )

                with gr.Row():
                    fish_add_btn = gr.Button("➕ Créer le profil", variant="primary")
                    fish_refresh_btn = gr.Button("🔄 Actualiser", variant="secondary")

                fish_status = gr.Textbox(label="Statut", interactive=False, lines=1)

                gr.Markdown("### 🗑️ Supprimer un profil")
                with gr.Row():
                    fish_delete_dropdown = gr.Dropdown(
                        choices=get_fish_references_choices(),
                        label="Sélectionner un profil",
                        info="Choisir le profil à supprimer",
                        scale=2
                    )
                    fish_delete_btn = gr.Button("🗑️ Supprimer", variant="stop", scale=1)

        # Right column - Samples & Logs
        with gr.Column(scale=1):
            gr.Markdown("## 📊 Logs")
            logs_display = gr.HTML(value=sample_manager.get_logs_html())

            gr.Markdown("## 🔊 Samples Générés")
            sample_list_display = gr.HTML(value=get_sample_display_html())

            gr.Markdown("### 🎵 Lecteurs Audio")
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
                    with gr.Column(scale=1, min_width=80):
                        delete_btn = gr.Button(
                            f"🗑️ #{i+1}",
                            variant="secondary",
                            size="sm"
                        )
                        delete_buttons.append(delete_btn)

            # Export section
            gr.Markdown("### 📦 Export")
            with gr.Row():
                export_btn = gr.Button("💾 Télécharger ZIP", variant="primary", size="lg")
                clear_btn = gr.Button("🗑️ Tout effacer", variant="stop", size="lg")

            status_export = gr.Textbox(label="Statut Export", interactive=False, lines=2)
            download_file = gr.File(label="📥 Fichier ZIP")

    # Help modal
    with gr.Accordion("💡 Guide d'utilisation", open=False) as help_accordion:
        gr.Markdown(create_help_popup())

        # Additional Fish Speech info
        gr.Markdown("""
        ---
        ## 🐟 Fish Speech - Fonctionnalités avancées

        Fish Speech (OpenAudio S1-mini) supporte des marqueurs d'émotion et de ton spéciaux :

        **Émotions basiques :**
        ```
        (angry) (sad) (excited) (surprised) (satisfied) (delighted)
        (scared) (worried) (upset) (nervous) (frustrated) (depressed)
        ```

        **Émotions avancées :**
        ```
        (disdainful) (unhappy) (anxious) (hysterical) (indifferent)
        (impatient) (sarcastic) (sincere) (hesitating)
        ```

        **Marqueurs de ton :**
        ```
        (in a hurry tone) (shouting) (screaming) (whispering) (soft tone)
        ```

        **Effets spéciaux :**
        ```
        (laughing) (chuckling) (sobbing) (crying loudly) (sighing)
        ```

        Exemple : `(excited) Quelle bonne nouvelle ! (laughing) Ha ha ha !`
        """)

    # Event handlers

    # Engine change handler
    engine_selector.change(
        fn=engine_changed_handler,
        inputs=[engine_selector],
        outputs=[speed, top_p, repetition_penalty, language_input, logs_display, engine_status]
    )

    add_btn.click(
        fn=add_sample_handler,
        inputs=[text_input, voice_selector, voice_name_input, language_input,
                temperature, speed, top_p, repetition_penalty,
                voice_sample_1, voice_sample_2, voice_sample_3, voice_sample_4],
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
        outputs=[temperature, speed, top_p, repetition_penalty]
    )

    # Fish Speech reference management handlers
    fish_add_btn.click(
        fn=add_fish_reference_handler,
        inputs=[fish_ref_id, fish_ref_audio, fish_ref_text],
        outputs=[fish_status, fish_refs_display, fish_delete_dropdown]
    )

    fish_delete_btn.click(
        fn=delete_fish_reference_handler,
        inputs=[fish_delete_dropdown],
        outputs=[fish_status, fish_refs_display, fish_delete_dropdown]
    )

    fish_refresh_btn.click(
        fn=refresh_fish_references_handler,
        outputs=[fish_refs_display, fish_delete_dropdown]
    )


if __name__ == "__main__":
    print("🚀 Lancement de TTS Ultra Pro (Multi-Engine)...")
    print(f"📍 Moteurs disponibles: {[e['name'] for e in audio_manager.get_available_engines()]}")
    demo.launch(**GRADIO_CONFIG)
