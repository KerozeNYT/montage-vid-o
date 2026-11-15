# Montage vidéo — SOLAR CAR 37 & SOLAR HOME 37

Chaîne de montage de vidéos courtes (Reels/TikTok 9:16, 1:1, 16:9) avec des outils gratuits :
ffmpeg, faster-whisper, auto-editor, Remotion.

```bash
./montage analyse   <dossier_rushs> <projet>   # copie, infos, planches, transcription
./montage assembler <projet>                   # plan.json → vidéo coupée + sous-titres
./montage rendu     <projet>                   # Remotion + son −14 LUFS → exports/
./montage controle  <projet>                   # images et mesures à vérifier
```

- Règles de montage et de marque : [CLAUDE.md](CLAUDE.md)
- Installation (session cloud Linux) : `bash scripts/setup-cloud.sh`

Seuls le code, les modèles (`templates/`) et la documentation sont versionnés.
Les rushs, les exports et les fichiers audio/vidéo restent hors de GitHub.
