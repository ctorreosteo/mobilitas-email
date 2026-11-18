# Campagna email Black Friday 2026 · Studio Mobilitas

Qui si costruiscono le 5 email HTML della campagna. I testi arrivano già approvati, uno per prompt. Il tuo lavoro è impaginarli e controllarli, non scriverli.

## Regola numero uno: il testo non si tocca
- Copia i testi del prompt parola per parola: stessa punteggiatura, stesse maiuscole, stessi simboli (450€, 900€, 23:59).
- Non correggere, non accorciare, non aggiungere titoli, etichette, frasi di raccordo o emoji.
- Le indicazioni tra parentesi quadre nei prompt ([RIQUADRO], [PULSANTE]...) servono per l'impaginazione: non vanno nel testo.
- Se un testo ti sembra sbagliato, fermati e chiedimelo. Non sistemarlo da solo.
- Gli unici testi fissi che non arrivano dal prompt sono il footer, il testo alternativo del logo e le scritte grafiche della testata Black Friday (config.json → "testata": EDIZIONE UNICA 2026 · OSTEOPATIA · TORINO · Black Friday · timbro "A METÀ −50% PREZZO" · VISITE 10, ne paghi 5 · PREZZO 450€ invece di 900€ · SCADENZA 29.11 · ore 23:59 · striscia BLACK FRIDAY · −50%). Sono uguali in tutte le email; si cambiano solo in config.json, o per una singola email con "testata" nel file di contenuto.

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
saluto · paragrafo (anche "stile": "evidenza") · elenco ("motivi" o "passi") · confronto (PRIMA / OGGI) · box (metafora, verde chiaro) · riquadro (offerta, scuro o "stile": "chiaro") · pulsante · nota (riga piccola sotto il pulsante) · chiusura · firma · ps.
Il file di contenuto li elenca nell'ordine in cui compaiono. Al massimo 2 pulsanti per email (di solito 1). Le 5 email devono essere tutte DIVERSE tra loro, dentro lo stesso stile del sito: cambia la variante della testata, la combinazione dei blocchi e la versione del biglietto (scuro / chiaro). Restano uguali colori, font, pulsante verde con freccia, P.S. corto e footer, così la campagna si riconosce. Le metafore e gli angoli delle ads non si ripetono da un'email all'altra.
- Email 1: testata "Black Friday" grande · motivi (01-03) · biglietto scuro · passi · nota con scadenza.
REGOLA DI CHIAREZZA: chi apre l'email deve capire SUBITO che è l'offerta Black Friday, come nell'email 1. Ogni email apre con un BANNER BLACK FRIDAY grande (scritta "Black Friday", −50%, dati essenziali dell'offerta, striscia "BLACK FRIDAY • −50%"), poi il titolo dell'email sul bianco, poi la lettera. Grafiche semplici ed efficaci: un banner, una o due card, il biglietto dell'offerta, un solo pulsante. Niente elementi che vanno spiegati (numeri senza contesto, barre "SEI QUI", troppe pillole/etichette). Ogni banner ha una sua versione, così le email restano diverse ma della stessa famiglia.
- Email 1: tema "chiaro", testata "Black Friday" scura con timbro −50% e riga dati · motivi 01-03 · biglietto scuro · passi.
- Email 2: tema "bianco", testata "variante": "banner", "banner": "nero" (−50% enorme verde a sinistra, "Black Friday" e i dati a destra, striscia verde) · titolo a sinistra con evidenziatore · lettera · box del tagliando · biglietto chiaro.
- Email 3: tema "centro", testata "variante": "banner", "banner": "verde", "allinea": "centro" (banner verde del sito con "Black Friday" blu notte, bollino blu notte "A METÀ −50% PREZZO", dati su una riga, striscia blu notte) · titolo centrato con evidenziatore · lettera · box "spiegazione" e "bastone" · offerta "intestata".
Banner: effetto RILIEVO e NERO Black Friday, sempre. Costanti in build.py: NERO_BF #000611 (il nero del sito) per fondi, strisce e bollini; RILIEVO_BIANCO / RILIEVO_VERDE / RILIEVO_NERO per le scritte grandi (ombre a strati, effetto estruso; il verde ha anche il bagliore come i prezzi del sito); OMBRA_BANNER per far staccare il banner dalla pagina; BOLLINO_BIANCO_3D / BOLLINO_NERO_3D per timbri e bollini. Ogni banner ha almeno un elemento nero ben visibile (fondo, striscia o bollino). I titoli sotto il banner hanno l'EVIDENZIATORE con la sfumatura verde → azzurro cielo #38BDF8 dei titoli del sito. Niente testo sfumato o contornato (background-clip:text, text-stroke): in Gmail il testo sparirebbe.
- Email 4 (venerdì 27, il giorno del Black Friday): offerta con riquadro "stile": "prezzi" (due tessere affiancate: DI SOLITO 900€ barrato in crema → freccia → BLACK FRIDAY 450€ su tessera nera; campi "prima" e "dopo" [etichetta, prezzo, sotto]) al posto dello scontrino. tema "bianco", "banner": "calendario" (banner nero con foto, foglio di calendario in rilievo "NOVEMBRE / 27 / VENERDÌ", "OGGI È IL / Black Friday", pillola verde −50%, striscia bianca bordata di nero) · titolo "Oggi, per una volta, / vieni prima tu." · foto nella lettera · box "stile": "macchia" (campi intro, subito, aspetti, chiusura: punto verde "se la lavi subito", macchia nera "se aspetti", chiusura su fascia nera) · riquadro "stile": "scontrino" (il conto: "conto" [[voce, importo] ×2], "totale", poi totale 450€ enorme, "450€ invece di 900€", cerchi delle visite, scadenza su fascia nera). È l'unica email che rifà il conto 900 → 450.
- Email 5 (domenica 29, ultime ore): tema "centro", "banner": "orologio" (banner nero con foto, pillola verde ULTIMO GIORNO, DOMENICA 29 NOVEMBRE, orologio a tessere in rilievo 23:59 con i due punti verdi luminosi, striscia verde "ULTIME ORE • BLACK FRIDAY • −50%") · titolo centrato "Ultime ore. / Stasera alle 23:59 finisce." · foto · evidenza · elenco "motivi" con i tre motivi delle email precedenti · biglietto scuro · nota SENZA telefono (domenica lo studio è chiuso).
BENEFICI POLARIZZANTI (email 1–4): blocco {"tipo": "benefici", "etichetta", "titolo" facoltativo, "voci": [[no, sì, spiegazione] ×3]}: "no" barrato in grigio, "sì" in grassetto con evidenziatore verde → cielo, spiegazione sotto. Ogni email ha benefici legati al suo angolo (1: cosa ti porti a casa, ora intera, solo mani, specialista · 2: anticipare il dolore, non ricominciare da capo, dire di sì · 3: arrivare in fondo, nuove abitudini, stare bene davvero · 4: oggi non il mese prossimo, prima di tutto il resto, 450€ una volta sola). Mai promettere guarigioni o risultati.
NOTA COPY: nell'email 4 «una rata ancora da pagare» è una spesa del paziente (come nel video già approvato) e NON va tolta. Il controllo blocca solo la parola intera "rate", non "rata".
Con il banner la fascia in alto e la pillola "BLACK FRIDAY 2026" del template spariscono da sole (sarebbero ripetizioni). Campi del banner in "testata": banner, titolo_bf ("Black Friday"), dati_bf [3 righe brevi], titolo (righe con "|"), allinea; sconto e striscia arrivano da config.json.
FOTO DI TRATTAMENTO: in ogni email una foto come sfondo del banner ("testata": "sfondo_foto" = URL, "sfondo_posizione" = es. "70% center") e una foto dentro la lettera (blocco {"tipo": "immagine", "url": ..., "alt": ..., "didascalia" facoltativa}). Usare SOLO le foto già ottimizzate del sito, sul dominio dello studio (60–130 KB): https://www.studiomobilitas.it/trattamenti/og/*.jpg (1200×630), /trattamenti/web/*-1600.jpg, /home/web/home2-1600.jpg, /home/web/home5-1600.jpg. Mai le foto originali su mcusercontent.com (6–7 MB l'una, e dipendono dal vecchio account Mailchimp). Foto diverse in ogni email. Sotto la foto del banner c'è sempre un velo di colore (nero nei banner scuri, verde nel banner verde) che tiene leggibili le scritte; se il client non carica le immagini di sfondo resta il colore pieno. Ogni immagine ha un testo alternativo descrittivo.
Foto usate: email 1 banner /home/web/home2-1600.jpg, lettera /trattamenti/og/collo_presa-cervicale-supino_18_orizzontale.jpg · email 2 banner /trattamenti/web/schiena_lombare-prono_14_orizzontale-1600.jpg, lettera /trattamenti/og/collo_presa-cervicale-supino_26_orizzontale.jpg · email 3 banner /trattamenti/web/schiena_lombare-supino_01_orizzontale-1600.jpg, lettera /trattamenti/og/anca_flessa-supino_07_orizzontale.jpg.

