# Agent Social Media - bmdesign.ro

Programator de postari automate: postari simple, carusele si Stories, cu generare de variatii de imagine (Nano Banana Pro) si caption-uri (Claude). Ruleaza pe GitHub Actions, gratuit, fara server.

## Structura folderului de Google Drive

```
bmdesign-social-agent/          (folderul partajat cu Service Account-ul)
|-- [imagini direct aici]        -> postari simple, o imagine per postare
|-- carusele/
|   |-- proiect-x/               -> un subfolder = un carusel (2-10 imagini)
|   |-- proiect-y/
|-- stories/
    |-- [imagini aici]           -> postate ca Instagram Stories (fara caption)
```

- Fiecare imagine/subfolder e procesat o singura data (nu se repeta postarile).
- Un subfolder din carusele/ trebuie sa aiba minim 2 imagini ca sa fie preluat.
- Poti incarca oricate imagini/subfoldere deodata, agentul le programeaza eșalonat.

## Piloni tematici (postari simple + carusele)

Informativi, orientati spre trafic si leaduri (nu before/after):

1. Sfat practic
2. Spotlight material
3. Din culise / proces
4. Mit vs. realitate
5. Invitatie la proiect

## Setup

### 1. Instagram + Meta App Review

1. Cont Instagram Business/Creator, legat de o Pagina de Facebook.
2. Cont pe developers.facebook.com, creezi o aplicatie Business.
3. Adaugi produsul Instagram API (Manage messaging & content on Instagram).
4. Ceri permisiunile instagram_business_basic, instagram_business_manage_comments, instagram_business_manage_messages.
5. Adaugi contul de Instagram ca Instagram Tester (Roles tab), accepti invitatia pe instagram.com/accounts/manage_access/ (tab Invitatii testeri).
6. Generezi access token-ul din API Setup (foloseste graph.instagram.com, nu graph.facebook.com).

### 2. Google Drive

1. Google Cloud Console, proiect nou, activezi Google Drive API.
2. Creezi un Service Account, descarci cheia JSON.
3. Creezi folderul de Drive cu subfolderele carusele/ si stories/ in interior.
4. Partajezi folderul principal cu adresa de email a Service Account-ului (Viewer).
5. Iei ID-ul folderului principal din URL.

### 3. Claude API si OpenRouter

- console.anthropic.com -> API key + credit adaugat (Plans & Billing).
- openrouter.ai/keys -> API key (pentru Nano Banana Pro).

### 4. GitHub Secrets

In repo, Settings > Secrets and variables > Actions:

- IG_ACCESS_TOKEN
- IG_BUSINESS_ACCOUNT_ID
- GDRIVE_FOLDER_ID
- GDRIVE_SERVICE_ACCOUNT_JSON
- ANTHROPIC_API_KEY
- OPENROUTER_API_KEY

### 5. Testare

Din tab-ul Actions, ruleaza manual workflow-ul scheduler.yml (Run workflow).

## Structura proiectului

- scripts/scheduler.py - orchestratorul principal (3 tipuri de continut)
- scripts/content_calendar.py - gestionare calendar (JSON)
- scripts/google_drive.py - preluare postari simple, carusele, stories din Drive
- scripts/caption_generator.py - generare caption-uri (Claude)
- scripts/image_generator.py - generare variatii de imagine (Nano Banana Pro)
- scripts/instagram_publisher.py - publicare imagine/carusel/story + comentarii
- data/calendar.json - starea calendarului
- .github/workflows/scheduler.yml - rulare automata (cron, 2x/zi)

## Ajustari rapide

- Frecventa postarilor: POSTING_INTERVAL_DAYS in scheduler.py
- Orele de rulare: valorile cron din scheduler.yml (UTC)
- Pilonii de continut: CONTENT_PILLARS in content_calendar.py + PILLAR_ANGLES in caption_generator.py
