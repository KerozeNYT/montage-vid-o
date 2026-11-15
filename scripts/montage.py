#!/usr/bin/env python3
"""Chaîne de montage SOLAR CAR 37 / SOLAR HOME 37.

  ./montage analyse   <dossier_rushs> <projet>   copie, infos, planches, transcription
  ./montage assembler <projet>                   plans → vidéo principale + sous-titres
  ./montage rendu     <projet>                   Remotion + son normalisé → exports/
  ./montage controle  <projet>                   images, son et format à vérifier

<projet> = AAAA-MM-JJ_marque_sujet_format (ex. 2026-11-15_solar-car_vitres-teintees_9x16).
Les rushs originaux ne sont jamais modifiés : tout se passe dans work/<projet>/.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUSHS = ROOT / "rushs"
WORK = ROOT / "work"
EXPORTS = ROOT / "exports"
TEMPLATES = ROOT / "templates"

FPS = 30
FORMATS = {
    "9x16": (1080, 1920, "Reel-9x16"),
    "1x1": (1080, 1080, "Carre-1x1"),
    "16x9": (1920, 1080, "Paysage-16x9"),
}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".mts", ".m2ts", ".webm", ".3gp"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
PROJECT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_(solar-car|solar-home)_[a-z0-9]+(-[a-z0-9]+)*_(9x16|1x1|16x9)$")
HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}
VOCABULAIRE = {
    "solar-car": "SOLAR CAR 37, Vouvray, vitres teintées, feux teintés, detailing, rénovation de phares, ciel étoilé, covering.",
    "solar-home": "SOLAR HOME 37, films pour vitrages, vitrage, baie vitrée, film solaire, film occultant, Tours.",
}
# Noms de marque fusionnés en un seul bloc de sous-titre (jamais coupés en deux).
NOMS_MARQUES = [
    ["solar car 37", "SOLAR CAR 37"], ["solaire car 37", "SOLAR CAR 37"], ["solarcar 37", "SOLAR CAR 37"],
    ["solar home 37", "SOLAR HOME 37"], ["solaire home 37", "SOLAR HOME 37"], ["solarhome 37", "SOLAR HOME 37"],
]
WHISPER_MODEL = os.environ.get("MONTAGE_WHISPER_MODEL", "large-v3-turbo")
WHISPER_DIR = os.environ.get("MONTAGE_MODELS", "/opt/montage/models")


# ─── utilitaires ────────────────────────────────────────────────────────────
def die(msg: str) -> None:
    print(f"✘ {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd: list[str], capture: bool = False, cwd: Path | None = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=capture)
    if res.returncode != 0:
        if capture:
            sys.stderr.write(res.stderr[-3000:])
        die(f"échec : {' '.join(cmd[:3])} …")
    return res.stdout if capture else ""


def ffmpeg(*args: str) -> None:
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args])


def probe(path: Path) -> dict:
    out = run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture=True,
    )
    data = json.loads(out)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    info = {"duree": float(data["format"].get("duration", 0)), "audio": a is not None}
    if v:
        rot = 0
        for sd in v.get("side_data_list", []):
            if "rotation" in sd:
                rot = int(sd["rotation"])
        rot = int(v.get("tags", {}).get("rotate", rot))
        w, h = v["width"], v["height"]
        if abs(rot) in (90, 270):
            w, h = h, w
        num, den = (v.get("avg_frame_rate") or "0/1").split("/")
        info.update(
            largeur=w,
            hauteur=h,
            ips=round(float(num) / float(den), 2) if float(den) else 0,
            codec=v["codec_name"],
            rotation=rot,
            hdr=v.get("color_transfer") in HDR_TRANSFERS,
            duree_video=float(v.get("duration", info["duree"])),
        )
    return info


def safe_copy(src: Path, dst: Path) -> None:
    """Copie sans jamais écrire dans rushs/ (clone instantané si le disque le permet)."""
    if RUSHS.resolve() in dst.resolve().parents:
        die(f"écriture interdite dans rushs/ : {dst}")
    if dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    flag = "-c" if platform.system() == "Darwin" else "--reflink=auto"
    if subprocess.run(["cp", flag, str(src), str(dst)]).returncode != 0:
        shutil.copy2(src, dst)


def check_project(projet: str) -> tuple[str, str]:
    m = PROJECT_RE.match(projet)
    if not m:
        die("nom de projet invalide. Attendu : AAAA-MM-JJ_marque_sujet_format "
            "(marque = solar-car|solar-home, format = 9x16|1x1|16x9)")
    return m.group(1), m.group(3)


def tc(sec: float) -> str:
    return f"{int(sec // 60):02d}:{sec % 60:05.2f}"


# ─── transcription ──────────────────────────────────────────────────────────
_model = None


def transcrire(path: Path, prompt: str | None) -> dict:
    global _model
    from faster_whisper import WhisperModel  # import tardif : lourd

    import numpy as np

    if _model is None:
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8",
                              download_root=WHISPER_DIR, cpu_threads=os.cpu_count() or 4)
    # Audio décodé par ffmpeg (16 kHz mono) : évite les soucis de compatibilité de PyAV.
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    segments, info = _model.transcribe(
        audio, language="fr", word_timestamps=True, beam_size=5,
        initial_prompt=prompt, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    segs, words = [], []
    for s in segments:
        segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
        first = len(words)
        for w in s.words or []:
            text = w.word.strip()
            if not text:
                continue
            # Ponctuation seule (« ? », « ! ») : collée au mot précédent, espace insécable à la française.
            if words and re.fullmatch(r"[.,!?;:…»)]+", text):
                words[-1]["text"] += ("\u00a0" if text[0] in "?!:;»" else "") + text
                words[-1]["end"] = round(w.end, 3)
            # Morceau collé au mot précédent (« s » + « 'occupe », « rendez » + « -vous ») : on fusionne.
            elif len(words) > first and (not w.word.startswith(" ") or text[0] in "'’-"):
                words[-1]["text"] += text
                words[-1]["end"] = round(w.end, 3)
            else:
                words.append({"text": text, "start": round(w.start, 3), "end": round(w.end, 3)})
    return {"duree": round(info.duration, 2), "segments": segs, "words": words}


def _norm(s: str) -> str:
    return re.sub(r"[^\wÀ-ÿ']", "", s.lower())


def appliquer_corrections(words: list[dict], corrections: list[list[str]]) -> list[dict]:
    """corrections = [["solaire car", "SOLAR CAR"], ...] (un ou plusieurs mots → texte corrigé)."""
    for wrong, right in corrections:
        pat = [_norm(x) for x in wrong.split()]
        i, out = 0, []
        while i < len(words):
            chunk = words[i:i + len(pat)]
            if len(chunk) == len(pat) and [_norm(w["text"]) for w in chunk] == pat:
                tail = re.search(r"[.,!?;:…]+$", chunk[-1]["text"])
                # On garde la ponctuation d'origine, sauf si la correction la précise déjà.
                explicit = re.search(r"[.,!?;:…]$", wrong) or re.search(r"[.,!?;:…]$", right)
                keep = tail.group(0) if tail and not explicit else ""
                out.append({"text": right + keep,
                            "start": chunk[0]["start"], "end": chunk[-1]["end"]})
                i += len(pat)
            else:
                out.append(words[i])
                i += 1
        words = out
    return words


# ─── analyse ────────────────────────────────────────────────────────────────
def cmd_analyse(args: argparse.Namespace) -> None:
    marque, _ = check_project(args.projet)
    src_dir = Path(args.rushs)
    if not src_dir.is_dir():
        src_dir = RUSHS / args.rushs
    if not src_dir.is_dir():
        die(f"dossier de rushs introuvable : {args.rushs}")
    videos = sorted(p for p in src_dir.iterdir() if p.suffix.lower() in VIDEO_EXT)
    photos = sorted(p for p in src_dir.iterdir() if p.suffix.lower() in IMAGE_EXT)
    if not videos and not photos:
        die(f"aucune vidéo ni photo dans {src_dir}")

    proj = WORK / args.projet
    out = proj / "analyse"
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"# Analyse — {args.projet}", "", f"Rushs : `{src_dir}` ({len(videos)} fichiers)", ""]
    for v in videos:
        copie = proj / "src" / v.name
        safe_copy(v, copie)
        info = probe(copie)
        print(f"▶ {v.name} — {tc(info['duree'])}")
        # Planche : 20 images réparties sur la durée.
        planche = out / f"{v.stem}_planche.jpg"
        rate = 20 / max(info["duree"], 1)
        ffmpeg("-i", str(copie), "-vf", f"fps={rate:.4f},scale=360:-2,tile=5x4:padding=4", "-frames:v", "1",
               "-q:v", "4", str(planche))
        lines += [f"## {v.name}", "",
                  f"- Durée : {tc(info['duree'])} — {info.get('largeur')}×{info.get('hauteur')} — "
                  f"{info.get('ips')} i/s — {info.get('codec')} — HDR : {'oui' if info.get('hdr') else 'non'} — "
                  f"son : {'oui' if info['audio'] else 'non'}",
                  f"- Planche : `{planche.relative_to(ROOT)}` (20 images, de gauche à droite puis de haut en bas)", ""]
        if info["audio"] and not args.sans_transcription:
            tr = transcrire(copie, VOCABULAIRE[marque])
            (out / f"{v.stem}.json").write_text(json.dumps(tr, ensure_ascii=False, indent=1))
            if tr["segments"]:
                lines += [f"- `{tc(s['start'])}–{tc(s['end'])}` {s['text']}" for s in tr["segments"]]
            else:
                lines.append("- (pas de voix détectée)")
            lines.append("")
    if photos:
        lines += ["## Photos", ""]
    for ph in photos:
        safe_copy(ph, proj / "src" / ph.name)
        dims = run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(ph)],
                   capture=True).strip()
        lines.append(f"- `{ph.name}` — {dims} (à regarder directement)")
    rapport = out / "rapport.md"
    rapport.write_text("\n".join(lines))
    print(f"✔ Rapport : {rapport.relative_to(ROOT)}")


# ─── assemblage ─────────────────────────────────────────────────────────────
def video_filter(info: dict, w: int, h: int, plan: dict) -> str:
    chain = []
    if info.get("hdr"):
        chain.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                     "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    px, py = plan.get("position_x", 0.5), plan.get("position_y", 0.5)
    cover = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}:(iw-{w})*{px}:(ih-{h})*{py}"
    vitesse = float(plan.get("vitesse", 1))
    if vitesse != 1:
        chain.append(f"setpts=PTS/{vitesse}")
    base = ",".join(chain) + "," if chain else ""
    if plan.get("cadrage", "remplir") == "flou":
        return (f"[0:v]{base}split[a][b];[a]{cover},boxblur=40:4[bg];"
                f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,fps={FPS},format=yuv420p,setsar=1[v]")
    return f"[0:v]{base}{cover},fps={FPS},format=yuv420p,setsar=1[v]"


def auto_editor_bin() -> str:
    return shutil.which("auto-editor") or "/opt/montage/bin/auto-editor"


def cmd_assembler(args: argparse.Namespace) -> None:
    marque, fmt = check_project(args.projet)
    w, h, _ = FORMATS[fmt]
    proj = WORK / args.projet
    plan_path = proj / "plan.json"
    if not plan_path.exists():
        die(f"{plan_path.relative_to(ROOT)} absent (le plan de montage validé)")
    plan = json.loads(plan_path.read_text())
    if plan.get("marque", marque) != marque:
        die("la marque du plan ne correspond pas au nom du projet")

    plans_dir, public = proj / "plans", proj / "public"
    plans_dir.mkdir(exist_ok=True)
    public.mkdir(exist_ok=True)
    pieces: list[Path] = []
    reveals_raw: list[dict] = []
    codecs = ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-c:a", "aac", "-b:a", "192k",
              "-ar", "48000", "-ac", "2"]

    def source(name: str, i: int) -> Path:
        path = proj / "src" / name
        if not path.exists():
            die(f"plan {i} : {name} absent de work/{args.projet}/src (lancer « analyse » d'abord)")
        return path

    def photo_segment(img: Path, dur: float, p: dict, out: Path) -> None:
        ffmpeg("-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(img),
               "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
               "-filter_complex", video_filter({}, w, h, p), "-map", "[v]", "-map", "1:a", *codecs,
               "-shortest", str(out))

    for i, p in enumerate(plan["plans"], 1):
        brut = plans_dir / f"{i:02d}.mp4"
        # Révélation avant / après (deux photos) : fond = photo « avant », effet ajouté par Remotion.
        if "avant_apres" in p:
            aa, dur = p["avant_apres"], float(p.get("duree", 3.5))
            avant, apres = source(aa["avant"], i), source(aa["apres"], i)
            print(f"▶ plan {i} : avant/après {avant.name} → {apres.name} ({dur:.1f} s)")
            photo_segment(avant, dur, p, brut)
            reveals_raw.append({"index": i - 1, "before": avant, "after": apres, "plan": p})
            pieces.append(brut)
            continue
        src = source(p["src"], i)
        # Photo seule.
        if src.suffix.lower() in IMAGE_EXT:
            dur = float(p.get("duree", 2.0))
            print(f"▶ plan {i} : photo {src.name} ({dur:.1f} s)")
            photo_segment(src, dur, p, brut)
            pieces.append(brut)
            continue
        info = probe(src)
        debut = float(p.get("debut", 0))
        fin = min(float(p.get("fin", info["duree"])), info["duree"])
        vitesse = float(p.get("vitesse", 1))
        if not 0.5 <= vitesse <= 2:
            die(f"plan {i} : vitesse entre 0.5 et 2")
        sortie = (fin - debut) / vitesse
        son = info["audio"] and p.get("son", True)
        cmd = ["-ss", f"{debut:.3f}", "-t", f"{fin - debut:.3f}", "-i", str(src)]
        graph = video_filter(info, w, h, p)
        if son:
            graph += f";[0:a:0]atempo={vitesse}[a]" if vitesse != 1 else ";[0:a:0]anull[a]"
            amap = "[a]"
        else:
            cmd += ["-f", "lavfi", "-t", f"{sortie:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            amap = "1:a"
        cmd += ["-filter_complex", graph, "-map", "[v]", "-map", amap, *codecs, "-shortest", str(brut)]
        ralenti = f" — vitesse ×{vitesse}" if vitesse != 1 else ""
        print(f"▶ plan {i} : {p['src']} {tc(debut)} → {tc(fin)}{ralenti}")
        ffmpeg(*cmd)
        piece = brut
        if son and p.get("couper_blancs", True):
            cut = plans_dir / f"{i:02d}_coupe.mp4"
            run([auto_editor_bin(), str(brut), "--margin", str(p.get("marge", "0.15s")), "--no-open", "--progress", "none",
                 "-c:v", "libx264", "-b:v", "24M", "-o", str(cut)])
            if cut.exists() and probe(cut)["duree"] >= 0.5:
                piece = cut
                print(f"  blancs coupés : {tc(probe(brut)['duree'])} → {tc(probe(cut)['duree'])}")
        pieces.append(piece)

    # Assemblage + instants de coupe.
    durees = [probe(x).get("duree_video", 0) for x in pieces]
    main = public / "main.mp4"
    inputs = sum((["-i", str(x)] for x in pieces), [])
    streams = "".join(f"[{i}:v][{i}:a]" for i in range(len(pieces)))
    ffmpeg(*inputs, "-filter_complex", f"{streams}concat=n={len(pieces)}:v=1:a=1[v][a]",
           "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "16",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(main))
    duree = probe(main)["duree_video"]
    starts, acc = [], 0.0
    for d in durees:
        starts.append(acc)
        acc += d
    cuts = [round(s, 3) for s in starts[1:]]

    # Sous-titres sur la vidéo assemblée.
    words: list[dict] = []
    if plan.get("sous_titres", True):
        print("▶ transcription de la vidéo assemblée")
        words = transcrire(main, plan.get("vocabulaire", VOCABULAIRE[marque]))["words"]
        words = appliquer_corrections(words, NOMS_MARQUES + plan.get("corrections", []))

    # Titres : par plan ({"plan": 2}) ou en secondes ({"debut": .., "fin": ..}).
    titres = []
    for t in plan.get("titres", []):
        if "plan" in t:
            k = int(t["plan"]) - 1
            s, e = starts[k], starts[k] + durees[k]
            titres.append({"text": t["texte"], "start": round(s + t.get("decalage", 0.15), 3), "end": round(e - 0.1, 3)})
        else:
            titres.append({"text": t["texte"], "start": t["debut"], "end": t["fin"]})

    def to_public(src: Path, name: str) -> str:
        dst = public / name
        if dst.exists():
            dst.unlink()
        safe_copy(src, dst)
        return name

    reveals = []
    for n, r in enumerate(reveals_raw, 1):
        k, p = r["index"], r["plan"]
        s0 = starts[k]
        reveals.append({
            "before": to_public(r["before"], f"avant_{n}{r['before'].suffix.lower()}"),
            "after": to_public(r["after"], f"apres_{n}{r['after'].suffix.lower()}"),
            # Le dernier plan va jusqu'au bout de la vidéo (évite une image « avant » juste avant l'outro).
            "start": round(s0, 3), "end": round(duree if k == len(pieces) - 1 else s0 + durees[k], 3),
            "wipeStart": round(s0 + float(p.get("balayage", 0.7)), 3),
            "wipeDuration": float(p.get("duree_balayage", 1.0)),
            "positionX": p.get("position_x", 0.5), "positionY": p.get("position_y", 0.5),
            "caption": p.get("legende"),
        })

    # Effets sonores « whoosh » (générés ici, libres de droits) à chaque coupe et révélation.
    sfx = []
    if plan.get("effets_sonores", True):
        whoosh = public / "whoosh.wav"
        ffmpeg("-f", "lavfi", "-i", "anoisesrc=color=pink:duration=0.7:amplitude=0.7:sample_rate=48000",
               "-af", "highpass=f=350,lowpass=f=6000,afade=t=in:st=0:d=0.42:curve=exp,"
               "afade=t=out:st=0.42:d=0.28:curve=exp", "-ac", "2", str(whoosh))
        moments = list(cuts) + [r["wipeStart"] + 0.15 for r in reveals] + [duree - 0.2]
        sfx = [{"src": "whoosh.wav", "at": round(max(0.0, m - 0.4), 3), "volume": 0.8} for m in sorted(set(moments))]

    def asset(key: str, folder: str, auto: bool) -> str | None:
        path = plan.get(key)
        if not path and auto:
            found = sorted(glob.glob(str(ROOT / "assets" / marque / folder / "*.*")))
            found = [f for f in found if not f.endswith((".txt", ".pdf", ".md"))]
            path = found[0] if found else None
        if not path:
            return None
        src = Path(path) if Path(path).is_absolute() else ROOT / path
        if not src.exists():
            die(f"{key} introuvable : {path}")
        name = f"{key}{src.suffix.lower()}"
        dst = public / name
        if dst.exists():
            dst.unlink()
        safe_copy(src, dst)
        return name

    props = {
        "brand": marque, "video": "main.mp4", "videoDuration": round(duree, 3), "words": words, "cuts": cuts,
        "hook": plan.get("accroche"), "hookDuration": plan.get("duree_accroche", 2.2), "titles": titres,
        "music": asset("musique", "musiques", auto=False), "musicVolume": plan.get("volume_musique", 0.3),
        "logo": asset("logo", "logos", auto=True), "font": asset("police", "polices", auto=True),
        "colors": plan.get("couleurs"), "reveals": reveals, "sfx": sfx,
        # Sans voix ni musique (effets seuls), on vise plus bas que −14 LUFS.
        "loudness": -14 if (words or plan.get("musique")) else -18,
    }
    (proj / "props.json").write_text(json.dumps(props, ensure_ascii=False, indent=1))
    texte = " ".join(x["text"] for x in words)
    (proj / "sous-titres.txt").write_text(texte + "\n")
    print(f"✔ Vidéo principale : {tc(duree)} — {len(pieces)} plans — {len(words)} mots")
    if words:
        print(f"  Sous-titres à relire : work/{args.projet}/sous-titres.txt")
    print(f"  Paramètres Remotion : work/{args.projet}/props.json")


# ─── rendu ──────────────────────────────────────────────────────────────────
def browser() -> str | None:
    if os.environ.get("REMOTION_BROWSER"):
        return os.environ["REMOTION_BROWSER"]
    found = sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell"))
    return found[-1] if found else None  # sinon Remotion télécharge le sien


def loudnorm(src: Path, dst: Path, lufs: float = -14) -> None:
    target = f"I={lufs}:TP=-1.5:LRA=11"
    res = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"loudnorm={target}:print_format=json",
                          "-f", "null", "-"], text=True, capture_output=True)
    m = json.loads(res.stderr[res.stderr.rindex("{"):])
    if float(m["input_i"]) < -60:  # vidéo muette
        ffmpeg("-i", str(src), "-c", "copy", "-movflags", "+faststart", str(dst))
        return
    af = (f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ffmpeg("-i", str(src), "-af", af, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", str(dst))


def cmd_rendu(args: argparse.Namespace) -> None:
    _, fmt = check_project(args.projet)
    proj = WORK / args.projet
    props = proj / "props.json"
    if not props.exists():
        die("props.json absent : lancer « assembler » d'abord")
    if not (TEMPLATES / "node_modules").exists():
        run(["npm", "ci", "--no-fund", "--no-audit"], cwd=TEMPLATES)
    rendu = proj / "rendu.mp4"
    cmd = ["npx", "remotion", "render", "src/index.ts", FORMATS[fmt][2], str(rendu),
           f"--props={props}", f"--public-dir={proj / 'public'}"]
    if browser():
        cmd.append(f"--browser-executable={browser()}")
    print("▶ rendu Remotion")
    run(cmd, cwd=TEMPLATES)
    EXPORTS.mkdir(exist_ok=True)
    final = EXPORTS / f"{args.projet}.mp4"
    cible = json.loads(props.read_text()).get("loudness", -14)
    print(f"▶ normalisation du son ({cible} LUFS)")
    loudnorm(rendu, final, cible)
    print(f"✔ Export : {final.relative_to(ROOT)}")


# ─── contrôle ───────────────────────────────────────────────────────────────
def cmd_controle(args: argparse.Namespace) -> None:
    _, fmt = check_project(args.projet)
    proj = WORK / args.projet
    video = EXPORTS / f"{args.projet}.mp4"
    if not video.exists():
        die(f"{video.relative_to(ROOT)} absent")
    out = proj / "controle"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    info = probe(video)
    w, h, _ = FORMATS[fmt]
    streams = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(video)], capture=True))
    codecs = sorted({s["codec_name"] for s in streams["streams"]})

    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af", "ebur128=peak=true",
                          "-f", "null", "-"], text=True, capture_output=True).stderr
    summary = res[res.rfind("Summary:"):]
    lufs = re.search(r"I:\s+(-?[\d.]+) LUFS", summary)
    peak = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)

    props = json.loads((proj / "props.json").read_text()) if (proj / "props.json").exists() else {}
    cible = props.get("loudness", -14)
    checks = [
        ("Taille", f"{info['largeur']}×{info['hauteur']}", (info["largeur"], info["hauteur"]) == (w, h)),
        ("Cadence", f"{info['ips']} i/s", abs(info["ips"] - FPS) < 0.05),
        ("Codecs", ", ".join(codecs), codecs == ["aac", "h264"]),
        ("Durée", tc(info["duree"]), True),
        ("Volume intégré", f"{lufs.group(1) if lufs else '?'} LUFS (cible {cible})", bool(lufs) and abs(float(lufs.group(1)) - cible) <= 1.5),
        ("Crête", f"{peak.group(1) if peak else '?'} dBTP", bool(peak) and (peak.group(1) == "-inf" or float(peak.group(1)) <= -1.0)),
    ]

    # Images à regarder : début, accroche, chaque coupe, titres, révélations, fin de la vidéo, outro.
    times = {0.2: "debut", 1.0: "accroche", 2.0: "accroche-fin"}
    for i, c in enumerate(props.get("cuts", []), 2):
        times[c + 0.5] = f"plan{i:02d}"
    for i, t in enumerate(props.get("titles", []), 1):
        times[(t["start"] + t["end"]) / 2] = f"titre{i}"
    for i, r in enumerate(props.get("reveals", []), 1):
        mid = r["wipeStart"] + r["wipeDuration"] / 2
        times[mid] = f"revelation{i}-balayage"
        times[(r["wipeStart"] + r["wipeDuration"] + r["end"]) / 2] = f"revelation{i}-apres"
    main_end = props.get("videoDuration", info["duree"])
    times[max(main_end - 1.0, 0)] = "fin-video"
    times[info["duree"] - 0.6] = "outro"
    images = []
    for t, label in sorted(times.items()):
        if 0 <= t < info["duree"]:
            img = out / f"{t:06.2f}s_{label}.jpg"
            ffmpeg("-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(img))
            images.append(img)
    planche = out / "planche.jpg"
    ffmpeg("-i", str(video), "-vf", f"fps=2,scale={270 if h > w else 384}:-2,tile=8x{max(1, int(info['duree'] * 2 / 8) + 1)}:padding=4",
           "-frames:v", "1", "-q:v", "4", str(planche))

    print(f"Contrôle — {video.name}")
    for name, val, ok in checks:
        print(f"  {'✔' if ok else '✘'} {name} : {val}")
    print(f"  Images à regarder ({len(images)}) : work/{args.projet}/controle/")
    for img in images:
        print(f"    {img.relative_to(ROOT)}")
    print(f"  Planche (2 images/s) : {planche.relative_to(ROOT)}")
    if props.get("words"):
        print("  Sous-titres à relire :")
        print("    " + " ".join(x["text"] for x in props["words"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyse", help="copie, infos, planches, transcription des rushs")
    a.add_argument("rushs")
    a.add_argument("projet")
    a.add_argument("--sans-transcription", action="store_true")
    for name, helptext in [("assembler", "plans → vidéo principale + sous-titres"),
                           ("rendu", "Remotion + son normalisé → exports/"),
                           ("controle", "vérification de l'export")]:
        sub.add_parser(name, help=helptext).add_argument("projet")
    args = ap.parse_args()
    {"analyse": cmd_analyse, "assembler": cmd_assembler, "rendu": cmd_rendu, "controle": cmd_controle}[args.cmd](args)


if __name__ == "__main__":
    main()