SFONDO SEMPRE BIANCO: tutte le email hanno fondo bianco (richiesta esplicita dello studio). Il blu notte si usa solo dentro card e blocchi, mai come fondo dell'email.

Temi ("tema" nel file di contenuto):
- "chiaro" (predefinito, template/base.html): card bianca su fondo grigio-azzurro, testata scura in un riquadro, adattamento dark mode.
- "bianco" (template/bianco.html): fondo bianco pieno, testata editoriale direttamente sulla pagina, resta chiara anche in dark mode (color-scheme: light). Testata: "testata" con etichetta, titolo (righe separate da "|": la prima blu notte, le altre blu notte con evidenziatore verde), numeri [[valore, etichetta], ...].
- Varianti della testata nei temi "bianco" e "centro": "sintesi" (campi: etichetta, titolo, sintesi [[etichetta, valore, sotto, ("barrato")], ...], pulsante) e "traguardo" (campi: etichetta, titolo, tappe [[etichetta, testo] ×3], pulsante, sintesi_riga). Il pulsante della testata conta nei 2 pulsanti ammessi.
- "centro" (template/centro.html): come "bianco" ma tutto centrato, fascia scura in alto, logo centrato. "testata": fascia [voci], pillola, etichetta, titolo (righe con "|"), avanzamento (percentuale della barra), barra_qui / barra_inizio / barra_fine, numeri. Blocchi in più: box con "stile": "spiegazione" o "bastone" (righe separate da "\n"), riquadro con "stile": "intestato".
- "notte" (template/notte.html): versione tutta scura. NON usarla: lo studio vuole lo sfondo bianco.
Titoli e oggetti devono essere polarizzanti e creare curiosità, senza promettere risultati.
Copy: partire sempre dagli angoli e dalle frasi delle ads Meta dello studio (tagliando della macchina, macchia sul vestito, il corpo che impara a stare teso, «ti ricordi com'era prima?», il dolore che torna più forte, non ricominciare da capo, dire di sì a cena/passeggiata/weekend). Chi riceve ha già fatto visite da noi: mai parlargli come a chi non ci conosce.

## Estetica
Riferimento: il sito www.studiomobilitas.it (colori e branding) e le email precedenti dello studio (black_friday_2026/Donna e Uomo). Dal sito: Montserrat, fondo inchiostro/blu notte, verde menta come colore d'azione, etichette maiuscole con trattino verde davanti, pulsanti a pillola verdi con testo blu notte e cerchio con la freccia, bagliori verdi sulle card scure. Dalle email: card bianca arrotondata su fondo grigio-azzurro, card con ombre morbide, numeri grandi chiari. L'impronta Black Friday è forte, ma il testo resta una lettera dello studio: niente toni da televendita.

Ordine fisso dall'alto: preheader nascosto → pagina grigio-azzurra con card bianca arrotondata (600px) → logo centrato → testata Black Friday → blocchi dell'email → footer centrato sotto la card.

Testata Black Friday (stessa struttura in tutte le email; il file di contenuto può cambiarne i testi con "testata", e "variante": "frase" sostituisce "Black Friday" con una frase su due righe separate da "|", bianca e verde, 46px, con il timbro nascosto su telefono; generata dallo script con i testi di config.json → "testata"): fondo dall'inchiostro #000F2B al blu notte con bagliori; in alto etichetta a pillola "EDIZIONE UNICA 2026" e, a destra, "OSTEOPATIA · TORINO"; "Black" bianco e "Friday" verde in Montserrat 900 (76px, 50px su telefono) con due trattini sotto; timbro ruotato (anello tratteggiato verde, cerchio bianco "A METÀ / −50% / PREZZO"); riga dati VISITE · PREZZO · SCADENZA (PREZZO nascosto su telefono: in config un dato con "solo_computer" sparisce sotto i 480px); striscia verde "BLACK FRIDAY • −50%" in fondo.

Colori: tutti in COLORI dentro build.py (unico punto), presi dal sito.
- pagina #EEF2F7; card #FFFFFF con bordo #E3EAF2, angoli 22px, ombra leggera;
- blu notte #002552: testo, link, testo del pulsante; inchiostro #000F2B e #0B3366 per le sfumature scure;
- verde menta #72FA93 (il verde del sito e del logo): sfondo del pulsante e accenti (Friday, timbro, striscia, trattini delle etichette, barra della frase in evidenza, trattino della firma, cerchi "in omaggio", scadenza nel biglietto). Come testo SOLO su fondo scuro: su bianco non si legge;
- crema #F4F4F4: card "cosa fare adesso";
- grigio-blu #4A5F7A: testo secondario su chiaro; #B8C4D4: testo secondario su scuro e prezzo barrato;
- #F4F8FC: box del P.S.
Corallo e azzurro non si usano più.

Dark mode (adattamento; la versione di riferimento è quella chiara): pagina #00142F, card #002552, testo #F4F4F4, secondario #B8C4D4, card interne #0B3366, logo da logo_url_dark. Testata, biglietto e pulsante restano come sono. Nei client che invertono i colori da soli (Gmail app) non forzare nulla.

Caratteri: Montserrat da Google Fonts (un <link> con i pesi 400, 700, 800, 900), con riserva Arial, Helvetica, sans-serif. In Outlook desktop forza Arial con un blocco condizionale mso. Dove Montserrat non carica (Gmail), l'email deve restare bella con Arial. Sfumature, ombre e angoli arrotondati sono un miglioramento: sotto c'è sempre un colore pieno di riserva (Outlook desktop li ignora).

Blocchi:
- saluto e paragrafo: 16px, interlinea 1.7, 18px di spazio sotto. Mai più piccoli su telefono.
- FORMATTAZIONE DEL CORPO (vale per tutte le email): niente muri di testo. Si va a capo ("\n") dove la frase respira, un pensiero per riga; pensieri diversi in paragrafi separati. Grassetto (**...**) solo sulle parole davvero chiave (l'offerta «dieci visite, ma ne paghi solo cinque», il prezzo «450€. La metà.», la frase-chiave del paragrafo), al massimo una o due per paragrafo. Le parole restano identiche: cambiano solo a capo e grassetti.
- paragrafo con "stile": "evidenza": la frase chiave dell'email, 20px, peso 800, barra sinistra verde di 4px. Al massimo una per email.
- elenco: card con etichetta (trattino verde), titolo 20px 800 e voci numerate. "stile": "motivi" = card bianca con bordo e numeri grandi chiari 01, 02, 03 (per il perché dell'offerta); "stile": "passi" = card crema con numeri in cerchi blu notte e cifra verde (per dire cosa fare). Campi: etichetta, titolo (facoltativo), voci.
- confronto: due card affiancate (una sotto l'altra su telefono). "sinistra" = PRIMA, crema con testo spento; "destra" = OGGI, scura con bagliore verde e testo bianco. Campi: etichetta, testo.
- box: card verde chiaro #EAFEF0 con bordo #BDF5CE, etichetta e paragrafi separati da una riga vuota (\n\n). Per la metafora dell'email.
- riquadro con "stile": "chiaro": stesso biglietto ma bianco con bordo verde 2px e alone verde, testo blu notte.
- riquadro = biglietto dell'offerta: fondo inchiostro → blu notte con bagliore verde, bordo verde sottile, angoli 22px. In alto etichetta ("etichetta"); riga 1 bianca 800 18px; riga 2 con il primo prezzo in Montserrat 900 66px (44px su telefono), "invece di" e il secondo prezzo barrato in #B8C4D4, sempre sulla stessa riga; schema delle visite ("visite": [pagate, omaggio], "legenda": [..., ...]): cerchi vuoti numerati = paghi, cerchi verdi = in omaggio; linea tratteggiata come uno strappo; riga 3 verde 700 14px con punto luminoso (la scadenza).
- pulsante: fatto in HTML (tabella + link), mai un'immagine. Come i pulsanti del sito: pillola verde in rilievo (sfumatura #A6FFBE → #72FA93 → #58E57F, luce in alto, ombra sotto, alone verde), etichetta piccola sopra il testo ("BLACK FRIDAY · −50%", da "sopra" o da striscia + sconto di config) e testo principale blu notte 800 17px; a destra cerchio 48px blu notte → nero con freccia verde piena DISEGNATA con le forme (asta 13×4px + punta a triangolo fatta con i bordi CSS), mai con un carattere: così è identica in ogni client. Testo del pulsante in tutte le email: «Riserva le tue 10 visite a metà prezzo» (10 in cifre). Su telefono a tutta larghezza (se va a capo su due righe va bene). Versione VML per Outlook desktop (solo testo).
- nota: centrata, subito sotto il pulsante. Con "stile": "passi" («Paghi online. Poi scegli tu: …») è una riga DISCRETA: 13px, grigio-blu, prima frase in grassetto blu notte, niente box. Non deve rubare l'attenzione al pulsante.
- chiusura: come un paragrafo.
- firma: trattino verde 32×3px, poi "Studio Mobilitas" 800 17px.
- ps: card con sfumatura chiara (#EEF4FA → #DCE8F3 → #F6F9FC), bordo #D7E2EE, angoli 20px; "P.S." dentro un cerchio blu notte con scritta verde, a sinistra (sopra il testo su telefono); testo 15px; con "scadenza" aggiunge sotto una pillola blu notte con punto verde (es. "SCADE IL 29.11 · ORE 23:59"). È l'ultima cosa che si legge: una frase netta, che metta davanti a una scelta.
- footer: centrato sotto la card, 12px #4A5F7A, interlinea 1.6, prima riga in grassetto.
Spazi tra i blocchi: tabella SPAZI in build.py.

Layout: card larga al massimo 600px, fluida sotto i 600px. Padding interno 40px (22px sotto i 480px). Logo: logo_url, larghezza logo_larghezza_px, centrato, altezza automatica, alt="Studio Mobilitas" con stile (blu notte, grassetto, 18px), così si legge anche con le immagini bloccate.

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
