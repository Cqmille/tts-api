"""Sample management for TTS generation"""
import os
from datetime import datetime
import zipfile
from .utils import sanitize_filename, get_voice_name


class SampleManager:
    """Manages audio samples generation, storage, and operations"""

    def __init__(self, temp_audio_dir):
        self.samples = []
        self.temp_audio_dir = temp_audio_dir
        self.logs = []
        self.voice_settings = {}  # Mémorisation des paramètres par voix

        # Ensure temp directory exists
        os.makedirs(self.temp_audio_dir, exist_ok=True)

    def add_log(self, message, level="info"):
        """Add a log entry"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
        # Keep only last 50 logs
        if len(self.logs) > 50:
            self.logs = self.logs[-50:]

    def get_logs_html(self):
        """Build HTML for logs display"""
        if not self.logs:
            return "<div style='padding: 15px; text-align: center; color: #999; font-size: 13px;'>Aucun log pour le moment</div>"

        html = "<div style='font-family: monospace; font-size: 12px; max-height: 400px; overflow-y: auto;'>"

        # Reverse to show newest first
        for log in reversed(self.logs):
            level_colors = {
                "info": "#4CAF50",
                "success": "#2196F3",
                "warning": "#FF9800",
                "error": "#F44336"
            }
            color = level_colors.get(log["level"], "#999")

            html += f"""
            <div style='padding: 6px 10px; margin: 2px 0; background: rgba(0,0,0,0.05);
                        border-left: 3px solid {color}; border-radius: 3px;'>
                <span style='color: #666;'>[{log['timestamp']}]</span>
                <span style='color: {color}; font-weight: bold;'> {log['level'].upper()}</span>
                <span style='color: #333;'> - {log['message']}</span>
            </div>
            """

        html += "</div>"
        return html

    def save_voice_settings(self, voice_name, temperature, speed):
        """Save temperature and speed for a specific voice"""
        self.voice_settings[voice_name] = {
            "temperature": temperature,
            "speed": speed
        }

    def get_voice_settings(self, voice_name):
        """Get saved settings for a voice, or return defaults"""
        return self.voice_settings.get(voice_name, {
            "temperature": 0.75,
            "speed": 1.0
        })

    def add_sample(self, text, voice_sample, voice_name, language, temperature, speed, audio_manager):
        """Add a new sample"""
        try:
            if not text or not text.strip():
                self.add_log("Le texte ne peut pas être vide", "error")
                return None, "❌ Le texte ne peut pas être vide"

            if not voice_sample:
                self.add_log("Aucun échantillon vocal sélectionné", "error")
                return None, "❌ Veuillez sélectionner un échantillon vocal"

            # Generate filename
            sample_number = len(self.samples) + 1
            base_name = sanitize_filename(text, max_length=30)
            safe_voice_name = sanitize_filename(voice_name if voice_name else get_voice_name(voice_sample))
            filename = f"sample_{sample_number:03d}_{safe_voice_name}_{base_name}.wav"
            output_path = os.path.join(self.temp_audio_dir, filename)

            # Generate audio
            self.add_log(f"Génération du sample {sample_number} avec {safe_voice_name}...", "info")
            audio_manager.generate_audio(
                text=text,
                speaker_wav=voice_sample,
                language=language,
                output_path=output_path,
                temperature=temperature,
                speed=speed
            )

            # Save voice settings
            self.save_voice_settings(safe_voice_name, temperature, speed)

            # Add to samples
            self.samples.append({
                "number": sample_number,
                "text": text,
                "voice_name": safe_voice_name,
                "audio_path": output_path,
                "filename": filename,
                "temperature": temperature,
                "speed": speed
            })

            self.add_log(f"✓ Sample {sample_number} généré avec succès", "success")
            status = f"✅ Sample {sample_number} ajouté !\n🎙️ Voix: {safe_voice_name}\n📝 {text[:50]}..."
            return output_path, status

        except Exception as e:
            self.add_log(f"Erreur lors de la génération: {str(e)}", "error")
            return None, f"❌ Erreur: {str(e)}"

    def add_samples_batch(self, texts, voice_sample, voice_name, language, temperature, speed, audio_manager):
        """Add multiple samples in batch"""
        results = []
        for i, text in enumerate(texts, 1):
            if text.strip():
                self.add_log(f"Génération en rafale: {i}/{len(texts)}", "info")
                output_path, status = self.add_sample(
                    text, voice_sample, voice_name, language,
                    temperature, speed, audio_manager
                )
                results.append((output_path, status))

        self.add_log(f"✓ Génération en rafale terminée: {len(results)} samples", "success")
        return results

    def remove_sample(self, sample_index):
        """Remove a specific sample and reorder"""
        try:
            if sample_index < 0 or sample_index >= len(self.samples):
                self.add_log(f"Index invalide: {sample_index}", "error")
                return False, "❌ Index invalide"

            removed = self.samples.pop(sample_index)

            # Remove file
            try:
                if os.path.exists(removed["audio_path"]):
                    os.remove(removed["audio_path"])
            except Exception as e:
                self.add_log(f"Erreur lors de la suppression du fichier: {str(e)}", "warning")

            # Reorder samples
            for i, sample in enumerate(self.samples, 1):
                sample["number"] = i

            self.add_log(f"✓ Sample {removed['number']} supprimé", "success")
            return True, f"🗑️ Sample supprimé"

        except Exception as e:
            self.add_log(f"Erreur lors de la suppression: {str(e)}", "error")
            return False, f"❌ Erreur: {str(e)}"

    def clear_all(self):
        """Clear all samples"""
        try:
            # Remove all files
            for sample in self.samples:
                try:
                    if os.path.exists(sample["audio_path"]):
                        os.remove(sample["audio_path"])
                except:
                    pass

            count = len(self.samples)
            self.samples = []
            self.add_log(f"✓ {count} samples effacés", "success")
            return True, f"🗑️ {count} samples effacés"

        except Exception as e:
            self.add_log(f"Erreur lors de l'effacement: {str(e)}", "error")
            return False, f"❌ Erreur: {str(e)}"

    def get_samples_html(self):
        """Build HTML display for samples"""
        if not self.samples:
            return "<div style='padding: 20px; text-align: center; color: #666;'>Aucun sample généré</div>"

        html = "<div style='font-family: Arial, sans-serif;'>"
        for i, sample in enumerate(self.samples):
            html += f"""
            <div style='margin: 8px 0; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: bold; color: white; font-size: 14px;'>
                        🎬 Sample {sample['number']} - 🎙️ {sample['voice_name']}
                    </span>
                    <button onclick='alert("Sample {i}")' style='background: rgba(255,255,255,0.2);
                            border: none; padding: 4px 10px; border-radius: 12px;
                            color: white; font-size: 11px; cursor: pointer;'>
                        {sample['filename']}
                    </button>
                </div>
                <div style='background: rgba(255,255,255,0.95); padding: 8px; border-radius: 6px;
                            color: #333; font-size: 13px; line-height: 1.4; margin-top: 6px;'>
                    "{sample['text'][:100]}{'...' if len(sample['text']) > 100 else ''}"
                </div>
            </div>
            """
        html += "</div>"
        return html

    def get_audio_paths(self):
        """Return list of audio paths"""
        return [sample["audio_path"] for sample in self.samples]

    def export_to_zip(self, output_dir):
        """Export all samples to ZIP"""
        try:
            if not self.samples:
                self.add_log("Aucun sample à exporter", "warning")
                return None, "❌ Aucun sample à exporter"

            os.makedirs(output_dir, exist_ok=True)

            # Create ZIP filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"samples_{timestamp}.zip"
            zip_path = os.path.join(output_dir, zip_filename)

            # Create ZIP
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for sample in self.samples:
                    zipf.write(sample["audio_path"], sample["filename"])

            self.add_log(f"✓ Export réussi: {len(self.samples)} samples", "success")
            status = f"✅ Export réussi !\n📦 {len(self.samples)} fichiers\n📁 {zip_filename}"
            return zip_path, status

        except Exception as e:
            self.add_log(f"Erreur lors de l'export: {str(e)}", "error")
            return None, f"❌ Erreur: {str(e)}"
