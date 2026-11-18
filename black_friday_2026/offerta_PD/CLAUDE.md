# Campagna email Black Friday 2026 · Studio Mobilitas

Qui si costruiscono le 5 email HTML della campagna. I testi arrivano già approvati, uno per prompt. Il tuo lavoro è impaginarli e controllarli, non scriverli.

## Regola numero uno: il testo non si tocca
- Copia i testi del prompt parola per parola: stessa punteggiatura, stesse maiuscole, stessi simboli (450€, 900€, 23:59).
- Non correggere, non accorciare, non aggiungere titoli, etichette, frasi di raccordo o emoji.
- Le indicazioni tra parentesi quadre nei prompt ([RIQUADRO], [PULSANTE]...) servono per l'impaginazione: non vanno nel testo.
- Se un testo ti sembra sbagliato, fermati e chiedimelo. Non sistemarlo da solo.
- Gli unici testi fissi che non arrivano dal prompt sono il footer e il testo alternativo del logo, scritti qui sotto.

## Lo studio
- Studio Mobilitas, studio di osteopatia a Torino. Due sedi: Via Peyron 54 e Via Lamarmora 35. Sito: www.studiomobilitas.it
- Mittente e firma delle email: Studio Mobilitas.
- Telefono: +39 351 819 8457 (lunedì–venerdì 8:00–21:00, sabato 9:00–18:00; la domenica è chiuso). Email: studio@studiomobilitas.it
- Cosa ci rende diversi: un osteopata specializzato per ogni dolore; un trattamento di un'ora intera; solo le mani (niente pastiglie, niente punture, niente cuscini miracolosi).
- Tono: del tu, frasi corte e parlate, empatico ma diretto. Niente maiuscole urlate, niente emoji, niente toni da televendita. Mai promettere guarigioni o risultati garantiti.

## Chi riceve le email
Pazienti ed ex pazienti. Ci conoscono già: ogni email è una lettera dello studio che li ha seguiti.

## L'offerta (l'unica di questa campagna)
- Dieci visite a 450€. Si paga online sulla landing page (LP).
- Formula ufficiale: "10 visite: ne paghi 5, le altre 5 sono in omaggio." · "450€ invece di 900€" · "a metà prezzo".
- 900€ = 10 visite × 90€, il prezzo di una visita singola.
- È un pacchetto creato solo per il Black Friday: durante l'anno non esiste.
- Scadenza: domenica 29 novembre 2026, ore 23:59.
- Dopo il pagamento il paziente prenota le visite da solo, oppure chiama il +39 351 819 8457.
- Nelle email non compaiono MAI: porta un amico, 49€, COUPON49, rate, bonus app, "11 visite", "visita in più", "percorso".

## Calendario (tutte alle 19:30, ora italiana)
| Email | Data | Angolo |
| --- | --- | --- |
| 1 | giovedì 19 novembre 2026 | Lancio: il Black Friday delle cose inutili |
| 2 | lunedì 23 novembre 2026 | Prevenzione |
| 3 | mercoledì 25 novembre 2026 | Problema non ancora risolto del tutto |
| 4 | venerdì 27 novembre 2026 (Black Friday) | Volevi fare più visite, ma costava troppo |
| 5 | domenica 29 novembre 2026 | Scadenza: ultime ore |

## File e cartelle
- config.json: tutti i dati che possono cambiare (piattaforma, tag, mittente, link LP, logo, contatti). I valori mancanti sono segnaposto [[DA_COMPILARE: ...]]: non inventarli mai.
- template/base.html: il template, uguale per tutte le email.
- content/: un file per email con il testo approvato diviso in blocchi. Formato a tua scelta (es. JSON), con: numero, data e ora di invio, oggetto, oggetto alternativo, preheader, blocchi in ordine, versione solo testo, testi obbligatori per il controllo.
- build.py (o build.js): compone l'email, aggiunge le UTM, fa i controlli.
- emails/: output finale. Nomi: emails/BF2026_email_<numero>_<AAAA-MM-GG>.html e .txt (es. emails/BF2026_email_1_2026-11-19.html).

## Blocchi disponibili
saluto · paragrafo · riquadro (offerta) · pulsante · nota (riga piccola sotto il pulsante) · chiusura · firma · ps.
Il file di contenuto li elenca nell'ordine in cui compaiono. Al massimo 2 pulsanti per email (di solito 1).

