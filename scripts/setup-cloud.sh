#!/usr/bin/env bash
# Installation des outils de montage dans une session cloud Claude Code (Linux).
# Utilisé comme script de démarrage de l'environnement « montage-vid-o ».
# Relançable sans risque : ne réinstalle pas ce qui est déjà là.
set -euo pipefail

PREFIX=/opt/montage

# 1. Python : faster-whisper (transcription) + auto-editor (blancs)
if [[ ! -x "$PREFIX/bin/python" ]]; then
  python3 -m venv "$PREFIX"
fi
"$PREFIX/bin/pip" install -q --disable-pip-version-check faster-whisper==1.2.1 auto-editor==29.3.1
"$PREFIX/bin/auto-editor" --version >/dev/null   # télécharge le binaire au 1er lancement
ln -sf "$PREFIX/bin/auto-editor" /usr/local/bin/auto-editor

# 2. Modèle Whisper large-v3-turbo (~1,6 Go)
"$PREFIX/bin/python" -I -c "
from faster_whisper import WhisperModel
WhisperModel('large-v3-turbo', device='cpu', compute_type='int8', download_root='$PREFIX/models')
"

# 3. Remotion (si le dépôt est présent dans la session)
for dir in montage-vid-o/templates templates; do
  if [[ -f "$dir/package-lock.json" ]]; then
    (cd "$dir" && npm ci --no-fund --no-audit --loglevel=error)
    break
  fi
done
