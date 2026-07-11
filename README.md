# Agent Social Media - bmdesign.ro

Modulul 1: Programator de postari + calendar de continut, automatizat, fara server (ruleaza pe GitHub Actions, gratuit).

## Ce face acum

1. Verifica periodic un folder de Google Drive pentru randari noi.
2. 2. Le adauga automat intr-un calendar de continut (rotind prin 5 piloni tematici).
   3. 3. Genereaza un caption in romana, in stilul tau (storytelling, CTA prin comentarii).
      4. 4. Posteaza automat pe Instagram, la interval de 2 zile (configurabil).
         5. 5. Salveaza tot progresul in data/calendar.json, versionat in repo.
           
            6. ## Module viitoare
           
            7. - Generare de imagini noi/variatii pornind de la randarile tale (Nano Banana Pro).
               - - Detectare si raspuns automat la comentarii/DM-uri cu intentie de lead.
                 - - Formular de contact/oferta pentru leaduri.
                  
                   - ## Setup
                  
                   - ### 1. Instagram + Meta App Review
                  
                   - 1. Cont Instagram Business/Creator, legat de o Pagina de Facebook.
                     2. 2. Cont pe developers.facebook.com, creezi o aplicatie Business.
                        3. 3. Adaugi produsul Instagram Graph API.
                           4. 4. Ceri permisiunile instagram_business_basic, instagram_business_manage_comments, instagram_business_manage_messages.
                              5. 5. Adaugi contul de Instagram ca Instagram Tester (Roles tab), accepti invitatia pe instagram.com/accounts/manage_access/ (tab Invitatii testeri).
                                 6. 6. Generezi access token-ul din API Setup.
                                    7. 7. Pentru productie (dincolo de contul tau), e nevoie de App Review.
                                      
                                       8. ### 2. Google Drive
                                      
                                       9. 1. Google Cloud Console, proiect nou, activezi Google Drive API.
                                          2. 2. Creezi un Service Account, descarci cheia JSON.
                                             3. 3. Partajezi folderul de Drive cu adresa de email a Service Account-ului.
                                                4. 4. Iei ID-ul folderului din URL.
                                                  
                                                   5. ### 3. Claude API
                                                  
                                                   6. Cont pe console.anthropic.com, generezi un API key.
                                                  
                                                   7. ### 4. GitHub Secrets
                                                  
                                                   8. In repo, Settings > Secrets and variables > Actions, adaugi:
                                                  
                                                   9. - IG_ACCESS_TOKEN
                                                      - - IG_BUSINESS_ACCOUNT_ID
                                                        - - GDRIVE_FOLDER_ID
                                                          - - GDRIVE_SERVICE_ACCOUNT_JSON (continutul fisierului JSON, ca text)
                                                            - - ANTHROPIC_API_KEY
                                                             
                                                              - ### 5. Testare
                                                             
                                                              - Din tab-ul Actions, ruleaza manual workflow-ul (Run workflow) ca sa testezi.
                                                             
                                                              - ## Structura
                                                             
                                                              - - scripts/scheduler.py - orchestratorul principal
                                                                - - scripts/content_calendar.py - gestionare calendar (JSON)
                                                                  - - scripts/google_drive.py - preluare randari din Drive
                                                                    - - scripts/caption_generator.py - generare caption-uri (Claude)
                                                                      - - scripts/instagram_publisher.py - publicare + comentarii (Graph API)
                                                                        - - data/calendar.json - starea calendarului
                                                                          - - .github/workflows/scheduler.yml - rulare automata (cron)
                                                                           
                                                                            - ## Ajustari rapide
                                                                           
                                                                            - - Frecventa postarilor: POSTING_INTERVAL_DAYS in scheduler.py
                                                                              - - Orele de rulare: valorile cron din scheduler.yml (UTC)
                                                                                - - Pilonii de continut: CONTENT_PILLARS in content_calendar.py
                                                                                  - 