## Estetica
Riferimento: il sito www.studiomobilitas.it (Montserrat, blu notte, pulsanti a pillola). L'email però resta CHIARA: sfondo bianco di default, perché Gmail e Poste gestiscono male gli sfondi scuri. Niente fasce blu notte a tutta larghezza. Deve sembrare una lettera dello studio, non un volantino: pochi elementi, tanto spazio, testo grande.

Ordine fisso dall'alto: preheader nascosto → logo a sinistra → linea sottile azzurra → blocchi dell'email → footer su fascia grigio chiaro.

Colori del brand (tienili tutti in un solo punto del template o dello script):
- bianco #FFFFFF: sfondo dell'email;
- blu notte #002552: testo, link, testo del pulsante;
- grigio chiaro #F4F4F4: sfondo del riquadro e della fascia del footer, linea sopra il P.S.;
- corallo #FA7272: SOLO sfondo del pulsante (è l'unica azione);
- azzurro #72B1FA: linea sotto il logo e bordo sinistro del riquadro;
- grigio-blu #4A5F7A (tinta ricavata dal blu notte): testo secondario e prezzo barrato.
Corallo e azzurro non si usano mai per scrivere su bianco: si leggono male.

Dark mode (solo un adattamento; la versione di riferimento è quella chiara): con prefers-color-scheme: dark → sfondo #002552, testo #F4F4F4, testo secondario #B8C4D4, riquadro #0B3366 con bordo #72B1FA, fascia footer #0B3366, pulsante invariato (corallo con testo blu notte), logo da logo_url_dark. Nei client che invertono i colori da soli (Gmail app) non forzare nulla.

Caratteri: Montserrat da Google Fonts (un <link> con i pesi 400, 700, 800, 900), con riserva Arial, Helvetica, sans-serif. In Outlook desktop forza Arial con un blocco condizionale mso. Dove Montserrat non carica (Gmail), l'email deve restare bella con Arial.

Blocchi:
- saluto e paragrafo: 16px, interlinea 1.65, 18px di spazio sotto. Mai più piccoli su telefono.
- riquadro: sfondo #F4F4F4, bordo sinistro 4px #72B1FA, padding 20px 22px, angoli 8px, 24px di spazio sopra e sotto. Riga 1: grassetto 700, 17px. Riga 2: il primo prezzo in Montserrat 900, 32px; "invece di" 16px normale; il secondo prezzo 16px barrato in #4A5F7A (il testo resta identico). Riga 3: 14px, #4A5F7A.
- pulsante: fatto in HTML (tabella + link), mai un'immagine. A pillola come sul sito: sfondo #FA7272, testo #002552, Montserrat 800, 16px, padding 16px 28px, angoli 30px, area di tocco di almeno 48px. Centrato su computer, a larghezza piena su telefono (se va a capo su due righe va bene). Versione VML per Outlook desktop. 24px di spazio sopra e sotto.
- nota: 14px, #4A5F7A, centrata. Il telefono è un link tel: in blu notte, sottolineato.
- chiusura: come un paragrafo.
- firma: "Studio Mobilitas" in grassetto 700.
- ps: 15px, "P.S." in grassetto, separato da una linea #F4F4F4 di 2px con 24px di spazio sopra.
- footer: fascia #F4F4F4 a tutta larghezza sotto il contenuto, padding 24px, testo 12px #4A5F7A centrato, interlinea 1.6.

Layout: larghezza massima 600px, fluida al 100% sotto i 600px. Padding laterale 32px (20px sotto i 480px). 32px di spazio sopra il logo.
Logo: logo_url, larghezza logo_larghezza_px, altezza automatica. alt="Studio Mobilitas", con stile (blu notte, grassetto, 18px), così si legge anche con le immagini bloccate.

## Regole tecniche
- Layout solo con tabelle (role="presentation") e CSS in linea su ogni elemento. Nel <head> solo il link del font, il CSS delle media query (telefono e dark mode) e i reset dei client email.
- <html lang="it">, meta charset UTF-8, meta viewport, <title> uguale all'oggetto dell'email.
- Dark mode: meta color-scheme e supported-color-schemes "light dark"; @media (prefers-color-scheme: dark) con classi e !important; selettori [data-ogsc] e [data-ogsb] per Outlook.com.
- Preheader nascosto (display:none; max-height:0; overflow:hidden; mso-hide:all), seguito da caratteri di riempimento (&zwnj;&nbsp; ripetuti), così nell'anteprima della casella non compare altro testo.
- Ogni immagine ha il testo alternativo. Se c'è logo_url_dark, in dark mode usa quello.
- Blocca il riconoscimento automatico di telefoni, date e indirizzi su iOS (meta format-detection e regola a[x-apple-data-detectors]): l'unico numero cliccabile è quello con il link tel:.
- Link sottolineati, in blu notte; target="_blank" sui link alla LP.
- Niente immagini in base64, niente JavaScript, niente form. L'unico font esterno è Montserrat.
- Peso dell'HTML sotto i 100 KB: sopra i 102 KB Gmail taglia l'email.
- Il .txt è testo semplice UTF-8, con i link per esteso.

