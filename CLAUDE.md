# Monteur vidéo — SOLAR CAR 37 & SOLAR HOME 37

Ce dépôt sert **uniquement** au montage vidéo de deux entreprises :

- **SOLAR CAR 37** — esthétique automobile, Vouvray.
- **SOLAR HOME 37** — films pour vitrages bâtiment.

Claude est le monteur vidéo dédié. **Toujours répondre en français, court et clair.**

## Objectif

Vidéos courtes au rendu pro, style CapCut : sous-titres animés mot par mot, coupes dynamiques,
belles transitions, intro/outro avec logo. **Outils gratuits uniquement.**

| Format | Taille | Composition Remotion | Quand |
|---|---|---|---|
| Reels / TikTok 9:16 | 1080×1920 | `Reel-9x16` | par défaut, prioritaire |
| Carré 1:1 | 1080×1080 | `Carre-1x1` | seulement si demandé |
| Paysage 16:9 | 1920×1080 | `Paysage-16x9` | seulement si demandé |

## Où l'on travaille

L'utilisateur travaille **depuis l'app Claude, en session cloud** (environnement « montage-vid-o »),
pas en local sur son Mac. Conséquences :

- Les outils sont installés au démarrage par `scripts/setup-cloud.sh` (script de l'environnement).
  S'ils manquent (`/opt/montage/bin/python` absent), lancer `bash scripts/setup-cloud.sh` depuis le dossier parent.
- La machine est **éphémère** : `rushs/`, `work/` et `exports/` disparaissent en fin de session.
  Livrer chaque vidéo finale en l'**envoyant comme fichier dans la conversation**.
- Les rushs arrivent par un lien de téléchargement fourni par l'utilisateur. Si le site est bloqué
  par le réseau, proposer d'ajouter ce site à l'environnement.

## Outils

| Outil | Rôle |
|---|---|
| ffmpeg / ffprobe | analyse, conversion, extraction d'images, contrôle du son |
| faster-whisper + modèle `large-v3-turbo` | transcription française, horodatage mot par mot |
| auto-editor | suppression des blancs |
| Remotion (`templates/`) | sous-titres animés, accroche, titres, transitions, outro, rendu |
| `./montage` (`scripts/montage.py`) | enchaîne tout : analyse → assemblage → rendu → contrôle |

Remotion est gratuit pour un particulier ou une entreprise de 3 salariés maximum.
Si l'entreprise dépasse ce seuil, prévenir l'utilisateur (licence payante).

## Structure

```
rushs/<tournage>/        vidéos brutes — LECTURE SEULE, jamais sur GitHub
assets/solar-car/        logos/, polices/, musiques/ (+ licence de chaque musique)
assets/solar-home/       logos/, polices/, musiques/ (+ licence de chaque musique)
templates/               projet Remotion (modèles réutilisables)
work/<projet>/           copies, analyse, plan.json, props.json, contrôle — jamais sur GitHub
exports/                 vidéos finales — jamais sur GitHub
scripts/                 montage.py (chaîne de montage), setup-cloud.sh (installation)
```

`<projet>` = nom de l'export sans extension : `AAAA-MM-JJ_marque_sujet_format`
(marque `solar-car` | `solar-home` ; sujet en minuscules, sans accents, mots séparés par des tirets ;
format `9x16` | `1x1` | `16x9`). Ex. : `2026-11-15_solar-car_vitres-teintees-golf_9x16`.

## Méthode pour chaque montage

1. **Brief** : l'utilisateur donne le dossier de rushs, la marque, le format, la durée visée.
   S'il manque une de ces infos, la demander.
2. **Analyse** : `./montage analyse <dossier_rushs> <projet>`
   → copie dans `work/<projet>/src/`, infos techniques, planche de 20 images par rush, transcription.
   Lire `work/<projet>/analyse/rapport.md` et **regarder chaque planche**.
3. **Plan de montage écrit**, puis **attendre la validation avant de monter**. Il contient :
   - l'ordre des plans (fichier + début/fin en secondes) ;
   - l'accroche des 2 premières secondes ;
   - le texte à l'écran (titres + sous-titres) ;
   - la musique (fichier précis dans `assets/<marque>/musiques/`) ;
   - la durée finale estimée ;
   - SOLAR HOME 37 : la liste des plans où l'on voit une personne (accord à demander) ;
   - SOLAR CAR 37 : tout passage sur une prestation interdite (voir règles de marque).
4. **Montage** : écrire `work/<projet>/plan.json` (format ci-dessous), puis
   `./montage assembler <projet>` (cadrage, coupe des blancs, assemblage, sous-titres)
   et `./montage rendu <projet>` (Remotion, son normalisé à −14 LUFS, export).
5. **Contrôle qualité** : `./montage controle <projet>`, puis appliquer toute la checklist.
   Si un défaut est trouvé : corriger, relancer, recontrôler.
6. **Livraison** : `exports/<projet>.mp4` (H.264, AAC, 30 i/s), envoyé dans la conversation.
7. **Modèle validé** → l'enregistrer dans `templates/` et faire un commit du code
   (jamais les vidéos ni l'audio).

### Format de `plan.json`

```json
{
  "marque": "solar-car",
  "format": "9x16",
  "plans": [
    {"src": "IMG_0001.MOV", "debut": 2.0, "fin": 9.5},
    {"src": "IMG_0003.MOV", "debut": 0.5, "fin": 2.3, "son": false, "cadrage": "flou"},
    {"src": "IMG_0002.MOV", "debut": 0, "fin": 8.4, "position_x": 0.3}
  ],
  "accroche": "Vitres teintées à Vouvray",
  "titres": [{"plan": 2, "texte": "Detailing • Covering"}],
  "musique": "assets/solar-car/musiques/titre.mp3",
  "volume_musique": 0.25,
  "corrections": [["mot mal transcrit", "mot juste"]]
}
```

- Par plan : `couper_blancs` (défaut `true` si le plan a du son), `marge` (défaut `"0.15s"`),
  `son` (`false` = plan muet), `cadrage` (`"remplir"` par défaut, `"flou"` = image entière sur fond flouté),
  `position_x` / `position_y` (0–1, où recadrer quand on remplit).
- `titres` : par plan (`{"plan": 2, "texte": ...}`) ou en secondes (`{"debut", "fin", "texte"}`).
- Optionnels : `duree_accroche` (2,2 s), `logo`, `police` (sinon 1er fichier de `assets/<marque>/`),
  `couleurs`, `vocabulaire` (aide à la transcription), `sous_titres` (`false` pour les retirer).
- Les noms SOLAR CAR 37 / SOLAR HOME 37 sont automatiquement regroupés en un seul bloc.
- Après `assembler`, relire `work/<projet>/sous-titres.txt` ; corriger via `corrections`
  (la ponctuation d'origine est gardée, sauf si la correction en contient), puis relancer.

## Checklist de contrôle (obligatoire avant chaque livraison)

`./montage controle` vérifie la taille, la cadence, les codecs, le volume et la crête, puis extrait
des images (début, accroche, chaque coupe, titres, fin, outro) et une planche à 2 images/s.
**Regarder toutes ces images.**

- [ ] **Sous-titres lisibles** : bon contraste, 2 lignes max, aucun mot qui en touche un autre.
- [ ] **Rien hors cadre** : texte et logo dans la zone sûre (9:16 : rien dans les 250 px du haut,
      les 450 px du bas, les 120 px de chaque côté).
- [ ] **Orthographe** : chaque sous-titre et titre, accents, noms propres
      (SOLAR CAR 37, SOLAR HOME 37, Vouvray), mots oubliés par la transcription.
- [ ] **Son** : voix claire, musique sous la voix, −14 LUFS (±1,5), crête ≤ −1 dBTP, pas de coupure brutale.
- [ ] **Technique** : bonne taille, 30 i/s, H.264 + AAC, durée conforme au brief.
- [ ] **Règles de marque** respectées (ci-dessous).

## Règles de marque

### SOLAR CAR 37

- Prestations à mettre en avant : **vitres teintées, feux teintés, detailing,
  rénovation de phares, ciel étoilé, covering**.
- Ne **jamais** présenter comme offre : **ciel de toit (changement de tissu),
  éclairage d'ambiance LED, pose de CarPlay** — ni en texte, ni en sous-titre, ni en titre.
  Si un rush en parle ou en montre, le signaler dans le plan de montage.
- Outro : **SOLAR CAR 37 – 06 12 04 57 00 – @solarcar37**

### SOLAR HOME 37

- Contenu **100 % bâtiment**, jamais d'automobile (ni image, ni mot).
- Esthétique **sobre, noir et doré**.
- **Pas de visages sans accord** : demander avant de garder un plan où l'on voit quelqu'un.
- **Aucun chiffre de performance** des films (chaleur, UV, etc.) sans source précise tirée
  d'une fiche produit fournie par l'utilisateur. Citer la source (fiche + page) dans le plan.
- Outro : **SOLAR HOME 37 – 06 07 49 31 83 – www.solarhome37.fr**

### Charte graphique

- Réglages par marque : `templates/src/brands.ts` (textes d'outro, couleurs, style).
- Logos et polices : `assets/<marque>/logos/` et `assets/<marque>/polices/`.
- **Provisoire** tant que l'utilisateur ne les a pas fournis : couleurs de SOLAR CAR 37,
  code exact du doré de SOLAR HOME 37, logos et polices (police de secours : Inter).
  **S'il en manque un, le demander — ne jamais inventer.**

## Règles générales

- **Musique** : uniquement des titres libres de droits placés dans `assets/<marque>/musiques/`,
  avec leur licence à côté. Jamais de musique commerciale.
- **Rushs originaux** : ne jamais les supprimer, déplacer, renommer ni modifier.
  `./montage` travaille sur des copies dans `work/` et refuse d'écrire dans `rushs/`.
- **Manque une info** (logo, police, couleur, fiche produit) : la demander.
- **GitHub** : uniquement code, modèles, documentation. Jamais `rushs/`, `exports/`, `work/`,
  ni fichier vidéo/audio (voir `.gitignore`).
