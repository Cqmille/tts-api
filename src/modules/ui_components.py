"""UI Components for TTS Ultra Pro"""
import gradio as gr


def create_help_popup():
    """Create help popup content"""
    help_content = """
# 💡 Guide d'utilisation - TTS Ultra Pro

## Workflow de base :
1. ✍️ Écrivez le texte de votre sample
2. 🎭 Sélectionnez la voix à utiliser
3. 🎚️ Ajustez la température et la vitesse si nécessaire
4. ➕ Cliquez sur "Générer Sample"
5. 🔊 Écoutez le résultat dans la liste des samples
6. 🔁 Répétez pour créer plusieurs samples
7. 💾 Téléchargez le tout en ZIP quand c'est prêt !

## Génération en rafale :
Pour générer plusieurs samples d'un coup, séparez vos textes par des lignes vides dans le champ texte.
Le système générera automatiquement un sample pour chaque bloc de texte.

## Gestion des voix :
- 📤 Importez vos échantillons vocaux dans la section en bas
- Les paramètres (température/vitesse) sont mémorisés par voix
- Nommez vos voix pour mieux vous y retrouver

## Astuces :
- Utilisez `...` pour les pauses naturelles
- MAJUSCULES pour les emphases
- Les samples sont numérotés automatiquement
- Vous pouvez supprimer individuellement chaque sample
- La liste se réordonne automatiquement

## Logs :
Consultez la section logs pour suivre toutes les opérations en temps réel.
"""
    return help_content


def build_sample_display_with_delete(samples, on_delete_fn):
    """Build dynamic sample display with individual delete buttons"""
    if not samples:
        return gr.HTML(value="<div style='padding: 20px; text-align: center; color: #666;'>Aucun sample généré</div>")

    components = []
    for i, sample in enumerate(samples):
        with gr.Row():
            with gr.Column(scale=5):
                gr.Audio(value=sample["audio_path"], label=f"Sample {sample['number']} - {sample['voice_name']}")
            with gr.Column(scale=1):
                delete_btn = gr.Button("🗑️", size="sm", variant="secondary")
                delete_btn.click(fn=lambda idx=i: on_delete_fn(idx), outputs=[])

        components.append((sample, delete_btn))

    return components