## Link e UTM
- Ogni link verso la LP: link_lp + utm_source=email&utm_medium=email&utm_campaign=bf2026&utm_content=email_<numero>. Se link_lp contiene già "?", unisci con "&".
- Telefono cliccabile: tel:+393518198457.
- Disiscrizione obbligatoria in ogni email, con il tag della piattaforma (config.json).

Tag delle piattaforme più comuni (verifica sempre nella documentazione, anche come gestiscono il nome mancante):
- Brevo: nome {{ contact.FIRSTNAME }} · disiscrizione {{ unsubscribe }}
- Mailchimp: nome *|FNAME|* · disiscrizione *|UNSUB|*
- ActiveCampaign: nome %FIRSTNAME% · disiscrizione %UNSUBSCRIBELINK%
Se il nome manca, il saluto deve diventare "Ciao," e mai "Ciao ,".

## Footer (testo fisso, uguale in tutte le email)
Studio Mobilitas · Osteopatia a Torino
Via Peyron 54 · Via Lamarmora 35
Tel. +39 351 819 8457 · studio@studiomobilitas.it
P.IVA 13020400019
Ricevi questa email perché ti abbiamo seguito in studio.
Non vuoi più ricevere le nostre email? Disiscriviti qui.
("Disiscriviti qui" è il link di disiscrizione; telefono ed email sono cliccabili. Nel .txt il footer va in fondo, con il link di disiscrizione per esteso.)

## Script di build
Comando: python3 build.py <numero> (oppure node build.js <numero>).
1. Legge config.json, template/base.html e il file dell'email in content/.
2. Compone l'HTML blocco per blocco, nell'ordine del file di contenuto.
3. Crea il link della LP con le UTM (vedi "Link e UTM").
4. Scrive emails/BF2026_email_<numero>_<AAAA-MM-GG>.html e .txt.
5. Fa i controlli qui sotto e stampa un report OK / AVVISO / ERRORE.
6. Stampa il riepilogo per la piattaforma: oggetto, oggetto alternativo (se c'è), preheader, mittente, data e ora di invio, percorsi dei file.

## Controlli
- Peso dell'HTML: ERRORE sopra i 100 KB, AVVISO sopra i 90 KB.
- Parole vietate (maiuscole o minuscole): "porta un amico", "COUPON49", "49€", "49 euro", "rate" (parola intera), "155€", "465€", "bonus", "app" (parola intera), "11 visite", "visita in più", "percorso", "garantit", "guarigione". Anche una sola: ERRORE.
- Testi obbligatori indicati nel prompt dell'email: se ne manca uno, ERRORE.
- Testo identico: ogni blocco del file di contenuto deve comparire identico nel testo visibile dell'HTML (senza tag, spazi normalizzati) e nel .txt. Altrimenti ERRORE.
- Link alla LP: tutti con le 4 UTM e l'utm_content giusto; massimo 2 pulsanti. Altrimenti ERRORE.
- Immagini senza testo alternativo: ERRORE.
- Emoji: ERRORE.
- Preheader o link di disiscrizione mancanti: ERRORE.
- Segnaposto [[DA_COMPILARE...]] ancora presenti: AVVISO, con l'elenco. Il file si genera lo stesso, ma non è pronto per l'invio.
Se c'è un ERRORE, correggi l'impaginazione o lo script, mai il testo approvato.

## Dopo ogni build
1. Apri l'anteprima dell'HTML nel browser (open su Mac, start su Windows). Se hai uno strumento per gli screenshot, guardala anche a 375px di larghezza e in dark mode.
2. Confronta con il prompt: prezzi, date, ora, link della LP con le UTM, telefono, testo parola per parola, numero di pulsanti.
3. Dammi il riepilogo per la piattaforma e l'elenco dei segnaposto ancora da compilare.
