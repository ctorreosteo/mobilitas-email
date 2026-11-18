#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build delle email Black Friday 2026 · Studio Mobilitas.
Nessuna dipendenza esterna (solo libreria standard, Python 3.7+).

Uso:  python3 build.py <numero>

Legge config.json, template/base.html e content/email_<numero>.json,
scrive emails/BF2026_email_<numero>_<AAAA-MM-GG>.html e .txt, fa i controlli
descritti nel CLAUDE.md e stampa il report OK / AVVISO / ERRORE e il
riepilogo per la piattaforma. Esce con codice 1 se c'è almeno un ERRORE.

FORMATO DI content/email_<numero>.json
{
  "numero": 1,
  "data_invio": "2026-11-19",
  "ora_invio": "19:30",
  "oggetto": "...",
  "oggetto_alternativo": "...",            ("" se non c'è)
  "preheader": "...",
  "testata": {...},                          facoltativo: sovrascrive "testata" di config.json
  "blocchi": [
    {"tipo": "saluto"},                      usa "saluto" di config.json ("testo" per sovrascriverlo)
    {"tipo": "paragrafo", "testo": "..."},
    {"tipo": "paragrafo", "testo": "...", "stile": "evidenza"},   frase in evidenza, più grande
    {"tipo": "riquadro", "righe": ["riga 1", "450€ invece di 900€", "riga 3"]},
    {"tipo": "pulsante", "testo": "...", "link": "lp"},    "lp" (predefinito) = link_lp con UTM
    {"tipo": "nota", "testo": "..."},
    {"tipo": "chiusura", "testo": "..."},
    {"tipo": "firma"},                       "Studio Mobilitas" ("testo" per sovrascriverlo)
    {"tipo": "ps", "testo": "P.S. ..."}
  ],
  "solo_testo": null,                        null = .txt generato dai blocchi; oppure una stringa
                                             con i segnaposto {saluto} {link_lp} {telefono}.
                                             Il footer viene sempre aggiunto in fondo.
  "testi_obbligatori": ["450€", "23:59"]
}

Segni di impaginazione ammessi nel testo dei blocchi (il controllo "testo identico" li ignora):
  a capo "\\n" -> <br>  ·  **testo** -> grassetto
  [testo](lp) -> link alla LP con UTM  ·  [testo](tel) -> telefono  ·  [testo](email) -> email
  [testo](https://...) -> altro link
Il numero di telefono (telefono_testo di config.json) diventa sempre un link tel:.
"""

import html
import json
import math
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs

BASE = Path(__file__).resolve().parent

# --------------------------------------------------------------------------
# Colori del brand: UNICO punto in cui sono definiti (template e blocchi).
# --------------------------------------------------------------------------
COLORI = {
    "C_PAGINA": "#EEF2F7",      # sfondo della pagina intorno alla card
    "C_BIANCO": "#FFFFFF",      # card dell'email
    "C_BORDO": "#E3EAF2",       # bordo della card e del box P.S.
    "C_CHIARO": "#F4F8FC",      # box del P.S.
    "C_NOTTE": "#002552",       # testo, link, testo del pulsante, testata
    "C_NOTTE2": "#0B3366",      # sfumatura della testata e del biglietto
    "C_NERO": "#000F2B",        # inchiostro del sito: nero Black Friday delle sfumature
    "C_VERDE": "#72FA93",       # verde Mobilitas (sito): pulsante e accenti; MAI per scrivere su bianco
    "C_CREMA": "#F4F4F4",       # crema del sito: card "cosa fare adesso"
    "C_VERDE_CHIARO": "#EAFEF0", # card "box" (verde del sito molto diluito)
    "C_VERDE_BORDO": "#BDF5CE",  # bordo della card "box"
    "C_SECONDARIO": "#4A5F7A",  # testo secondario su chiaro
    "C_SU_SCURO": "#B8C4D4",    # testo secondario su scuro, prezzo barrato
    # dark mode
    "D_PAGINA": "#00142F",
    "D_CARD": "#002552",
    "D_TESTO": "#F4F4F4",
    "D_SECONDARIO": "#B8C4D4",
    "D_RIQUADRO": "#0B3366",
    "D_BORDO": "#1E4A80",
}
C = COLORI
FONT = "Montserrat, Arial, Helvetica, sans-serif"

# Nero Black Friday (il nero del sito, #000611) e azzurro cielo del sito per le sfumature dei titoli
NERO_BF = "#000611"
CIELO = "#38BDF8"
# Effetti di rilievo (ombre a strati): scritte "estruse", bollini come bottoni 3D, banner che si staccano dalla pagina
RILIEVO_BIANCO = ("text-shadow:0 2px 0 #0B3366, 0 4px 0 #061B3A, 0 6px 0 rgba(0,0,0,0.55), "
                  "0 18px 32px rgba(0,0,0,0.55);")
RILIEVO_VERDE = ("text-shadow:0 2px 0 #3FD86B, 0 4px 0 #23A653, 0 6px 0 rgba(0,0,0,0.5), "
                 "0 0 42px rgba(114,250,147,0.45), 0 18px 32px rgba(0,0,0,0.5);")
RILIEVO_NERO = ("text-shadow:0 1px 0 rgba(255,255,255,0.6), 0 3px 0 #2EAA5A, 0 5px 0 rgba(0,37,82,0.35), "
                "0 16px 28px rgba(0,37,82,0.35);")
OMBRA_BANNER = ("box-shadow:0 36px 64px -26px rgba(0,6,17,0.7), 0 14px 28px -14px rgba(0,37,82,0.5), "
                "inset 0 1px 0 rgba(255,255,255,0.10);")
BOLLINO_BIANCO_3D = "box-shadow:0 20px 36px rgba(0,0,0,0.5), inset 0 -6px 0 rgba(0,37,82,0.14), inset 0 3px 0 #FFFFFF;"
BOLLINO_NERO_3D = ("box-shadow:0 20px 36px -6px rgba(0,6,17,0.7), inset 0 -6px 0 rgba(0,0,0,0.55), "
                   "inset 0 3px 0 rgba(255,255,255,0.16);")
def con_foto(t, velo):
    """Aggiunge la foto di sfondo (testata "sfondo_foto") sotto un velo di colore che tiene leggibile il testo.
    Senza foto restituisce solo il velo. Se il client non carica le immagini di sfondo resta il colore pieno (bgcolor)."""
    foto = t.get("sfondo_foto")
    if not foto:
        return ""
    return (" background-image:%s, url(%s); background-size:cover; background-position:%s; background-repeat:no-repeat;"
            % (velo, foto, t.get("sfondo_posizione", "center center")))


EVIDENZIATORE = ("background-image:linear-gradient(100deg, rgba(114,250,147,0.9) 10%, rgba(56,189,248,0.55) 95%); "
                 "background-size:100% 36%; background-position:0 90%; background-repeat:no-repeat;")

CALENDARIO = {1: "2026-11-19", 2: "2026-11-23", 3: "2026-11-25", 4: "2026-11-27", 5: "2026-11-29"}
ORA_INVIO = "19:30"
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]

PIATTAFORME = {
    "brevo": {"nome": "{{ contact.FIRSTNAME }}", "disiscrizione": "{{ unsubscribe }}"},
    "mailchimp": {"nome": "*|FNAME|*", "disiscrizione": "*|UNSUB|*"},
    "activecampaign": {"nome": "%FIRSTNAME%", "disiscrizione": "%UNSUBSCRIBELINK%"},
}

PAROLE_VIETATE = [
    ("porta un amico", r"porta\s+un\s+amico"),
    ("COUPON49", r"coupon49"),
    ("49€", r"(?<!\d)49\s?€"),
    ("49 euro", r"(?<!\d)49\s+euro"),
    ("rate", r"(?<!\w)rate(?!\w)"),
    ("155€", r"(?<!\d)155\s?€"),
    ("465€", r"(?<!\d)465\s?€"),
    ("bonus", r"bonus"),
    ("app", r"(?<!\w)app(?!\w)"),
    ("11 visite", r"(?<!\d)11\s+visite"),
    ("visita in più", r"visita\s+in\s+più"),
    ("percorso", r"percorso"),
    ("garantit", r"garantit"),
    ("guarigione", r"guarigione"),
]

EMOJI = re.compile(
    "[\\U0001F000-\\U0001FAFF\\u2600-\\u27BF\\u2B00-\\u2BFF\\uFE0F\\u231A\\u231B"
    "\\u23E9-\\u23FA\\u2934\\u2935\\u3030\\u303D\\u3297\\u3299]"
)
SEGNAPOSTO = re.compile(r"\[\[DA_COMPILARE[^\]]*\]\]")
LINK_MD = re.compile(r"\[([^\[\]]+)\]\(([^()\s]+)\)")
BOLD_MD = re.compile(r"\*\*(.+?)\*\*")
PREZZO = re.compile(r"^(\S+)( invece di )(\S+)(.*)$")

FOOTER_INTESTAZIONE = "Studio Mobilitas · Osteopatia a Torino"
FOOTER_AVVISO = "Ricevi questa email perché ti abbiamo seguito in studio."
FOOTER_DISISCRIZIONE = ("Non vuoi più ricevere le nostre email? ", "Disiscriviti qui", ".")

# Spazio (sopra, sotto) in px di ogni blocco: tra due blocchi vale il maggiore.
SPAZI = {
    "saluto": (0, 18), "paragrafo": (0, 18), "evidenza": (14, 28), "chiusura": (0, 18),
    "firma": (8, 18), "nota": (0, 18), "nota_passi": (14, 24), "riquadro": (30, 30), "pulsante": (30, 14), "ps": (30, 0),
    "elenco": (30, 30), "confronto": (24, 30), "box": (30, 30), "immagine": (28, 28), "benefici": (30, 30),
}

MARCA_INIZIO = "<!-- BLOCCHI:INIZIO -->"
MARCA_FINE = "<!-- BLOCCHI:FINE -->"


# --------------------------------------------------------------------------
# Utilità
# --------------------------------------------------------------------------
def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


def normalizza(s):
    s = s.replace("‌", "").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def testo_puro(s):
    """Testo del blocco senza i segni di impaginazione."""
    s = LINK_MD.sub(r"\1", s)
    s = BOLD_MD.sub(r"\1", s)
    return s


# Temi: "chiaro" (card bianca, email 1) e "notte" (tutta scura come il sito, email 2).
TEMI = {
    "chiaro": {"testo": C["C_NOTTE"], "forte": None, "sec": C["C_SECONDARIO"], "link": C["C_NOTTE"],
               "template": "base.html"},
    "notte": {"testo": "#D9E2EE", "forte": "#FFFFFF", "sec": "#8FA3BD", "link": "#FFFFFF",
              "template": "notte.html", "editoriale": True, "scuro": True,
              "titolo": "#FFFFFF", "card": "#0A1A36", "bordo": "rgba(255,255,255,0.10)", "linea": "rgba(255,255,255,0.12)"},
    "bianco": {"testo": C["C_NOTTE"], "forte": None, "sec": C["C_SECONDARIO"], "link": C["C_NOTTE"],
               "template": "bianco.html", "editoriale": True, "scuro": False,
               "titolo": C["C_NOTTE"], "card": "#F4F4F4", "bordo": "#E6EAF0", "linea": "#E3E8EF"},
    "centro": {"testo": C["C_NOTTE"], "forte": None, "sec": C["C_SECONDARIO"], "link": C["C_NOTTE"],
               "template": "centro.html", "editoriale": True, "scuro": False,
               "titolo": C["C_NOTTE"], "card": "#F4F4F4", "bordo": "#E6EAF0", "linea": "#E3E8EF"},
}
T = dict(TEMI["chiaro"])


def usa_tema(nome):
    T.clear()
    T.update(TEMI[nome])


def stile(size=16, lh="1.7", colore=None, extra=""):
    colore = colore or T["testo"]
    return ("margin:0; font-family:%s; font-size:%dpx; line-height:%s; color:%s;%s"
            % (FONT, size, lh, colore, (" " + extra) if extra else ""))


def stile_link():
    return "color:%s; text-decoration:underline;" % T["link"]
TABELLA = 'role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;"'
def GRASSETTO(m):
    colore = (" color:%s;" % T["forte"]) if T["forte"] else ""
    return '<strong style="font-weight:800;%s">%s</strong>' % (colore, m.group(1))


class Ctx:
    def __init__(self, cfg, numero, testata):
        self.cfg = cfg
        self.numero = numero
        self.testata = testata
        self.lp = url_lp(cfg, numero)

    def risolvi(self, dest):
        if dest == "lp":
            return self.lp
        if dest == "tel":
            return self.cfg["telefono_link"]
        if dest == "email":
            return "mailto:" + self.cfg["email_studio"]
        return dest


def url_lp(cfg, numero):
    base = cfg["link_lp"]
    frammento = ""
    if "#" in base:
        base, frammento = base.split("#", 1)
        frammento = "#" + frammento
    if base.endswith(("?", "&")):
        sep = ""
    else:
        sep = "&" if "?" in base else "?"
    utm = "utm_source=%s&utm_medium=%s&utm_campaign=%s&utm_content=email_%d" % (
        cfg["utm_source"], cfg["utm_medium"], cfg["utm_campaign"], numero)
    return base + sep + utm + frammento


def ancora(url, testo_html, cfg):
    blank = ' target="_blank"' if url.startswith(("http", cfg["link_lp"])) else ""
    st = stile_link() + (" white-space:nowrap;" if url.startswith("tel:") else "")
    return '<a href="%s"%s class="link" style="%s">%s</a>' % (attr(url), blank, st, testo_html)


def inline(s, ctx):
    """Testo del blocco -> HTML: escape, grassetto, link, telefono, a capo."""
    def segmento(t):
        t = BOLD_MD.sub(GRASSETTO, esc(t))
        tel = esc(ctx.cfg["telefono_testo"])
        if tel and tel in t:
            t = t.replace(tel, ancora(ctx.cfg["telefono_link"], tel, ctx.cfg))
        return t

    out, pos = [], 0
    for m in LINK_MD.finditer(s):
        out.append(segmento(s[pos:m.start()]))
        testo_link = BOLD_MD.sub(GRASSETTO, esc(m.group(1)))
        out.append(ancora(ctx.risolvi(m.group(2)), testo_link, ctx.cfg))
        pos = m.end()
    out.append(segmento(s[pos:]))
    return "".join(out).replace("\n", "<br>")


def inline_txt(s, ctx):
    """Testo del blocco -> .txt: testo identico, poi gli URL dei link per esteso."""
    urls = [ctx.risolvi(m.group(2)) for m in LINK_MD.finditer(s)]
    urls = [u[len("tel:"):] if u.startswith("tel:") else u for u in urls]
    urls = [u[len("mailto:"):] if u.startswith("mailto:") else u for u in urls]
    return "\n".join([testo_puro(s)] + urls)


def etichetta(testo, colore, bordo, sfondo="transparent"):
    """Pillola maiuscola spaziata (elemento grafico della testata e del biglietto)."""
    return ('<span style="display:inline-block; padding:6px 12px; border:1px solid %s; border-radius:999px; '
            'background-color:%s; font-family:%s; font-size:10px; line-height:12px; font-weight:800; '
            'letter-spacing:2.4px; color:%s; white-space:nowrap;">%s</span>'
            % (bordo, sfondo, FONT, colore, esc(testo)))


# --------------------------------------------------------------------------
# Testata Black Friday (elementi grafici fissi, testi in config.json "testata")
# --------------------------------------------------------------------------
def testata_html(t):
    frase = t.get("variante") == "frase"
    parole = t["titolo"].split("|", 1) if frase else t["titolo"].split(" ", 1)
    riga1, riga2 = (parole + [""])[:2]
    cls_wm = "wm-f" if frase else "wm"
    az = C["C_VERDE"]
    sfondo = (
        "background-color:%s; background-image:"
        "radial-gradient(circle at 88%% 18%%, rgba(114,250,147,0.38) 0%%, rgba(114,250,147,0) 42%%), "
        "radial-gradient(circle at 0%% 100%%, rgba(11,51,102,0.9) 0%%, rgba(11,51,102,0) 55%%), "
        "linear-gradient(140deg, %s 0%%, %s 50%%, %s 100%%);"
        % (NERO_BF, NERO_BF, C["C_NERO"], C["C_NOTTE"]))
    if t.get("sfondo_foto"):
        sfondo = "background-color:%s;" % NERO_BF + con_foto(t,
            "radial-gradient(circle at 88% 18%, rgba(114,250,147,0.30) 0%, rgba(114,250,147,0) 42%), "
            "linear-gradient(90deg, rgba(0,6,17,0.95) 0%, rgba(0,6,17,0.86) 42%, rgba(0,15,43,0.62) 72%, rgba(0,37,82,0.50) 100%)")
    if frase:
        wm = "font-family:%s; font-size:46px; line-height:48px; font-weight:900; letter-spacing:-1.6px;" % FONT
    else:
        wm = "font-family:%s; font-size:76px; line-height:66px; font-weight:900; letter-spacing:-3px;" % FONT

    # Riga alta: etichetta a sinistra, sigla a destra
    alto = (
        '<table %s><tr>'
        '<td valign="middle">%s</td>'
        '<td class="tk-x" valign="middle" align="right" style="text-align:right; font-family:%s; font-size:10px; '
        'line-height:12px; font-weight:800; letter-spacing:2.4px; color:rgba(255,255,255,0.55);">%s</td>'
        '</tr></table>'
    ) % (TABELLA, etichetta(t["etichetta"], az, "rgba(114,250,147,0.5)", "rgba(114,250,147,0.08)"),
         FONT, esc(t["sigla"]))

    # Titolo + timbro
    titolo = (
        '<p style="margin:0;"><span class="%s" style="%s color:#FFFFFF; %s">%s</span><br>'
        '<span class="%s" style="%s color:%s; %s">%s</span></p>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px;"><tr>'
        '<td width="56" height="4" bgcolor="%s" style="width:56px; height:4px; border-radius:2px; background-color:%s; '
        'font-size:0; line-height:0;">&nbsp;</td>'
        '<td width="8" style="width:8px; font-size:0; line-height:0;">&nbsp;</td>'
        '<td width="12" height="4" bgcolor="#FFFFFF" style="width:12px; height:4px; border-radius:2px; background-color:#FFFFFF; '
        'font-size:0; line-height:0;">&nbsp;</td></tr></table>'
    ) % (cls_wm, wm, RILIEVO_BIANCO, esc(riga1), cls_wm, wm, az, RILIEVO_VERDE, esc(riga2), az, az)
    piccolo = ("display:block; font-family:%s; font-size:9px; line-height:11px; font-weight:800; "
               "letter-spacing:2px; color:%s;" % (FONT, C["C_SECONDARIO"]))
    timbro = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="right" '
        'style="transform:rotate(-10deg);"><tr>'
        '<td class="timbro" style="padding:6px; border:2px dashed rgba(114,250,147,0.7); border-radius:50%%;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        '<td class="bollino" align="center" valign="middle" width="112" height="112" bgcolor="#FFFFFF" '
        'style="width:112px; height:112px; border-radius:50%%; background-color:#FFFFFF; text-align:center; %s">'
        '<span class="tb-s" style="%s">%s</span>'
        '<span class="bollino-t" style="display:block; font-family:%s; font-size:32px; line-height:34px; font-weight:900; '
        'letter-spacing:-1.5px; color:%s; white-space:nowrap;">%s</span>'
        '<span class="tb-s" style="%s">%s</span>'
        '</td></tr></table></td></tr></table>'
    ) % (BOLLINO_BIANCO_3D, piccolo, esc(t["sconto_sopra"]), FONT, C["C_NOTTE"], esc(t["sconto"]), piccolo, esc(t["sconto_sotto"]))

    # Riga dati in stile biglietto
    celle = []
    for k, d in enumerate(t["dati"]):
        lab, val = d[0], d[1]
        solo_computer = len(d) > 2 and d[2] == "solo_computer"
        bordo = "" if k == 0 else " border-left:1px solid rgba(255,255,255,0.14); padding-left:16px;"
        classe = ' class="tk-x"' if solo_computer else ""
        celle.append(
            '<td%s valign="top" style="padding:16px 12px 0 0;%s">'
            '<span style="display:block; font-family:%s; font-size:9px; line-height:12px; font-weight:800; '
            'letter-spacing:2.2px; color:%s;">%s</span>'
            '<span class="dato" style="display:block; margin-top:4px; font-family:%s; font-size:14px; line-height:18px; '
            'font-weight:800; color:#FFFFFF; white-space:nowrap;">%s</span></td>'
            % (classe, bordo, FONT, az, esc(lab), FONT, esc(val)))
    dati = (
        '<table %s><tr><td style="padding:26px 0 0 0;">'
        '<div style="border-top:1px solid rgba(255,255,255,0.14); height:0; line-height:0; font-size:0;">&nbsp;</div>'
        '</td></tr></table>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>%s</tr></table>'
    ) % (TABELLA, "".join(celle))

    # Striscia finale
    pallino = ('<span style="display:inline-block; width:5px; height:5px; border-radius:50%%; background-color:%s; '
               'vertical-align:middle; margin:0 14px; box-shadow:0 0 8px rgba(114,250,147,0.8);"></span>' % C["C_VERDE"])
    striscia = ('<span class="tk-x">%s%s</span>%s%s%s%s%s'
                % (esc(t["striscia"]), pallino, esc(t["sconto"]), pallino, esc(t["striscia"]), pallino, esc(t["sconto"])))

    return (
        '<table %s style="border-radius:18px; ' + OMBRA_BANNER.replace('%', '%%') + '">'
        '<tr><td class="hero-in" style="padding:26px 30px 24px 30px; border-radius:18px 18px 0 0; %s">'
        '%s'
        '<table %s><tr>'
        '<td valign="bottom" style="padding-top:26px;">%s</td>'
        '<td class="col-timbro%s" valign="middle" width="140" style="width:140px; padding-top:22px;">%s</td>'
        '</tr></table>'
        '%s'
        '</td></tr>'
        '<tr><td align="center" bgcolor="%s" style="padding:12px 12px; border-radius:0 0 18px 18px; '
        'background-color:%s; border-top:1px solid rgba(114,250,147,0.55); '
        'font-family:%s; font-size:10px; line-height:14px; font-weight:900; letter-spacing:3px; color:#FFFFFF; '
        'white-space:nowrap;">%s</td></tr>'
        '</table>'
    ) % (TABELLA.replace(' style="width:100%;"', ' width="100%"'), sfondo, alto, TABELLA, titolo, " tb-hide-m" if frase else "", timbro, dati,
         NERO_BF, NERO_BF, FONT, striscia)


# --------------------------------------------------------------------------
# Blocchi: ognuno restituisce (html, txt, [testi attesi])
# --------------------------------------------------------------------------
def occhiello(testo, colore, linea, classe=""):
    """Etichetta maiuscola con trattino davanti, come sul sito."""
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        '<td width="22" style="width:22px; padding-right:10px;" valign="middle">'
        '<div style="height:2px; line-height:2px; font-size:0; background-color:%s; border-radius:2px;">&nbsp;</div></td>'
        '<td%s valign="middle" style="font-family:%s; font-size:10px; line-height:14px; font-weight:800; '
        'letter-spacing:2.4px; color:%s;">%s</td></tr></table>'
    ) % (linea, (' class="%s"' % classe) if classe else "", FONT, colore, esc(testo))


def b_testo(b, ctx, testo=None):
    t = testo if testo is not None else b["testo"]
    if b.get("stile") == "evidenza":
        h = ('<table %s><tr><td class="evid" style="border-left:4px solid %s; padding:4px 0 4px 20px;">'
             '<p class="t-main" style="%s">%s</p></td></tr></table>'
             % (TABELLA, C["C_VERDE"], stile(20, "1.42", extra="font-weight:800; letter-spacing:-0.3px;"),
                inline(t, ctx)))
    else:
        h = '<p class="t-main" style="%s">%s</p>' % (stile(), inline(t, ctx))
    return h, inline_txt(t, ctx), [testo_puro(t)]


def b_saluto(b, ctx):
    return b_testo(b, ctx, b.get("testo", ctx.cfg["saluto"]))


def b_firma(b, ctx):
    t = b.get("testo", "Studio Mobilitas")
    h = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
         '<td width="32" height="3" bgcolor="%s" style="width:32px; height:3px; border-radius:2px; '
         'background-color:%s; font-size:0; line-height:0;">&nbsp;</td></tr></table>'
         '<p class="t-main" style="%s">%s</p>'
         % (C["C_VERDE"], C["C_VERDE"], stile(17, "1.4", extra="font-weight:800; margin-top:12px;"),
            inline(t, ctx)))
    return h, testo_puro(t), [testo_puro(t)]


def b_elenco(b, ctx):
    """Card con occhiello, titolo e voci numerate.
    stile "motivi": card bianca, numeri grandi chiari (01, 02...).
    stile "passi":  card crema, numeri in cerchi blu notte con cifra verde."""
    passi = b.get("stile") == "passi"
    voci = b["voci"]
    parti = [occhiello(b["etichetta"], C["C_NOTTE"], C["C_VERDE"], "t-main")]
    attesi = [b["etichetta"]]
    if b.get("titolo"):
        parti.append('<p class="t-main" style="%s">%s</p>' % (
            stile(20, "1.35", extra="font-weight:800; letter-spacing:-0.3px; margin-top:12px;"), inline(b["titolo"], ctx)))
        attesi.append(testo_puro(b["titolo"]))
    righe = []
    for i, v in enumerate(voci, 1):
        sep = "" if i == 1 else " border-top:1px solid %s;" % (C["C_BORDO"] if not passi else "#E6EAF0")
        if passi:
            num = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
                   '<td align="center" valign="middle" width="32" height="32" bgcolor="%s" style="width:32px; height:32px; '
                   'border-radius:50%%; background-color:%s; font-family:%s; font-size:14px; line-height:32px; '
                   'font-weight:900; color:%s;">%d</td></tr></table>' % (C["C_NOTTE"], C["C_NOTTE"], FONT, C["C_VERDE"], i))
            larg = 48
        else:
            num = ('<span class="num-ghost" style="font-family:%s; font-size:30px; line-height:30px; font-weight:900; '
                   'letter-spacing:-1px; color:%s;">%02d</span>' % (FONT, "#C9D6E6", i))
            larg = 58
        righe.append(
            '<tr><td class="sep" valign="top" width="%d" style="width:%dpx; padding:14px 0;%s">%s</td>'
            '<td class="sep" valign="middle" style="padding:14px 0;%s"><p class="t-main" style="%s">%s</p></td></tr>'
            % (larg, larg, sep, num, sep, stile(15, "1.55"), inline(v, ctx)))
        attesi.append(testo_puro(v))
    parti.append('<table %s style="margin-top:8px;">%s</table>' % (TABELLA.replace(' style="width:100%;"', ""), "".join(righe)))
    if passi:
        card = ('class="card-passi" style="padding:20px 24px 8px 24px; border:1px solid %s; border-radius:20px;"'
                % C["C_BORDO"])
    else:
        card = ('class="card-motivi" bgcolor="%s" style="padding:24px 26px 12px 26px; background-color:%s; '
                'border:1px solid %s; border-radius:20px; box-shadow:0 12px 30px rgba(0,37,82,0.06);"'
                % (C["C_BIANCO"], C["C_BIANCO"], C["C_BORDO"]))
    h = '<table %s><tr><td %s>%s</td></tr></table>' % (TABELLA, card, "".join(parti))
    txt = "\n".join([b["etichetta"]] + ([testo_puro(b["titolo"])] if b.get("titolo") else []) + [""] +
                    ["%d. %s" % (i, inline_txt(v, ctx)) for i, v in enumerate(voci, 1)])
    return h, txt, attesi


def b_confronto(b, ctx):
    """Due card affiancate: a sinistra "prima" (crema, testo spento), a destra "oggi" (scura, testo bianco)."""
    sx, dx = b["sinistra"], b["destra"]
    def card(lato, scura):
        lab_col = C["C_VERDE"] if scura else C["C_SECONDARIO"]
        linea = C["C_VERDE"] if scura else "#B8C4D4"
        testo_col = "#FFFFFF" if scura else C["C_SECONDARIO"]
        occ = occhiello(lato["etichetta"], lab_col, linea, "" if scura else "t-sec")
        corpo = '<p class="%s" style="%s">%s</p>' % (
            "" if scura else "t-sec", stile(15, "1.6", testo_col, "margin-top:12px;"), inline(lato["testo"], ctx))
        if scura:
            fondo = ('bgcolor="%s" style="padding:22px 22px 24px 22px; border-radius:18px; background-color:%s; '
                     'background-image:radial-gradient(circle at 100%% 0%%, rgba(114,250,147,0.22) 0%%, rgba(114,250,147,0) 50%%), '
                     'linear-gradient(160deg, %s 0%%, %s 100%%);"' % (C["C_NOTTE"], C["C_NOTTE"], C["C_NERO"], C["C_NOTTE"]))
            classe = "cf cf-oggi"
        else:
            fondo = ('bgcolor="%s" style="padding:22px 22px 24px 22px; border-radius:18px; background-color:%s;"'
                     % (C["C_CREMA"], C["C_CREMA"]))
            classe = "cf card-passi"
        return '<td class="%s" valign="top" width="48%%" %s>%s%s</td>' % (classe, fondo, occ, corpo)
    h = ('<table %s><tr>%s<td class="cf-gap" width="4%%" style="width:4%%; min-width:12px; font-size:0; line-height:0;">&nbsp;</td>%s</tr></table>'
         % (TABELLA, card(sx, False), card(dx, True)))
    txt = "%s\n%s\n\n%s\n%s" % (sx["etichetta"], inline_txt(sx["testo"], ctx), dx["etichetta"], inline_txt(dx["testo"], ctx))
    return h, txt, [sx["etichetta"], testo_puro(sx["testo"]), dx["etichetta"], testo_puro(dx["testo"])]


def b_box(b, ctx):
    """Card verde chiaro con etichetta e paragrafi (per una metafora o un'idea forte). "\n\n" separa i paragrafi."""
    paragrafi = b["testo"].split("\n\n")
    parti = [occhiello(b["etichetta"], C["C_NOTTE"], C["C_VERDE"], "t-main")]
    for i, par in enumerate(paragrafi):
        parti.append('<p class="t-main" style="%s">%s</p>' % (
            stile(16, "1.65", extra="margin-top:%dpx;" % (14 if i == 0 else 12)), inline(par, ctx)))
    h = ('<table %s><tr><td class="card-box" bgcolor="%s" style="padding:24px 26px 26px 26px; background-color:%s; '
         'border:1px solid %s; border-radius:20px;">%s</td></tr></table>'
         % (TABELLA, C["C_VERDE_CHIARO"], C["C_VERDE_CHIARO"], C["C_VERDE_BORDO"], "".join(parti)))
    txt = b["etichetta"] + "\n" + "\n\n".join(inline_txt(x, ctx) for x in paragrafi)
    return h, txt, [b["etichetta"]] + [testo_puro(x) for x in paragrafi]


def b_riquadro_chiaro(b, ctx):
    """Biglietto dell'offerta in versione chiara: card bianca con bordo verde, testo blu notte."""
    righe = b["righe"]
    v, n = C["C_VERDE"], C["C_NOTTE"]
    sopra = []
    if b.get("etichetta"):
        sopra.append(occhiello(b["etichetta"], n, v, "t-main"))
    for i, r in enumerate(righe[:2]):
        m = PREZZO.match(r) if i == 1 else None
        if i == 0:
            sopra.append('<p class="t-main" style="%s">%s</p>' % (
                stile(18, "1.4", n, "font-weight:800; letter-spacing:-0.2px; margin-top:14px;"), inline(r, ctx)))
        elif m:
            sopra.append(
                '<p class="t-main" style="%s">'
                '<span class="prezzo" style="font-size:66px; line-height:70px; font-weight:900; letter-spacing:-3px;">%s</span> '
                '<span style="white-space:nowrap; padding-left:2px;">'
                '<span class="t-sec" style="font-size:16px; font-weight:400; color:%s;">%s</span>'
                '<span class="t-sec" style="font-size:20px; font-weight:700; color:%s; text-decoration:line-through;">%s</span>'
                '<span class="t-sec" style="font-size:16px; font-weight:400; color:%s;">%s</span></span></p>' % (
                    stile(16, "1.2", n, "margin-top:6px;"), esc(m.group(1)),
                    C["C_SECONDARIO"], esc(m.group(2).lstrip()), C["C_SECONDARIO"], esc(m.group(3)),
                    C["C_SECONDARIO"], esc(m.group(4))))
        else:
            sopra.append('<p class="t-main" style="%s">%s</p>' % (stile(16, "1.5", n, "margin-top:8px;"), inline(r, ctx)))
    if b.get("visite"):
        pagate, omaggio = b["visite"]
        celle = []
        for k in range(1, pagate + omaggio + 1):
            if k > 1:
                celle.append('<td width="4" style="width:4px; font-size:0; line-height:0;">&nbsp;</td>')
            if k <= pagate:
                st = "border:2px solid %s; color:%s; width:18px; height:18px; line-height:18px;" % (n, n)
                cl = "pall-pag t-main"
            else:
                st = ("background-color:%s; color:%s; width:22px; height:22px; line-height:22px; "
                      "box-shadow:0 4px 10px rgba(114,250,147,0.55);" % (v, n))
                cl = "pall-om"
            celle.append('<td class="%s" align="center" valign="middle" style="%s border-radius:50%%; font-family:%s; '
                         'font-size:10px; font-weight:900; text-align:center;">%d</td>' % (cl, st, FONT, k))
        leg = b.get("legenda", ["", ""])
        voce = ('<td valign="middle" style="padding-right:8px;"><div class="%s" style="width:10px; height:10px; border-radius:50%%; %s">'
                '</div></td><td class="t-main" valign="middle" style="padding-right:18px; font-family:%s; font-size:10px; line-height:12px; '
                'font-weight:800; letter-spacing:1.8px; color:%s; white-space:nowrap;">%s</td>')
        sopra.append(
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:18px;"><tr>%s</tr></table>'
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:10px;"><tr>%s%s</tr></table>'
            % ("".join(celle),
               voce % ("pall-pag", "border:2px solid %s; width:6px; height:6px;" % n, FONT, n, esc(leg[0])),
               voce % ("", "background-color:%s;" % v, FONT, n, esc(leg[1]))))
    sotto = []
    for i, r in enumerate(righe[2:]):
        punto = ('<span style="display:inline-block; width:8px; height:8px; border-radius:50%%; background-color:%s; '
                 'vertical-align:middle; margin-right:10px; box-shadow:0 0 0 4px rgba(114,250,147,0.30);"></span>' % v) if i == 0 else ""
        sotto.append('<p class="t-main" style="%s">%s%s</p>' % (
            stile(14, "1.55", n, "font-weight:800;" + (" margin-top:6px;" if i else "")), punto, inline(r, ctx)))
    h = (
        '<table role="presentation" class="cp-chiaro" width="100%%" cellpadding="0" cellspacing="0" border="0" bgcolor="%s" '
        'style="width:100%%; border-radius:22px; border:2px solid %s; background-color:%s; '
        'box-shadow:0 22px 44px -22px rgba(114,250,147,0.75);">'
        '<tr><td class="cp" style="padding:26px 28px 22px 28px;">%s</td></tr>'
        '<tr><td class="cp" style="padding:4px 28px;"><div class="sep" style="border-top:2px dashed %s; '
        'height:0; line-height:0; font-size:0;">&nbsp;</div></td></tr>'
        '<tr><td class="cp" style="padding:16px 28px 22px 28px;">%s</td></tr>'
        '</table>'
    ) % (C["C_BIANCO"], v, C["C_BIANCO"], "".join(sopra), C["C_BORDO"], "".join(sotto))
    txt = "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [testo_puro(r) for r in righe]


def b_riquadro(b, ctx):
    """Il riquadro dell'offerta come biglietto Black Friday, con lo schema visivo delle visite."""
    if b.get("stile") == "chiaro":
        return b_riquadro_chiaro(b, ctx)
    righe = b["righe"]
    v = C["C_VERDE"]
    sopra = []
    if b.get("etichetta"):
        sopra.append(occhiello(b["etichetta"], v, v))
    for i, r in enumerate(righe[:2]):
        m = PREZZO.match(r) if i == 1 else None
        if i == 0:
            sopra.append('<p style="%s">%s</p>' % (
                stile(18, "1.4", "#FFFFFF", "font-weight:800; letter-spacing:-0.2px; margin-top:14px;"), inline(r, ctx)))
        elif m:
            sopra.append(
                '<p style="%s">'
                '<span class="prezzo" style="font-size:66px; line-height:70px; font-weight:900; letter-spacing:-3px; color:#FFFFFF;">%s</span> '
                '<span style="white-space:nowrap; padding-left:2px;">'
                '<span style="font-size:16px; font-weight:400; color:%s;">%s</span>'
                '<span style="font-size:20px; font-weight:700; color:%s; text-decoration:line-through;">%s</span>'
                '<span style="font-size:16px; font-weight:400; color:%s;">%s</span></span></p>' % (
                    stile(16, "1.2", "#FFFFFF", "margin-top:6px;"), esc(m.group(1)),
                    C["C_SU_SCURO"], esc(m.group(2).lstrip()), C["C_SU_SCURO"], esc(m.group(3)),
                    C["C_SU_SCURO"], esc(m.group(4))))
        else:
            sopra.append('<p style="%s">%s</p>' % (stile(16, "1.5", "#FFFFFF", "margin-top:8px;"), inline(r, ctx)))

    # Schema delle visite: cerchi vuoti = paghi, cerchi verdi = in omaggio
    if b.get("visite"):
        pagate, omaggio = b["visite"]
        celle = []
        for n in range(1, pagate + omaggio + 1):
            if n > 1:
                celle.append('<td width="4" style="width:4px; font-size:0; line-height:0;">&nbsp;</td>')
            if n <= pagate:
                st = "border:2px solid rgba(255,255,255,0.55); color:#FFFFFF; width:18px; height:18px; line-height:18px;"
            else:
                st = ("background-color:%s; color:%s; width:22px; height:22px; line-height:22px; "
                      "box-shadow:0 0 12px rgba(114,250,147,0.45);" % (v, C["C_NERO"]))
            celle.append('<td class="pallino" align="center" valign="middle" style="%s border-radius:50%%; '
                         'font-family:%s; font-size:10px; font-weight:900; text-align:center;">%d</td>' % (st, FONT, n))
        leg = b.get("legenda", ["", ""])
        voce = ('<td valign="middle" style="padding-right:8px;"><div style="width:10px; height:10px; border-radius:50%%; %s">'
                '</div></td><td valign="middle" style="padding-right:18px; font-family:%s; font-size:10px; line-height:12px; '
                'font-weight:800; letter-spacing:1.8px; color:%s; white-space:nowrap;">%s</td>')
        sopra.append(
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:18px;"><tr>%s</tr></table>'
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:10px;"><tr>%s%s</tr></table>'
            % ("".join(celle),
               voce % ("border:2px solid rgba(255,255,255,0.55); width:6px; height:6px;", FONT, C["C_SU_SCURO"], esc(leg[0])),
               voce % ("background-color:%s;" % v, FONT, v, esc(leg[1]))))

    sotto = []
    for i, r in enumerate(righe[2:]):
        punto = ('<span style="display:inline-block; width:8px; height:8px; border-radius:50%%; '
                 'background-color:%s; vertical-align:middle; margin-right:10px; '
                 'box-shadow:0 0 0 4px rgba(114,250,147,0.22);"></span>' % v) if i == 0 else ""
        sotto.append('<p style="%s">%s%s</p>' % (
            stile(14, "1.55", v if i == 0 else C["C_SU_SCURO"],
                  "font-weight:700;" + (" margin-top:6px;" if i else "")), punto, inline(r, ctx)))

    fondo = ("background-color:%s; background-image:"
             "radial-gradient(circle at 100%% 0%%, rgba(114,250,147,0.20) 0%%, rgba(114,250,147,0) 46%%), "
             "linear-gradient(165deg, %s 0%%, %s 100%%);" % (C["C_NOTTE"], C["C_NERO"], C["C_NOTTE"]))
    h = (
        '<table role="presentation" class="cp-top" width="100%%" cellpadding="0" cellspacing="0" border="0" bgcolor="%s" '
        'style="width:100%%; border-radius:22px; border:1px solid rgba(114,250,147,0.22); '
        'box-shadow:0 24px 48px -20px rgba(0,37,82,0.55); %s">'
        '<tr><td class="cp" style="padding:26px 28px 22px 28px;">%s</td></tr>'
        '<tr><td class="cp" style="padding:4px 28px;"><div style="border-top:2px dashed rgba(255,255,255,0.22); '
        'height:0; line-height:0; font-size:0;">&nbsp;</div></td></tr>'
        '<tr><td class="cp" style="padding:16px 28px 22px 28px;">%s</td></tr>'
        '</table>'
    ) % (C["C_NOTTE"], fondo, "".join(sopra), "".join(sotto))
    txt = "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [testo_puro(r) for r in righe]


def b_pulsante(b, ctx):
    """Pulsante come quelli del sito: pillola verde in rilievo, etichetta piccola sopra il testo,
    cerchio scuro con freccia verde luminosa. Versione VML (solo testo) per Outlook desktop."""
    testo = b["testo"]
    url = ctx.risolvi(b.get("link", "lp"))
    sopra = b.get("sopra")
    if sopra is None:
        sopra = "%s · %s" % (ctx.testata.get("striscia", "BLACK FRIDAY"), ctx.testata.get("sconto", "−50%"))
    n, v = C["C_NOTTE"], C["C_VERDE"]
    larg_testo = len(testo) * 10.2
    w = int(min(536, larg_testo + 80))
    righe = max(1, math.ceil(larg_testo / (536 - 80)))
    alt = 60 + (righe - 1) * 22
    etichetta_html = ('<span style="display:block; font-family:%s; font-size:9.5px; line-height:12px; font-weight:900; '
                      'letter-spacing:2.2px; color:#0E6B37;">%s</span>' % (FONT, esc(sopra))) if sopra else ""
    h = (
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" style="width:100%%;">'
        '<tr><td align="center" style="padding:0;">'
        '<!--[if mso]>'
        '<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" '
        'href="%(url)s" style="height:%(alt)dpx; v-text-anchor:middle; width:%(w)dpx;" arcsize="50%%" '
        'strokecolor="%(v)s" fillcolor="%(v)s"><w:anchorlock/>'
        '<center style="color:%(n)s; font-family:Arial, Helvetica, sans-serif; font-size:17px; font-weight:bold;">%(testo)s</center>'
        '</v:roundrect>'
        '<![endif]-->'
        '<!--[if !mso]><!-->'
        '<table role="presentation" class="btn-table" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;">'
        '<tr><td class="btn-td" align="center" bgcolor="%(v)s" style="border-radius:999px; background-color:%(v)s; '
        'background-image:linear-gradient(180deg, #A6FFBE 0%%, %(v)s 55%%, #58E57F 100%%); '
        'box-shadow:0 20px 36px -14px rgba(114,250,147,0.95), 0 10px 20px -10px rgba(0,37,82,0.40), '
        'inset 0 2px 0 rgba(255,255,255,0.7), inset 0 -3px 0 rgba(0,37,82,0.14);">'
        '<a class="btn-a" href="%(url)s" target="_blank" style="display:block; padding:9px 9px 9px 30px; '
        'text-decoration:none; color:%(n)s; border-radius:999px;">'
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"><tr>'
        '<td class="btn-txt" valign="middle" align="left" style="padding-right:18px; text-align:left;">'
        '%(etichetta)s'
        '<span style="display:block; margin-top:3px; font-family:%(font)s; font-size:17px; line-height:21px; font-weight:800; '
        'letter-spacing:-0.2px; color:%(n)s;">%(testo)s</span></td>'
        '<td valign="middle" align="right" width="48" style="width:48px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        '<td align="center" valign="middle" width="48" height="48" bgcolor="%(n)s" style="width:48px; height:48px; '
        'border-radius:50%%; background-color:%(n)s; background-image:linear-gradient(145deg, #0B3366 0%%, %(nero)s 100%%); '
        'box-shadow:inset 0 2px 0 rgba(255,255,255,0.18), 0 8px 16px -6px rgba(0,6,17,0.7), 0 0 0 4px rgba(0,37,82,0.10); '
        'text-align:center; font-size:0; line-height:0;">'
        # Freccia disegnata con le forme (asta + punta a triangolo fatta con i bordi): identica in ogni client
        '<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;"><tr>'
        '<td valign="middle" style="font-size:0; line-height:0;">'
        '<div style="width:13px; height:4px; border-radius:2px 0 0 2px; background-color:%(v)s; font-size:0; line-height:0;">&nbsp;</div></td>'
        '<td valign="middle" style="font-size:0; line-height:0;">'
        '<div style="width:0; height:0; border-top:8px solid transparent; border-bottom:8px solid transparent; '
        'border-left:11px solid %(v)s; font-size:0; line-height:0;"></div></td>'
        '</tr></table></td></tr></table>'
        '</td></tr></table>'
        '</a></td></tr></table>'
        '<!--<![endif]-->'
        '</td></tr></table>'
    ) % {"url": attr(url), "alt": alt, "w": w, "v": v, "n": n, "nero": NERO_BF,
         "font": FONT, "testo": esc(testo), "etichetta": etichetta_html}
    return h, "%s\n%s" % (testo, url), [testo]


def nota_passi(b, ctx):
    """Nota sotto il pulsante, discreta: una riga piccola e centrata, la prima frase in grassetto.
    Il testo resta identico: la prima frase viene solo evidenziata."""
    t = b["testo"]
    frasi = re.split(r"(?<=[.!?])\s+", t, maxsplit=1)
    corpo = '<strong style="font-weight:800; color:%s;">%s</strong>' % (C["C_NOTTE"], inline(frasi[0], ctx))
    if len(frasi) > 1:
        corpo += " " + inline(frasi[1], ctx)
    h = ('<p class="t-sec" style="%s">%s</p>'
         % (stile(13, "1.6", C["C_SECONDARIO"], "text-align:center; max-width:440px; margin-left:auto; margin-right:auto;"), corpo))
    return h, inline_txt(t, ctx), [testo_puro(f) for f in frasi]


def b_nota(b, ctx):
    t = b["testo"]
    if b.get("stile") == "passi":
        return nota_passi(b, ctx)
    h = '<p class="t-sec" style="%s">%s</p>' % (
        stile(14, "1.6", C["C_SECONDARIO"], "text-align:center; font-weight:700;"), inline(t, ctx))
    return h, inline_txt(t, ctx), [testo_puro(t)]


def b_ps(b, ctx):
    """P.S.: card sfumata chiara, sigla "P.S." in un cerchio blu notte, scadenza facoltativa ("scadenza")."""
    t = b["testo"]
    if t.startswith("P.S."):
        sigla, corpo = "P.S.", t[4:].lstrip()
    else:
        sigla, corpo = "", t
    cerchio = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        '<td class="ps-sigla" align="center" valign="middle" width="46" height="46" bgcolor="%s" '
        'style="width:46px; height:46px; border-radius:50%%; background-color:%s; font-family:%s; font-size:13px; '
        'line-height:46px; font-weight:900; letter-spacing:-0.3px; color:%s; text-align:center; '
        'box-shadow:0 8px 18px -6px rgba(0,37,82,0.45);">%s</td></tr></table>'
    ) % (C["C_NOTTE"], C["C_NOTTE"], FONT, C["C_VERDE"], esc(sigla)) if sigla else ""
    chip = ""
    if b.get("scadenza"):
        chip = (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:16px;"><tr>'
            '<td bgcolor="%s" style="padding:8px 14px; border-radius:999px; background-color:%s; font-family:%s; '
            'font-size:9.5px; line-height:14px; font-weight:800; letter-spacing:1.6px; color:#FFFFFF;">'
            '<span style="display:inline-block; width:7px; height:7px; border-radius:50%%; background-color:%s; '
            'vertical-align:middle; margin-right:8px; box-shadow:0 0 0 3px rgba(114,250,147,0.25);"></span>%s</td>'
            '</tr></table>'
        ) % (C["C_NOTTE"], C["C_NOTTE"], FONT, C["C_VERDE"], esc(b["scadenza"]))
    h = (
        '<table %s><tr><td class="ps-box" bgcolor="%s" style="padding:24px 24px 24px 22px; background-color:%s; '
        'background-image:linear-gradient(135deg, #EEF4FA 0%%, #DCE8F3 55%%, #F6F9FC 100%%); '
        'border:1px solid #D7E2EE; border-radius:20px;">'
        '<table %s><tr>'
        '<td class="ps-col" valign="top" width="62" style="width:62px;">%s</td>'
        '<td class="ps-txt" valign="top"><p class="t-main" style="%s">%s</p>%s</td>'
        '</tr></table></td></tr></table>'
    ) % (TABELLA, C["C_CHIARO"], C["C_CHIARO"], TABELLA, cerchio,
         stile(15, "1.65", extra="padding-top:2px; text-wrap:balance;"), inline(corpo, ctx), chip)
    return h, inline_txt(t, ctx), [testo_puro(t)]


def b_immagine(b, ctx):
    """Foto di trattamento a tutta larghezza, angoli arrotondati e ombra. "alt" obbligatorio, "didascalia" facoltativa."""
    did = ""
    if b.get("didascalia"):
        did = ('<p class="t-sec" style="%s">%s</p>' % (stile(12, "1.5", C["C_SECONDARIO"], "text-align:center; margin-top:10px; font-weight:700; letter-spacing:0.3px;"), esc(b["didascalia"])))
    h = ('<table %s><tr><td style="border-radius:22px; box-shadow:0 24px 46px -24px rgba(0,37,82,0.55);">'
         '<img src="%s" width="528" alt="%s" style="display:block; width:100%%; max-width:100%%; height:auto; border:0; outline:none; '
         'text-decoration:none; border-radius:22px; font-family:%s; font-size:14px; font-weight:700; color:%s; background-color:#E6EAF0;">'
         '</td></tr></table>%s' % (TABELLA, attr(b["url"]), attr(b["alt"]), FONT, C["C_NOTTE"], did))
    return h, "", ([b["didascalia"]] if b.get("didascalia") else [])


BLOCCHI = {
    "immagine": b_immagine,
    "saluto": b_saluto,
    "paragrafo": b_testo,
    "chiusura": b_testo,
    "elenco": b_elenco,
    "confronto": b_confronto,
    "box": b_box,
    "riquadro": b_riquadro,
    "pulsante": b_pulsante,
    "nota": b_nota,
    "firma": b_firma,
    "ps": b_ps,
}


# --------------------------------------------------------------------------
# Tema "notte": email tutta scura come il sito (fondo inchiostro, verde menta)
# --------------------------------------------------------------------------


def striscia_notte_html(t, colore_punto=None):
    sep = ('<span style="display:inline-block; width:5px; height:5px; border-radius:50%%; background-color:%s; '
           'vertical-align:middle; margin:0 14px;"></span>' % (colore_punto or C["C_NERO"]))
    voci = t.get("fascia") or [t["striscia"], t["sconto"]]
    pezzo = sep.join(esc(x) for x in voci)
    return '<span class="tk-x">%s%s</span>%s' % (pezzo, sep, pezzo)


def testata_notte_html(t):
    v = C["C_VERDE"]
    righe = t["titolo"].split("|")
    h1 = "font-family:%s; font-size:52px; line-height:54px; font-weight:900; letter-spacing:-2px;" % FONT
    evid = ("background-image:linear-gradient(180deg, rgba(114,250,147,0) 58%, rgba(114,250,147,0.75) 58%, "
            "rgba(114,250,147,0.75) 92%, rgba(114,250,147,0) 92%);")
    def riga_titolo(i, r):
        if i == 0:
            return '<span class="h1n" style="%s color:%s;">%s</span>' % (h1, T["titolo"], esc(r))
        if T.get("scuro"):
            return '<span class="h1n" style="%s color:%s;">%s</span>' % (h1, v, esc(r))
        return '<span class="h1n" style="%s color:%s; %s">%s</span>' % (h1, T["titolo"], evid, esc(r))
    titolo = "<br>".join(riga_titolo(i, r) for i, r in enumerate(righe))
    celle = []
    for k, (val, lab) in enumerate(t["numeri"]):
        bordo = "" if k == 0 else " border-left:1px solid %s; padding-left:18px;" % T["linea"]
        celle.append(
            '<td valign="top" style="padding:20px 14px 0 0;%s">'
            '<span class="num-n" style="display:block; font-family:%s; font-size:40px; line-height:42px; font-weight:900; '
            'letter-spacing:-1.5px; color:%s; white-space:nowrap;">%s</span>'
            '<span style="display:block; margin-top:6px; font-family:%s; font-size:9.5px; line-height:13px; font-weight:800; '
            'letter-spacing:1.8px; color:%s;">%s</span></td>'
            % (bordo, FONT, v if (k == 1 and T.get("scuro")) else T["titolo"], esc(val), FONT, T["sec"], esc(lab)))
    return (
        '%s'
        '<p style="margin:22px 0 0 0;">%s</p>'
        '<table %s style="margin-top:34px;"><tr><td style="border-top:1px solid %s; '
        'font-size:0; line-height:0; height:1px;">&nbsp;</td></tr></table>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>%s</tr></table>'
    ) % (occhiello(t["etichetta"], v if T.get("scuro") else C["C_NOTTE"], v), titolo,
         TABELLA.replace(' style="width:100%;"', ""), T["linea"], "".join(celle))


def n_testo(b, ctx, testo=None):
    t = testo if testo is not None else b["testo"]
    if b.get("stile") == "evidenza":
        h = ('<table %s><tr><td align="center" style="padding:6px 0;">'
             '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center"><tr>'
             '<td width="40" height="3" bgcolor="%s" style="width:40px; height:3px; border-radius:2px; background-color:%s; '
             'font-size:0; line-height:0;">&nbsp;</td></tr></table>'
             '<p style="%s">%s</p></td></tr></table>'
             % (TABELLA, C["C_VERDE"], C["C_VERDE"],
                stile(28, "1.25", T["titolo"], "font-weight:900; letter-spacing:-0.8px; text-align:center; margin-top:18px;"),
                inline(t, ctx)))
    else:
        h = '<p style="%s">%s</p>' % (stile(16, "1.75"), inline(t, ctx))
    return h, inline_txt(t, ctx), [testo_puro(t)]


def n_saluto(b, ctx):
    return n_testo(b, ctx, b.get("testo", ctx.cfg["saluto"]))


def n_confronto(b, ctx):
    sx, dx = b["sinistra"], b["destra"]
    def card(lato, accesa):
        if accesa and not T.get("scuro"):
            fondo = ('bgcolor="%s" style="padding:22px 22px 24px 22px; border-radius:20px; background-color:%s; '
                     'background-image:radial-gradient(circle at 100%% 0%%, rgba(114,250,147,0.24) 0%%, rgba(114,250,147,0) 50%%), '
                     'linear-gradient(160deg, %s 0%%, %s 100%%); box-shadow:0 18px 36px -18px rgba(0,37,82,0.5);"'
                     % (C["C_NOTTE"], C["C_NOTTE"], C["C_NERO"], C["C_NOTTE"]))
            lab, linea, col = C["C_VERDE"], C["C_VERDE"], "#FFFFFF"
        elif accesa:
            fondo = ('bgcolor="#0B2A33" style="padding:22px 22px 24px 22px; border-radius:20px; background-color:#0B2A33; '
                     'background-image:linear-gradient(160deg, rgba(114,250,147,0.16) 0%%, rgba(114,250,147,0.04) 100%%); '
                     'border:1px solid rgba(114,250,147,0.45);"')
            lab, linea, col = C["C_VERDE"], C["C_VERDE"], "#FFFFFF"
        else:
            fondo = ('bgcolor="%s" style="padding:22px 22px 24px 22px; border-radius:20px; background-color:%s; '
                     'border:1px solid %s;"' % (T["card"], T["card"], T["bordo"]))
            lab, linea, col = T["sec"], "#B8C4D4" if not T.get("scuro") else "rgba(143,163,189,0.6)", T["sec"]
        return ('<td class="cf" valign="top" width="48%%" %s>%s<p style="%s">%s</p></td>'
                % (fondo, occhiello(lato["etichetta"], lab, linea), stile(15, "1.6", col, "margin-top:12px;"),
                   inline(lato["testo"], ctx)))
    h = ('<table %s><tr>%s<td class="cf-gap" width="4%%" style="width:4%%; min-width:12px; font-size:0; line-height:0;">&nbsp;</td>%s</tr></table>'
         % (TABELLA, card(sx, False), card(dx, True)))
    txt = "%s\n%s\n\n%s\n%s" % (sx["etichetta"], inline_txt(sx["testo"], ctx), dx["etichetta"], inline_txt(dx["testo"], ctx))
    return h, txt, [sx["etichetta"], testo_puro(sx["testo"]), dx["etichetta"], testo_puro(dx["testo"])]


def n_box(b, ctx):
    paragrafi = b["testo"].split("\n\n")
    parti = ['<p style="margin:0; font-family:%s; font-size:84px; line-height:56px; font-weight:900; color:%s;">&ldquo;</p>'
             % (FONT, C["C_VERDE"]), occhiello(b["etichetta"], C["C_VERDE"] if T.get("scuro") else C["C_NOTTE"], C["C_VERDE"])]
    for i, par in enumerate(paragrafi):
        ultimo = i == len(paragrafi) - 1
        parti.append('<p style="%s">%s</p>' % (
            stile(18 if ultimo else 16, "1.6", T["titolo"] if ultimo else T["testo"],
                  "margin-top:%dpx;%s" % (16 if i == 0 else 12, " font-weight:800;" if ultimo else "")),
            inline(par, ctx)))
    h = ('<table %s><tr><td bgcolor="%s" style="padding:26px 28px 30px 28px; background-color:%s; border:1px solid %s; '
         'border-radius:24px; background-image:radial-gradient(circle at 0%% 0%%, rgba(114,250,147,0.14) 0%%, rgba(114,250,147,0) 45%%);">'
         '%s</td></tr></table>' % (TABELLA, T["card"], T["card"], T["bordo"], "".join(parti)))
    txt = b["etichetta"] + "\n" + "\n\n".join(inline_txt(x, ctx) for x in paragrafi)
    return h, txt, [b["etichetta"]] + [testo_puro(x) for x in paragrafi]


def n_riquadro(b, ctx):
    """Offerta centrata: prezzo enorme con alone verde, schema delle visite, scadenza in una pillola."""
    righe = b["righe"]
    v = C["C_VERDE"]
    parti = []
    if b.get("etichetta"):
        parti.append('<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td>%s</td></tr></table>'
                     % occhiello(b["etichetta"], v, v))
    parti.append('<p style="%s">%s</p>' % (
        stile(18, "1.4", "#FFFFFF", "font-weight:800; text-align:center; margin-top:14px;"), inline(righe[0], ctx)))
    m = PREZZO.match(righe[1]) if len(righe) > 1 else None
    if m:
        parti.append(
            '<p style="%s"><span class="prezzo-n" style="font-size:88px; line-height:90px; font-weight:900; letter-spacing:-4px; '
            'color:#FFFFFF; text-shadow:0 0 42px rgba(114,250,147,0.55);">%s</span></p>'
            '<p style="%s">%s<span style="text-decoration:line-through;">%s</span>%s</p>'
            % (stile(16, "1", "#FFFFFF", "text-align:center; margin-top:12px;"), esc(m.group(1)),
               stile(17, "1.4", C["C_SU_SCURO"], "text-align:center; margin-top:6px; font-weight:700;"),
               esc(m.group(2)), esc(m.group(3)), esc(m.group(4))))
    elif len(righe) > 1:
        parti.append('<p style="%s">%s</p>' % (stile(16, "1.5", "#FFFFFF", "text-align:center; margin-top:8px;"), inline(righe[1], ctx)))
    if b.get("visite"):
        pagate, omaggio = b["visite"]
        celle = []
        for n in range(1, pagate + omaggio + 1):
            if n > 1:
                celle.append('<td width="5" style="width:5px; font-size:0; line-height:0;">&nbsp;</td>')
            if n <= pagate:
                st = "border:2px solid rgba(255,255,255,0.5); color:#FFFFFF; width:18px; height:18px; line-height:18px;"
            else:
                st = ("background-color:%s; color:%s; width:22px; height:22px; line-height:22px; "
                      "box-shadow:0 0 14px rgba(114,250,147,0.6);" % (v, C["C_NERO"]))
            celle.append('<td align="center" valign="middle" style="%s border-radius:50%%; font-family:%s; font-size:10px; '
                         'font-weight:900; text-align:center;">%d</td>' % (st, FONT, n))
        leg = b.get("legenda", ["", ""])
        voce = ('<td valign="middle" style="padding-right:8px;"><div style="width:10px; height:10px; border-radius:50%%; %s"></div></td>'
                '<td valign="middle" style="padding-right:16px; font-family:%s; font-size:10px; line-height:12px; font-weight:800; '
                'letter-spacing:1.8px; color:%s; white-space:nowrap;">%s</td>')
        parti.append(
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:22px;"><tr>%s</tr></table>'
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:10px;"><tr>%s%s</tr></table>'
            % ("".join(celle),
               voce % ("border:2px solid rgba(255,255,255,0.5); width:6px; height:6px;", FONT, C["C_SU_SCURO"], esc(leg[0])),
               voce % ("background-color:%s;" % v, FONT, v, esc(leg[1]))))
    for r in righe[2:]:
        parti.append(
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:24px;"><tr>'
            '<td style="padding:10px 18px; border-radius:999px; border:1px solid rgba(114,250,147,0.45); background-color:#0B2A33;">'
            '<p style="%s"><span style="display:inline-block; width:8px; height:8px; border-radius:50%%; background-color:%s; '
            'vertical-align:middle; margin-right:10px; box-shadow:0 0 0 4px rgba(114,250,147,0.22);"></span>%s</p>'
            '</td></tr></table>' % (stile(14, "1.4", v, "font-weight:800;"), v, inline(r, ctx)))
    h = ('<table %s><tr><td class="cp-n" align="center" bgcolor="%s" style="padding:34px 26px 34px 26px; background-color:%s; '
         'background-image:radial-gradient(circle at 50%% 0%%, rgba(114,250,147,0.22) 0%%, rgba(114,250,147,0) 55%%), '
         'linear-gradient(180deg, #06204A 0%%, %s 100%%); border:1px solid rgba(114,250,147,0.35); border-radius:28px; '
         'box-shadow:0 30px 60px -30px rgba(114,250,147,0.45);">%s</td></tr></table>'
         % (TABELLA, C["C_NOTTE"], C["C_NOTTE"], C["C_NERO"], "".join(parti)))
    txt = "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [testo_puro(r) for r in righe]


def n_nota(b, ctx):
    t = b["testo"]
    if b.get("stile") == "passi":
        return nota_passi(b, ctx)
    h = '<p style="%s">%s</p>' % (stile(14, "1.6", T["sec"], "text-align:center; font-weight:700;"), inline(t, ctx))
    return h, inline_txt(t, ctx), [testo_puro(t)]


def n_firma(b, ctx):
    t = b.get("testo", "Studio Mobilitas")
    h = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
         '<td width="32" height="3" bgcolor="%s" style="width:32px; height:3px; border-radius:2px; background-color:%s; '
         'font-size:0; line-height:0;">&nbsp;</td></tr></table><p style="%s">%s</p>'
         % (C["C_VERDE"], C["C_VERDE"], stile(17, "1.4", T["titolo"], "font-weight:800; margin-top:12px;"), inline(t, ctx)))
    return h, testo_puro(t), [testo_puro(t)]


def n_ps(b, ctx):
    t = b["testo"]
    sigla, corpo = ("P.S.", t[4:].lstrip()) if t.startswith("P.S.") else ("", t)
    cerchio = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
               '<td align="center" valign="middle" width="46" height="46" bgcolor="%s" style="width:46px; height:46px; '
               'border-radius:50%%; background-color:%s; font-family:%s; font-size:13px; line-height:46px; font-weight:900; '
               'color:%s; text-align:center; box-shadow:0 0 18px rgba(114,250,147,0.45);">%s</td></tr></table>'
               % (C["C_VERDE"], C["C_VERDE"], FONT, C["C_NERO"], esc(sigla))) if sigla else ""
    h = ('<table %s><tr><td bgcolor="%s" style="padding:22px 24px 22px 22px; background-color:%s; border:1px solid %s; '
         'border-radius:20px;"><table %s><tr><td class="ps-col" valign="top" width="62" style="width:62px;">%s</td>'
         '<td class="ps-txt" valign="middle"><p style="%s">%s</p></td></tr></table></td></tr></table>'
         % (TABELLA, T["card"], T["card"], T["bordo"], TABELLA, cerchio,
            stile(15, "1.65", extra="text-wrap:balance;"), inline(corpo, ctx)))
    return h, inline_txt(t, ctx), [testo_puro(t)]


BLOCCHI_NOTTE = {
    "saluto": n_saluto,
    "paragrafo": n_testo,
    "chiusura": n_testo,
    "confronto": n_confronto,
    "box": n_box,
    "riquadro": n_riquadro,
    "nota": n_nota,
    "firma": n_firma,
    "ps": n_ps,
}


# --------------------------------------------------------------------------
# Tema "centro": fondo bianco, testata centrata con barra di avanzamento (email 3)
# --------------------------------------------------------------------------
def testata_centro_html(t):
    v, n = C["C_VERDE"], C["C_NOTTE"]
    righe = t["titolo"].split("|")
    h1 = "font-family:%s; font-size:56px; line-height:58px; font-weight:900; letter-spacing:-2.2px;" % FONT
    titolo = "<br>".join(
        '<span class="h1c" style="%s color:%s;">%s</span>' % (h1, n if i == 0 else C["C_SECONDARIO"], esc(r))
        for i, r in enumerate(righe))
    pill = ('<span style="display:inline-block; padding:8px 16px; border-radius:999px; background-color:%s; '
            'font-family:%s; font-size:10px; line-height:12px; font-weight:900; letter-spacing:2.6px; color:%s; '
            'white-space:nowrap;">%s</span>' % (n, FONT, v, esc(t["pillola"])))
    occ = ('<p style="margin:18px 0 0 0; font-family:%s; font-size:10px; line-height:14px; font-weight:800; '
           'letter-spacing:2.6px; color:%s; text-align:center;">%s</p>' % (FONT, C["C_SECONDARIO"], esc(t["etichetta"])))
    # Barra di avanzamento: il lavoro fatto insieme, non ancora finito
    perc = int(t.get("avanzamento", 70))
    piccolo = ("font-family:%s; font-size:9.5px; line-height:12px; font-weight:800; letter-spacing:1.8px; color:%s;"
               % (FONT, C["C_SECONDARIO"]))
    barra = (
        '<table %s style="margin-top:34px;"><tr>'
        '<td width="%d%%" align="right" style="padding-bottom:8px;">'
        '<span style="display:inline-block; padding:5px 10px; border-radius:999px; background-color:%s; font-family:%s; '
        'font-size:9.5px; line-height:12px; font-weight:900; letter-spacing:1.8px; color:%s; white-space:nowrap;">%s</span></td><td width="%d%%" style="padding-bottom:8px;">&nbsp;</td></tr>'
        '<tr><td width="%d%%" height="12" bgcolor="%s" style="height:12px; background-color:%s; border-radius:999px 0 0 999px; '
        'background-image:linear-gradient(90deg, #B8FFCB 0%%, %s 100%%); box-shadow:0 0 16px rgba(114,250,147,0.55); '
        'font-size:0; line-height:0;">&nbsp;</td>'
        '<td width="%d%%" height="12" bgcolor="#E6EAF0" style="height:12px; background-color:#E6EAF0; border-radius:0 999px 999px 0; '
        'font-size:0; line-height:0;">&nbsp;</td></tr>'
        '<tr><td style="padding-top:8px; %s">%s</td><td align="right" style="padding-top:8px; text-align:right; %s">%s</td></tr>'
        '</table>'
    ) % (TABELLA.replace(' style="width:100%;"', ""), perc, n, FONT, v, esc(t.get("barra_qui", "SEI QUI")), 100 - perc,
         perc, v, v, v, 100 - perc, piccolo, esc(t.get("barra_inizio", "INIZIO")), piccolo, esc(t.get("barra_fine", "FINE")))
    # Numeri in tre tessere
    celle = []
    for k, (val, lab) in enumerate(t["numeri"]):
        if k:
            celle.append('<td class="tile-gap" width="3%" style="width:3%; font-size:0; line-height:0;">&nbsp;</td>')
        celle.append(
            '<td class="tile" align="center" valign="top" width="31%%" style="padding:0 6px 16px 6px; border:1px solid #E3E8EF; '
            'border-radius:18px; text-align:center;">'
            '<div style="width:28px; height:4px; margin:0 auto; border-radius:0 0 4px 4px; background-color:%s; font-size:0; line-height:0;">&nbsp;</div>'
            '<span class="num-c" style="display:block; margin-top:14px; font-family:%s; font-size:36px; line-height:38px; font-weight:900; '
            'letter-spacing:-1.2px; color:%s; white-space:nowrap;">%s</span>'
            '<span style="display:block; margin-top:6px; %s">%s</span></td>'
            % (v, FONT, n, esc(val), piccolo, esc(lab)))
    numeri = '<table %s style="margin-top:30px;"><tr>%s</tr></table>' % (TABELLA.replace(' style="width:100%;"', ""), "".join(celle))
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td align="center">%s</td></tr></table>'
        '%s<p style="margin:16px 0 0 0; text-align:center;">%s</p>%s%s'
    ) % (pill, occ, titolo, barra, numeri)


def n_box_variante(b, ctx):
    """Box del tema "centro": "spiegazione" (card bianca con bordo blu notte a sinistra)
    oppure "bastone" (una riga per frase, con un bastone verde a sinistra: la metafora della pianta)."""
    stile_box = b.get("stile")
    if stile_box not in ("spiegazione", "bastone"):
        return n_box(b, ctx)
    n, v = C["C_NOTTE"], C["C_VERDE"]
    occ = occhiello(b["etichetta"], n, v)
    if stile_box == "spiegazione":
        paragrafi = b["testo"].split("\n\n")
        parti = [occ]
        for i, par in enumerate(paragrafi):
            ultimo = i == len(paragrafi) - 1
            parti.append('<p style="%s">%s</p>' % (
                stile(17 if ultimo else 16, "1.65", n, "margin-top:%dpx;%s" % (14 if i == 0 else 12, " font-weight:800;" if ultimo else "")),
                inline(par, ctx)))
        h = ('<table %s><tr><td style="padding:26px 28px 28px 26px; background-color:#FFFFFF; border:1px solid #E3E8EF; '
             'border-left:6px solid %s; border-radius:20px; box-shadow:0 16px 36px -22px rgba(0,37,82,0.35);">%s</td></tr></table>'
             % (TABELLA, n, "".join(parti)))
        txt = b["etichetta"] + "\n" + "\n\n".join(inline_txt(x, ctx) for x in paragrafi)
        return h, txt, [b["etichetta"]] + [testo_puro(x) for x in paragrafi]
    # bastone
    righe = b["testo"].split("\n")
    parti = []
    for i, r in enumerate(righe):
        ultima = i == len(righe) - 1
        parti.append('<p style="%s">%s</p>' % (
            stile(18 if ultima else 17, "1.5", n, "margin-top:%dpx; font-weight:%d;" % (0 if i == 0 else 12, 800 if ultima else 600)),
            inline(r, ctx)))
    h = ('<table %s><tr><td bgcolor="%s" style="padding:26px 28px 28px 26px; background-color:%s; border:1px solid %s; border-radius:22px;">'
         '%s<table %s style="margin-top:18px;"><tr>'
         '<td width="6" style="width:6px; border-radius:999px; background-color:%s; background-image:linear-gradient(180deg, %s 0%%, #3FD86B 100%%); '
         'font-size:0; line-height:0;">&nbsp;</td><td width="20" style="width:20px; font-size:0; line-height:0;">&nbsp;</td>'
         '<td valign="top">%s</td></tr></table></td></tr></table>'
         % (TABELLA, C["C_VERDE_CHIARO"], C["C_VERDE_CHIARO"], C["C_VERDE_BORDO"], occ,
            TABELLA.replace(' style="width:100%;"', ""), v, v, "".join(parti)))
    txt = b["etichetta"] + "\n" + "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [b["etichetta"]] + [testo_puro(r) for r in righe]


def n_riquadro_variante(b, ctx):
    """Offerta "intestata": card bianca con bordo blu notte, intestazione scura e scadenza in fondo."""
    if b.get("stile") == "chiaro":
        return b_riquadro_chiaro(b, ctx)
    if b.get("stile") != "intestato":
        return n_riquadro(b, ctx)
    righe = b["righe"]
    n, v = C["C_NOTTE"], C["C_VERDE"]
    corpo = ['<p style="%s">%s</p>' % (stile(19, "1.4", n, "font-weight:800; text-align:center;"), inline(righe[0], ctx))]
    m = PREZZO.match(righe[1]) if len(righe) > 1 else None
    if m:
        corpo.append(
            '<p style="%s"><span class="prezzo-c" style="font-size:80px; line-height:84px; font-weight:900; letter-spacing:-3.5px; color:%s;">%s</span> '
            '<span style="white-space:nowrap; padding-left:4px;"><span style="font-size:17px; font-weight:700; color:%s;">%s</span>'
            '<span style="font-size:20px; font-weight:800; color:%s; text-decoration:line-through;">%s</span>'
            '<span style="font-size:17px; color:%s;">%s</span></span></p>'
            % (stile(16, "1.1", n, "text-align:center; margin-top:10px;"), n, esc(m.group(1)),
               C["C_SECONDARIO"], esc(m.group(2).lstrip()), C["C_SECONDARIO"], esc(m.group(3)), C["C_SECONDARIO"], esc(m.group(4))))
    if b.get("visite"):
        pagate, omaggio = b["visite"]
        celle = []
        for k in range(1, pagate + omaggio + 1):
            if k > 1:
                celle.append('<td width="4" style="width:4px; font-size:0; line-height:0;">&nbsp;</td>')
            if k <= pagate:
                st = "border:2px solid %s; color:%s; width:20px; height:20px; line-height:20px;" % (n, n)
            else:
                st = ("background-color:%s; color:%s; width:24px; height:24px; line-height:24px; "
                      "box-shadow:0 4px 12px rgba(114,250,147,0.6);" % (v, n))
            celle.append('<td class="pall-c" align="center" valign="middle" style="%s border-radius:50%%; font-family:%s; '
                         'font-size:11px; font-weight:900; text-align:center;">%d</td>' % (st, FONT, k))
        leg = b.get("legenda", ["", ""])
        voce = ('<td valign="middle" style="padding-right:8px;"><div style="width:10px; height:10px; border-radius:50%%; %s"></div></td>'
                '<td valign="middle" style="padding-right:16px; font-family:%s; font-size:10px; line-height:12px; font-weight:800; '
                'letter-spacing:1.8px; color:%s; white-space:nowrap;">%s</td>')
        corpo.append(
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:22px;"><tr>%s</tr></table>'
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:12px;"><tr>%s%s</tr></table>'
            % ("".join(celle),
               voce % ("border:2px solid %s; width:6px; height:6px;" % n, FONT, n, esc(leg[0])),
               voce % ("background-color:%s;" % v, FONT, n, esc(leg[1]))))
    scad = "".join('<p style="%s"><span style="display:inline-block; width:8px; height:8px; border-radius:50%%; background-color:%s; '
                   'vertical-align:middle; margin-right:10px; box-shadow:0 0 0 4px rgba(114,250,147,0.28);"></span>%s</p>'
                   % (stile(15, "1.4", n, "font-weight:800; text-align:center;"), v, inline(r, ctx)) for r in righe[2:])
    testa = (
        '<table %s><tr><td align="left" style="font-family:%s; font-size:10px; line-height:14px; font-weight:900; '
        'letter-spacing:2.6px; color:%s;">%s</td><td align="right" style="text-align:right; font-family:%s; font-size:16px; '
        'line-height:16px; font-weight:900; letter-spacing:-0.5px; color:#FFFFFF;">%s</td></tr></table>'
    ) % (TABELLA, FONT, v, esc(b.get("etichetta", "")), FONT, esc(ctx.testata.get("sconto", "")))
    h = (
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" style="width:100%%; border:2px solid %s; '
        'border-radius:24px; box-shadow:0 26px 50px -28px rgba(0,37,82,0.55);">'
        '<tr><td bgcolor="%s" style="padding:16px 24px; background-color:%s; border-radius:21px 21px 0 0; '
        'background-image:linear-gradient(90deg, %s 0%%, %s 100%%);">%s</td></tr>'
        '<tr><td class="cp-c" align="center" style="padding:30px 24px 26px 24px; background-color:#FFFFFF;">%s</td></tr>'
        '<tr><td bgcolor="%s" style="padding:16px 24px; background-color:%s; border-top:1px solid %s; border-radius:0 0 21px 21px;">%s</td></tr>'
        '</table>'
    ) % (n, n, n, C["C_NERO"], n, testa, "".join(corpo), C["C_VERDE_CHIARO"], C["C_VERDE_CHIARO"], C["C_VERDE_BORDO"], scad)
    txt = "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [testo_puro(r) for r in righe]


BLOCCHI_NOTTE["box"] = n_box_variante
BLOCCHI_NOTTE["riquadro"] = n_riquadro_variante


# --------------------------------------------------------------------------
# Aperture "funzionali" (email 2 e 3): titolo + sintesi dell'offerta + pulsante subito
# --------------------------------------------------------------------------
def _piccola(colore):
    return ("display:block; font-family:%s; font-size:9.5px; line-height:13px; font-weight:800; letter-spacing:2px; color:%s;"
            % (FONT, colore))


def _testata_intestazione(t, centrata):
    """Etichetta e titolo. Righe del titolo separate da "|": la prima blu notte, le altre con evidenziatore verde."""
    n = C["C_NOTTE"]
    righe = t["titolo"].split("|")
    h1 = "font-family:%s; font-size:50px; line-height:54px; font-weight:900; letter-spacing:-1.8px;" % FONT
    evid = ("background-image:linear-gradient(180deg, rgba(114,250,147,0) 60%, rgba(114,250,147,0.8) 60%, "
            "rgba(114,250,147,0.8) 92%, rgba(114,250,147,0) 92%);")
    titolo = "<br>".join(
        '<span class="h1f" style="%s color:%s;%s">%s</span>' % (h1, n, "" if i == 0 else " " + evid, esc(r))
        for i, r in enumerate(righe))
    allinea = "center" if centrata else "left"
    occ = ('<p style="margin:0; font-family:%s; font-size:10px; line-height:14px; font-weight:800; letter-spacing:2.6px; '
           'color:%s; text-align:%s;">%s</p>' % (FONT, C["C_SECONDARIO"], allinea, esc(t["etichetta"])))
    return '%s<p style="margin:16px 0 0 0; text-align:%s;">%s</p>' % (occ, allinea, titolo)


def testata_sintesi_html(t, ctx):
    """Email 2: titolo a sinistra + card scura con COSA / PREZZO / FINO A + pulsante dentro la card."""
    v = C["C_VERDE"]
    celle = []
    for k, voce in enumerate(t["sintesi"]):
        lab, val, sotto = voce[0], voce[1], voce[2]
        barrato = len(voce) > 3 and voce[3] == "barrato"
        bordo = "" if k == 0 else " border-left:1px solid rgba(255,255,255,0.14); padding-left:18px;"
        grande = k == 1
        celle.append(
            '<td class="sx" valign="top" style="padding:0 14px 0 0;%s">'
            '<span style="%s">%s</span>'
            '<span style="display:block; margin-top:8px; font-family:%s; font-size:%dpx; line-height:%dpx; font-weight:900; '
            'letter-spacing:%s; color:#FFFFFF; white-space:nowrap;">%s</span>'
            '<span style="display:block; margin-top:4px; font-family:%s; font-size:13px; line-height:18px; font-weight:700; '
            'color:%s;%s">%s</span></td>'
            % (bordo, _piccola(v), esc(lab), FONT, 40 if grande else 19, 42 if grande else 24,
               "-1.5px" if grande else "-0.3px", esc(val), FONT, C["C_SU_SCURO"],
               " text-decoration:line-through;" if barrato else "", esc(sotto)))
    puls, _, _ = b_pulsante({"testo": t["pulsante"], "link": "lp"}, ctx)
    card = (
        '<table %s style="margin-top:30px;"><tr><td class="cp-s" bgcolor="%s" style="padding:24px 26px 26px 26px; '
        'background-color:%s; background-image:radial-gradient(circle at 100%% 0%%, rgba(114,250,147,0.22) 0%%, '
        'rgba(114,250,147,0) 48%%), linear-gradient(160deg, %s 0%%, %s 100%%); border-radius:24px; '
        'box-shadow:0 24px 48px -26px rgba(0,37,82,0.6);">'
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"><tr>%s</tr></table>'
        '<table %s style="margin-top:22px;"><tr><td>%s</td></tr></table>'
        '</td></tr></table>'
    ) % (TABELLA.replace(' style="width:100%;"', ""), C["C_NOTTE"], C["C_NOTTE"], C["C_NERO"], C["C_NOTTE"],
         "".join(celle), TABELLA.replace(' style="width:100%;"', ""), puls)
    return _testata_intestazione(t, False) + card


def testata_traguardo_html(t, ctx):
    """Email 3: titolo centrato + linea con tre tappe (PRIMA, OGGI, IL TRAGUARDO) + pulsante + riga di sintesi."""
    n, v = C["C_NOTTE"], C["C_VERDE"]
    tappe = t["tappe"]
    def linea(stato):
        if stato == "vuota":
            return '<td width="50%" style="font-size:0; line-height:0;">&nbsp;</td>'
        if stato == "fatta":
            return ('<td width="50%%" valign="middle"><div style="height:3px; line-height:3px; font-size:0; background-color:%s;">'
                    '&nbsp;</div></td>' % v)
        return ('<td width="50%" valign="middle"><div style="height:0; line-height:0; font-size:0; '
                'border-top:3px dotted #C9D3E0;">&nbsp;</div></td>')
    cerchi = [
        ('background-color:#E6EAF0; border:2px solid #C9D3E0;', 18),
        ('background-color:%s; box-shadow:0 0 0 6px rgba(114,250,147,0.45);' % n, 22),
        ('background-color:%s; box-shadow:0 6px 14px rgba(114,250,147,0.6);' % v, 22),
    ]
    stati = [("vuota", "fatta"), ("fatta", "da_fare"), ("da_fare", "vuota")]
    riga_cerchi, riga_testi = [], []
    for k, (lab, testo) in enumerate(tappe):
        st, dim = cerchi[k]
        sx, dx = stati[k]
        riga_cerchi.append(
            '<td width="33%%" align="center"><table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"><tr>'
            '%s<td width="%d" align="center" valign="middle"><div style="width:%dpx; height:%dpx; border-radius:50%%; %s '
            'font-size:0; line-height:0;">&nbsp;</div></td>%s</tr></table></td>'
            % (linea(sx), dim + 12, dim, dim, st, linea(dx)))
        oggi = k == 1
        etichetta = ('<span style="display:inline-block; padding:4px 9px; border-radius:999px; background-color:%s; '
                     'font-family:%s; font-size:9px; line-height:11px; font-weight:900; letter-spacing:1.6px; color:%s;">%s</span>'
                     % (n, FONT, v, esc(lab))) if oggi else '<span style="%s">%s</span>' % (_piccola(C["C_SECONDARIO"]), esc(lab))
        riga_testi.append(
            '<td class="tl" width="33%%" align="center" valign="top" style="padding:14px 6px 0 6px; text-align:center;">%s'
            '<span class="tl-t" style="display:block; margin-top:8px; font-family:%s; font-size:14px; line-height:19px; '
            'font-weight:%d; color:%s;">%s</span></td>'
            % (etichetta, FONT, 800 if oggi else 700, n if k else C["C_SECONDARIO"], esc(testo)))
    linea_tempo = (
        '<table %s style="margin-top:34px;"><tr>%s</tr><tr>%s</tr></table>'
        % (TABELLA.replace(' style="width:100%;"', ""), "".join(riga_cerchi), "".join(riga_testi)))
    puls, _, _ = b_pulsante({"testo": t["pulsante"], "link": "lp"}, ctx)
    sintesi = ('<p style="margin:14px 0 0 0; font-family:%s; font-size:13px; line-height:1.5; font-weight:700; '
               'color:%s; text-align:center;">%s</p>' % (FONT, C["C_SECONDARIO"], esc(t["sintesi_riga"])))
    return (_testata_intestazione(t, True) + linea_tempo +
            '<table %s style="margin-top:34px;"><tr><td>%s%s</td></tr></table>'
            % (TABELLA.replace(' style="width:100%;"', ""), puls, sintesi))


# --------------------------------------------------------------------------
# Banner Black Friday (email 2 e 3): si capisce subito che è l'offerta Black Friday
# --------------------------------------------------------------------------
def _ticker(t, sfondo, colore, punto):
    sep = ('<span style="display:inline-block; width:5px; height:5px; border-radius:50%%; background-color:%s; '
           'vertical-align:middle; margin:0 14px;"></span>' % punto)
    pezzo = esc(t["striscia"]) + sep + esc(t["sconto"])
    return ('<tr><td align="center" bgcolor="%s" style="padding:12px 12px; background-color:%s; border-radius:0 0 22px 22px; '
            'box-shadow:inset 0 4px 8px -4px rgba(0,0,0,0.35); '
            'font-family:%s; font-size:10px; line-height:14px; font-weight:900; letter-spacing:3px; color:%s; white-space:nowrap;">'
            '<span class="tk-x">%s%s</span>%s</td></tr>' % (sfondo, sfondo, FONT, colore, pezzo, sep, pezzo))


def banner_nero_html(t):
    """Banner scuro: "−50%" enorme in verde a sinistra, "Black Friday" e i dati a destra, striscia verde sotto."""
    v = C["C_VERDE"]
    parole = t["titolo_bf"].split(" ", 1)
    return (
        '<table %s style="border-radius:22px; ' + OMBRA_BANNER.replace('%', '%%') + '">'
        '<tr><td class="bn-in" bgcolor="%s" style="padding:30px 30px 28px 30px; border-radius:22px 22px 0 0; background-color:%s; '
        'background-image:radial-gradient(circle at 0%% 0%%, rgba(114,250,147,0.30) 0%%, rgba(114,250,147,0) 45%%), '
        'linear-gradient(140deg, %s 0%%, %s 60%%, %s 100%%);%s">'
        '<table %s><tr>'
        '<td class="bn-c" valign="middle" width="48%%" style="padding-right:22px;">'
        '<span class="bn-pct" style="display:block; font-family:%s; font-size:100px; line-height:92px; font-weight:900; '
        'letter-spacing:-6px; color:%s; white-space:nowrap; ' + RILIEVO_VERDE + '">%s</span></td>'
        '<td class="bn-c bn-r" valign="middle" style="border-left:1px solid rgba(255,255,255,0.16); padding-left:26px;">'
        '<span style="display:block; font-family:%s; font-size:40px; line-height:38px; font-weight:900; letter-spacing:-1.5px; color:#FFFFFF; ' + RILIEVO_BIANCO + '">%s<br>%s</span>'
        '<span style="display:block; margin-top:14px; font-family:%s; font-size:14px; line-height:21px; font-weight:700; color:%s;">%s</span>'
        '</td></tr></table></td></tr>%s</table>'
    ) % (TABELLA.replace(' style="width:100%;"', ' width="100%"'), NERO_BF, NERO_BF, NERO_BF, C["C_NERO"], C["C_NOTTE"],
         con_foto(t, "radial-gradient(circle at 0% 0%, rgba(114,250,147,0.26) 0%, rgba(114,250,147,0) 45%), "
                     "linear-gradient(90deg, rgba(0,6,17,0.94) 0%, rgba(0,6,17,0.78) 40%, rgba(0,6,17,0.50) 100%)"),
         TABELLA,
         FONT, v, esc(t["sconto"]), FONT, esc(parole[0]), esc(parole[1] if len(parole) > 1 else ""),
         FONT, C["C_SU_SCURO"], "<br>".join('<span style="white-space:nowrap;">%s</span>' % esc(x) for x in t["dati_bf"]),
         _ticker(t, v, NERO_BF, NERO_BF))


def banner_verde_html(t):
    """Banner verde (il verde del sito): "Black Friday" blu notte enorme, bollino blu notte −50%, dati sotto."""
    n, v = C["C_NOTTE"], C["C_VERDE"]
    parole = t["titolo_bf"].split(" ", 1)
    bollino = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="right" style="transform:rotate(-8deg);"><tr>'
        '<td class="bn-boll" align="center" valign="middle" width="112" height="112" bgcolor="%s" style="width:112px; height:112px; '
        'border-radius:50%%; background-color:%s; text-align:center; ' + BOLLINO_NERO_3D.replace('%', '%%') + '">'
        '<span style="display:block; font-family:%s; font-size:9px; line-height:11px; font-weight:800; letter-spacing:2px; color:%s;">A METÀ</span>'
        '<span class="bn-boll-t" style="display:block; font-family:%s; font-size:31px; line-height:34px; font-weight:900; letter-spacing:-1.5px; color:#FFFFFF; white-space:nowrap;">%s</span>'
        '<span style="display:block; font-family:%s; font-size:9px; line-height:11px; font-weight:800; letter-spacing:2px; color:%s;">PREZZO</span>'
        '</td></tr></table>') % (NERO_BF, NERO_BF, FONT, v, FONT, esc(t["sconto"]), FONT, v)
    sep_dati = '<span style="display:inline-block; width:5px; height:5px; border-radius:50%%; background-color:%s; vertical-align:middle; margin:0 10px;"></span>' % NERO_BF
    dati = ('<td style="padding:14px 0 0 0; font-family:%s; font-size:14px; line-height:22px; font-weight:800; color:%s;">%s</td>'
            % (FONT, NERO_BF, sep_dati.join('<span style="white-space:nowrap;">%s</span>' % esc(x) for x in t["dati_bf"])))
    return (
        '<table %s style="border-radius:22px; box-shadow:0 36px 64px -28px rgba(0,6,17,0.55), 0 16px 34px -16px rgba(46,170,90,0.85), inset 0 1px 0 rgba(255,255,255,0.6);">'
        '<tr><td class="bn-in" bgcolor="%s" style="padding:28px 30px 24px 30px; border-radius:22px 22px 0 0; background-color:%s; '
        'background-image:linear-gradient(135deg, %s 0%%, #B5FFC9 100%%);%s">'
        '<table %s><tr>'
        '<td valign="middle"><span class="bn-wm" style="display:block; font-family:%s; font-size:66px; line-height:60px; font-weight:900; '
        'letter-spacing:-2.6px; color:%s; ' + RILIEVO_NERO + '">%s<br>%s</span></td>'
        '<td class="bn-bc" valign="middle" width="130" style="width:130px;">%s</td></tr></table>'
        '<table %s style="margin-top:20px;"><tr><td style="border-top:1px solid rgba(0,37,82,0.18); font-size:0; line-height:0; height:1px;">&nbsp;</td></tr></table>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>%s</tr></table>'
        '</td></tr>%s</table>'
    ) % (TABELLA.replace(' style="width:100%;"', ' width="100%"'), v, v, v,
         con_foto(t, "linear-gradient(100deg, rgba(114,250,147,0.97) 0%, rgba(114,250,147,0.90) 45%, rgba(150,255,180,0.66) 100%)"),
         TABELLA, FONT, NERO_BF, esc(parole[0]),
         esc(parole[1] if len(parole) > 1 else ""), bollino,
         TABELLA.replace(' style="width:100%;"', ""), dati, _ticker(t, NERO_BF, "#FFFFFF", v))


def testata_banner_html(t):
    """Banner Black Friday + titolo dell'email subito sotto, sul bianco."""
    banner = (banner_verde_html(t) if t.get("banner") == "verde" else
              banner_calendario_html(t) if t.get("banner") == "calendario" else
              banner_orologio_html(t) if t.get("banner") == "orologio" else banner_nero_html(t))
    centrata = t.get("allinea") == "centro"
    n = C["C_NOTTE"]
    righe = t["titolo"].split("|")
    h1 = "font-family:%s; font-size:38px; line-height:44px; font-weight:900; letter-spacing:-1.3px;" % FONT
    evid = EVIDENZIATORE
    titolo = "<br>".join('<span class="h1b" style="%s color:%s;%s">%s</span>' % (h1, n, "" if i == 0 else " " + evid, esc(r))
                         for i, r in enumerate(righe))
    return '%s<p style="margin:36px 0 0 0; text-align:%s;">%s</p>' % (banner, "center" if centrata else "left", titolo)


# --------------------------------------------------------------------------
# Email 4 (il giorno del Black Friday): banner calendario, box della macchia, offerta a scontrino
# --------------------------------------------------------------------------
def banner_calendario_html(t):
    """Banner nero con un foglio di calendario in rilievo (il giorno dell'invio) e "Black Friday"."""
    v, n = C["C_VERDE"], C["C_NOTTE"]
    cal = t["calendario"]          # [mese, giorno, giorno della settimana]
    foglio = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="left" style="transform:rotate(-6deg); '
        'border-radius:16px; box-shadow:0 22px 40px -10px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.08);">'
        '<tr><td class="cal-w" align="center" bgcolor="%s" style="width:124px; padding:8px 0; border-radius:16px 16px 0 0; '
        'background-color:%s; background-image:linear-gradient(180deg, #A6FFBE 0%%, %s 100%%); font-family:%s; font-size:10px; '
        'line-height:12px; font-weight:900; letter-spacing:2.4px; color:%s; text-align:center;">%s</td></tr>'
        '<tr><td align="center" bgcolor="#FFFFFF" style="padding:6px 0 12px 0; border-radius:0 0 16px 16px; background-color:#FFFFFF; '
        'text-align:center; box-shadow:inset 0 -5px 0 rgba(0,37,82,0.10);">'
        '<span class="cal-g" style="display:block; font-family:%s; font-size:64px; line-height:66px; font-weight:900; '
        'letter-spacing:-3px; color:%s;">%s</span>'
        '<span style="display:block; font-family:%s; font-size:10px; line-height:12px; font-weight:800; letter-spacing:2.2px; '
        'color:%s;">%s</span></td></tr></table>'
    ) % (v, v, v, FONT, NERO_BF, esc(cal[0]), FONT, n, esc(cal[1]), FONT, C["C_SECONDARIO"], esc(cal[2]))
    parole = t["titolo_bf"].split(" ", 1)
    pillola = ('<span style="display:inline-block; padding:8px 16px; border-radius:999px; background-color:%s; '
               'background-image:linear-gradient(180deg, #A6FFBE 0%%, %s 100%%); font-family:%s; font-size:24px; line-height:26px; '
               'font-weight:900; letter-spacing:-1px; color:%s; white-space:nowrap; '
               'box-shadow:0 10px 22px -8px rgba(114,250,147,0.8), inset 0 2px 0 rgba(255,255,255,0.7), inset 0 -3px 0 rgba(0,37,82,0.15);">%s</span>'
               % (v, v, FONT, NERO_BF, esc(t["sconto"])))
    destra = (
        '<span style="display:block; font-family:%s; font-size:11px; line-height:14px; font-weight:900; letter-spacing:2.6px; color:%s;">%s</span>'
        '<span class="cal-bf" style="display:block; margin-top:8px; font-family:%s; font-size:48px; line-height:46px; font-weight:900; '
        'letter-spacing:-1.8px; color:#FFFFFF; %s">%s<br>%s</span>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:16px;"><tr>'
        '<td valign="middle">%s</td>'
        '<td class="tk-x" valign="middle" style="padding-left:14px; font-family:%s; font-size:13px; line-height:18px; font-weight:700; color:%s;">%s</td>'
        '</tr></table>'
    ) % (FONT, v, esc(t["sopra_bf"]), FONT, RILIEVO_BIANCO, esc(parole[0]), esc(parole[1] if len(parole) > 1 else ""),
         pillola, FONT, C["C_SU_SCURO"], "<br>".join(esc(x) for x in t["dati_bf"]))
    sep = ('<span style="display:inline-block; width:5px; height:5px; border-radius:50%%; background-color:%s; '
           'vertical-align:middle; margin:0 14px;"></span>' % NERO_BF)
    pezzo = sep.join(esc(x) for x in t["fascia"])
    return (
        '<table %s style="border-radius:22px; %s">'
        '<tr><td class="bn-in" bgcolor="%s" style="padding:32px 30px 30px 30px; border-radius:22px 22px 0 0; background-color:%s;%s">'
        '<table %s><tr>'
        '<td class="cal-c" valign="middle" width="160" style="width:160px;">%s</td>'
        '<td valign="middle">%s</td>'
        '</tr></table></td></tr>'
        '<tr><td align="center" bgcolor="#FFFFFF" style="padding:12px 12px; border-radius:0 0 22px 22px; background-color:#FFFFFF; '
        'border:2px solid %s; border-top:0; font-family:%s; font-size:10px; line-height:14px; font-weight:900; letter-spacing:3px; '
        'color:%s; white-space:nowrap;">%s</td></tr>'
        '</table>'
    ) % (TABELLA.replace(' style="width:100%;"', ' width="100%"'), OMBRA_BANNER, NERO_BF, NERO_BF,
         con_foto(t, "radial-gradient(circle at 12% 30%, rgba(114,250,147,0.28) 0%, rgba(114,250,147,0) 40%), "
                     "linear-gradient(90deg, rgba(0,6,17,0.80) 0%, rgba(0,6,17,0.88) 45%, rgba(0,6,17,0.80) 100%)"),
         TABELLA, foglio, destra, NERO_BF, FONT, NERO_BF,
         # testo lungo: una volta sola; testo corto: ripetuto su computer
         pezzo if len(" ".join(t["fascia"])) > 18 else '<span class="tk-x">%s%s</span>%s' % (pezzo, sep, pezzo))


def n_box_macchia(b, ctx):
    """Box "macchia": introduzione, due righe a confronto (subito = punto verde, se aspetti = macchia nera), chiusura su fascia scura."""
    n, v = C["C_NOTTE"], C["C_VERDE"]
    parti = [occhiello(b["etichetta"], n, v)]
    intro = b["intro"].split("\n")
    for i, r in enumerate(intro):
        parti.append('<p style="%s">%s</p>' % (stile(16, "1.6", n, "margin-top:%dpx;" % (14 if i == 0 else 8)), inline(r, ctx)))
    def riga(icona, testo, forte):
        return ('<tr><td valign="top" width="44" style="width:44px; padding-top:2px;">%s</td>'
                '<td valign="top"><p style="%s">%s</p></td></tr>'
                % (icona, stile(16, "1.5", n, "font-weight:%d;" % (800 if forte else 600)), inline(testo, ctx)))
    pulito = ('<div style="width:26px; height:26px; border-radius:50%%; background-color:%s; '
              'box-shadow:0 0 0 5px rgba(114,250,147,0.25), 0 6px 12px -4px rgba(46,170,90,0.7); font-size:0; line-height:0;">&nbsp;</div>' % v)
    macchia = ('<div style="width:30px; height:26px; border-radius:58%% 42%% 55%% 45%% / 50%% 60%% 40%% 50%%; background-color:%s; '
               'box-shadow:6px 4px 0 -2px rgba(0,6,17,0.55), 0 8px 14px -4px rgba(0,6,17,0.6); font-size:0; line-height:0;">&nbsp;</div>' % NERO_BF)
    confronto = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:20px;">%s'
                 '<tr><td colspan="2" style="height:14px; font-size:0; line-height:0;">&nbsp;</td></tr>%s</table>'
                 % (riga(pulito, b["subito"], False), riga(macchia, b["aspetti"], True)))
    parti.append(confronto)
    chiusura = ('<table %s style="margin-top:22px;"><tr><td bgcolor="%s" style="padding:16px 20px; border-radius:14px; background-color:%s; '
                'background-image:linear-gradient(135deg, %s 0%%, %s 100%%); box-shadow:0 14px 28px -16px rgba(0,6,17,0.8);">'
                '<p style="%s">%s</p></td></tr></table>'
                % (TABELLA.replace(' style="width:100%;"', ""), NERO_BF, NERO_BF, NERO_BF, n,
                   stile(17, "1.45", "#FFFFFF", "font-weight:800;"), inline(b["chiusura"], ctx)))
    parti.append(chiusura)
    h = ('<table %s><tr><td style="padding:26px 26px 26px 26px; background-color:#FFFFFF; border:1px solid #E3E8EF; border-radius:22px; '
         'box-shadow:0 20px 40px -26px rgba(0,37,82,0.45);">%s</td></tr></table>' % (TABELLA, "".join(parti)))
    righe = intro + [b["subito"], b["aspetti"], b["chiusura"]]
    txt = b["etichetta"] + "\n" + "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [b["etichetta"]] + [testo_puro(r) for r in righe]


def n_riquadro_scontrino(b, ctx):
    """Offerta come scontrino: il conto 10 × 90€ = 900€, lo sconto Black Friday, il totale 450€."""
    righe = b["righe"]
    n, v = C["C_NOTTE"], C["C_VERDE"]
    voce = ('<tr><td style="padding:10px 0; font-family:%s; font-size:14px; line-height:18px; font-weight:700; color:%s;">%s</td>'
            '<td width="22%%" style="padding:10px 8px; border-bottom:2px dotted #C9D3E0;">&nbsp;</td>'
            '<td align="right" style="padding:10px 0; text-align:right; font-family:%s; font-size:16px; line-height:18px; font-weight:900; '
            'color:%s; white-space:nowrap;%s">%s</td></tr>')
    conto = "".join(voce % (FONT, n, esc(lab), FONT, col, extra, esc(val)) for lab, val, col, extra in [
        (b["conto"][0][0], b["conto"][0][1], C["C_SECONDARIO"], " text-decoration:line-through;"),
        (b["conto"][1][0], b["conto"][1][1], "#0E8A45", ""),
    ])
    pall = []
    if b.get("visite"):
        pagate, omaggio = b["visite"]
        for k in range(1, pagate + omaggio + 1):
            if k > 1:
                pall.append('<td width="4" style="width:4px; font-size:0; line-height:0;">&nbsp;</td>')
            st = ("border:2px solid %s; color:%s; width:20px; height:20px; line-height:20px;" % (n, n) if k <= pagate else
                  "background-color:%s; color:%s; width:24px; height:24px; line-height:24px; box-shadow:0 4px 12px rgba(114,250,147,0.6);" % (v, n))
            pall.append('<td align="center" valign="middle" style="%s border-radius:50%%; font-family:%s; font-size:11px; font-weight:900; '
                        'text-align:center;">%d</td>' % (st, FONT, k))
    leg = b.get("legenda", ["", ""])
    legenda = ('<td valign="middle" style="padding-right:8px;"><div style="width:6px; height:6px; border-radius:50%%; border:2px solid %s;"></div></td>'
               '<td valign="middle" style="padding-right:16px; font-family:%s; font-size:10px; font-weight:800; letter-spacing:1.8px; color:%s;">%s</td>'
               '<td valign="middle" style="padding-right:8px;"><div style="width:10px; height:10px; border-radius:50%%; background-color:%s;"></div></td>'
               '<td valign="middle" style="font-family:%s; font-size:10px; font-weight:800; letter-spacing:1.8px; color:%s;">%s</td>'
               % (n, FONT, n, esc(leg[0]), v, FONT, n, esc(leg[1])))
    m = PREZZO.match(righe[1])
    totale_val = esc(m.group(1)) if m else esc(righe[1])
    corpo = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td>%s</td></tr></table>'
        '<p style="%s">%s</p>'
        '<table %s style="margin-top:18px;">%s</table>'
        '<table %s style="margin-top:6px;"><tr><td style="border-top:3px double %s; font-size:0; line-height:0; height:3px;">&nbsp;</td></tr></table>'
        '<table %s style="margin-top:10px;"><tr>'
        '<td valign="bottom" style="font-family:%s; font-size:12px; line-height:14px; font-weight:900; letter-spacing:2.6px; color:%s; padding-bottom:12px;">%s</td>'
        '<td align="right" valign="bottom" style="text-align:right;"><span class="prezzo-c" style="display:block; font-family:%s; font-size:64px; '
        'line-height:66px; font-weight:900; letter-spacing:-3px; color:%s; %s">%s</span></td></tr></table>'
        '<p style="%s">%s</p>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:20px;"><tr>%s</tr></table>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:10px;"><tr>%s</tr></table>'
    ) % (occhiello(b.get("etichetta", ""), n, v),
         stile(18, "1.4", n, "font-weight:800; text-align:center; margin-top:14px;"), inline(righe[0], ctx),
         TABELLA.replace(' style="width:100%;"', ""), conto,
         TABELLA.replace(' style="width:100%;"', ""), n,
         TABELLA.replace(' style="width:100%;"', ""), FONT, n, esc(b.get("totale", "TOTALE")),
         FONT, n, "text-shadow:0 3px 0 rgba(114,250,147,0.9);", totale_val,
         stile(14, "1.4", C["C_SECONDARIO"], "text-align:right; font-weight:700; margin-top:2px;"), esc(righe[1]),
         "".join(pall), legenda)
    scad = "".join('<p style="%s"><span style="display:inline-block; width:8px; height:8px; border-radius:50%%; background-color:%s; '
                   'vertical-align:middle; margin-right:10px; box-shadow:0 0 10px rgba(114,250,147,0.9);"></span>%s</p>'
                   % (stile(14, "1.4", "#FFFFFF", "font-weight:800; text-align:center;"), v, inline(r, ctx)) for r in righe[2:])
    h = (
        '<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" style="width:100%%; max-width:460px; margin:0 auto; '
        'border-radius:18px; box-shadow:0 30px 56px -28px rgba(0,37,82,0.6), 0 2px 0 rgba(0,37,82,0.06);">'
        '<tr><td class="cp-c" style="padding:26px 28px 22px 28px; background-color:#FFFFFF; border:1px solid #E3E8EF; border-bottom:0; '
        'border-radius:18px 18px 0 0;">%s</td></tr>'
        '<tr><td bgcolor="%s" style="padding:16px 24px; background-color:%s; border-radius:0 0 18px 18px;">%s</td></tr>'
        '</table>'
    ) % (corpo, NERO_BF, NERO_BF, scad)
    txt = "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [testo_puro(r) for r in righe]


_box_prec = BLOCCHI_NOTTE["box"]
_riq_prec = BLOCCHI_NOTTE["riquadro"]
BLOCCHI_NOTTE["box"] = lambda b, ctx: n_box_macchia(b, ctx) if b.get("stile") == "macchia" else _box_prec(b, ctx)
BLOCCHI_NOTTE["riquadro"] = lambda b, ctx: n_riquadro_scontrino(b, ctx) if b.get("stile") == "scontrino" else _riq_prec(b, ctx)


def n_riquadro_prezzi(b, ctx):
    """Offerta semplice: due tessere affiancate DI SOLITO 900€ -> BLACK FRIDAY 450€, cerchi delle visite, scadenza."""
    righe = b["righe"]
    n, v = C["C_NOTTE"], C["C_VERDE"]
    piccola = "display:block; font-family:%s; font-size:9.5px; line-height:12px; font-weight:900; letter-spacing:2px; color:%s;"
    prima, dopo = b["prima"], b["dopo"]
    tessera_a = (
        '<td class="pz-t" valign="middle" align="center" width="44%%" bgcolor="%s" style="padding:18px 10px; border-radius:18px; '
        'background-color:%s; text-align:center;">'
        '<span style="%s">%s</span>'
        '<span class="pz-o" style="display:block; margin-top:8px; font-family:%s; font-size:34px; line-height:36px; font-weight:900; '
        'letter-spacing:-1.5px; color:#8FA3BD; text-decoration:line-through; white-space:nowrap;">%s</span>'
        '<span style="display:block; margin-top:6px; font-family:%s; font-size:13px; line-height:16px; font-weight:700; color:%s;">%s</span></td>'
    ) % (C["C_CREMA"], C["C_CREMA"], piccola % (FONT, C["C_SECONDARIO"]), esc(prima[0]), FONT, esc(prima[1]),
         FONT, C["C_SECONDARIO"], esc(prima[2]))
    freccia = (
        '<td valign="middle" align="center" width="12%%" style="text-align:center;">'
        '<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;"><tr>'
        '<td align="center" valign="middle" width="34" height="34" bgcolor="%s" style="width:34px; height:34px; border-radius:50%%; '
        'background-color:%s; box-shadow:0 6px 12px -4px rgba(0,6,17,0.5); font-size:0; line-height:0;">'
        '<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;"><tr>'
        '<td valign="middle" style="font-size:0; line-height:0;"><div style="width:9px; height:3px; background-color:%s; font-size:0; line-height:0;">&nbsp;</div></td>'
        '<td valign="middle" style="font-size:0; line-height:0;"><div style="width:0; height:0; border-top:6px solid transparent; '
        'border-bottom:6px solid transparent; border-left:8px solid %s; font-size:0; line-height:0;"></div></td>'
        '</tr></table></td></tr></table></td>'
    ) % (NERO_BF, NERO_BF, v, v)
    tessera_b = (
        '<td class="pz-t" valign="middle" align="center" width="44%%" bgcolor="%s" style="padding:18px 10px; border-radius:18px; '
        'background-color:%s; background-image:radial-gradient(circle at 50%% 0%%, rgba(114,250,147,0.28) 0%%, rgba(114,250,147,0) 60%%), '
        'linear-gradient(160deg, %s 0%%, %s 100%%); text-align:center; box-shadow:0 18px 34px -16px rgba(0,6,17,0.75);">'
        '<span style="%s">%s</span>'
        '<span class="pz-v" style="display:block; margin-top:6px; font-family:%s; font-size:46px; line-height:48px; font-weight:900; '
        'letter-spacing:-2px; color:#FFFFFF; white-space:nowrap; %s">%s</span>'
        '<span style="display:block; margin-top:6px; font-family:%s; font-size:13px; line-height:16px; font-weight:700; color:%s;">%s</span></td>'
    ) % (NERO_BF, NERO_BF, NERO_BF, n, piccola % (FONT, v), esc(dopo[0]), FONT, RILIEVO_BIANCO, esc(dopo[1]),
         FONT, C["C_SU_SCURO"], esc(dopo[2]))
    pall = []
    if b.get("visite"):
        pagate, omaggio = b["visite"]
        for k in range(1, pagate + omaggio + 1):
            if k > 1:
                pall.append('<td width="4" style="width:4px; font-size:0; line-height:0;">&nbsp;</td>')
            st = ("border:2px solid %s; color:%s; width:20px; height:20px; line-height:20px;" % (n, n) if k <= pagate else
                  "background-color:%s; color:%s; width:24px; height:24px; line-height:24px; box-shadow:0 4px 12px rgba(114,250,147,0.6);" % (v, n))
            pall.append('<td align="center" valign="middle" style="%s border-radius:50%%; font-family:%s; font-size:11px; font-weight:900; '
                        'text-align:center;">%d</td>' % (st, FONT, k))
    leg = b.get("legenda", ["", ""])
    legenda = ('<td valign="middle" style="padding-right:8px;"><div style="width:6px; height:6px; border-radius:50%%; border:2px solid %s;"></div></td>'
               '<td valign="middle" style="padding-right:16px; font-family:%s; font-size:10px; font-weight:800; letter-spacing:1.8px; color:%s;">%s</td>'
               '<td valign="middle" style="padding-right:8px;"><div style="width:10px; height:10px; border-radius:50%%; background-color:%s;"></div></td>'
               '<td valign="middle" style="font-family:%s; font-size:10px; font-weight:800; letter-spacing:1.8px; color:%s;">%s</td>'
               % (n, FONT, n, esc(leg[0]), v, FONT, n, esc(leg[1])))
    scad = "".join('<p style="%s"><span style="display:inline-block; width:8px; height:8px; border-radius:50%%; background-color:%s; '
                   'vertical-align:middle; margin-right:10px; box-shadow:0 0 0 4px rgba(114,250,147,0.3);"></span>%s</p>'
                   % (stile(14, "1.5", n, "font-weight:800; text-align:center; margin-top:18px;"), v, inline(r, ctx)) for r in righe[2:])
    corpo = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td>%s</td></tr></table>'
        '<p style="%s">%s</p>'
        '<table %s style="margin-top:20px;"><tr>%s%s%s</tr></table>'
        '<p style="%s">%s</p>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:18px;"><tr>%s</tr></table>'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin-top:10px;"><tr>%s</tr></table>%s'
    ) % (occhiello(b.get("etichetta", ""), n, v),
         stile(18, "1.4", n, "font-weight:800; text-align:center; margin-top:14px;"), inline(righe[0], ctx),
         TABELLA.replace(' style="width:100%;"', ""), tessera_a, freccia, tessera_b,
         stile(13, "1.4", C["C_SECONDARIO"], "font-weight:700; text-align:center; margin-top:12px;"), esc(righe[1]),
         "".join(pall), legenda, scad)
    h = ('<table %s><tr><td class="cp-c" style="padding:26px 22px 24px 22px; background-color:#FFFFFF; border:1px solid #E3E8EF; '
         'border-radius:24px; box-shadow:0 26px 50px -30px rgba(0,37,82,0.5);">%s</td></tr></table>' % (TABELLA, corpo))
    txt = "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [testo_puro(r) for r in righe]


_riq_prec2 = BLOCCHI_NOTTE["riquadro"]
BLOCCHI_NOTTE["riquadro"] = lambda b, ctx: n_riquadro_prezzi(b, ctx) if b.get("stile") == "prezzi" else _riq_prec2(b, ctx)


# --------------------------------------------------------------------------
# Benefici a contrasto (tutte le email) e banner "orologio" (email 5)
# --------------------------------------------------------------------------
def b_benefici(b, ctx):
    """Benefici polarizzanti: per ogni voce [no, si, spiegazione] -> "no" barrato in grigio, "si" in grassetto
    con evidenziatore verde, spiegazione sotto. Card bianca con bordo sottile."""
    n, v = C["C_NOTTE"], C["C_VERDE"]
    parti = [occhiello(b["etichetta"], n, v, "t-main")]
    attesi = [b["etichetta"]]
    txt = [b["etichetta"]]
    if b.get("titolo"):
        parti.append('<p class="t-main" style="%s">%s</p>' % (
            stile(20, "1.35", n, "font-weight:800; letter-spacing:-0.3px; margin-top:12px;"), inline(b["titolo"], ctx)))
        attesi.append(testo_puro(b["titolo"]))
        txt.append(testo_puro(b["titolo"]))
    righe = []
    for k, (no, si, spieg) in enumerate(b["voci"]):
        sep = "" if k == 0 else " border-top:1px solid %s;" % C["C_BORDO"]
        righe.append(
            '<tr><td class="sep" style="padding:16px 0;%s">'
            '<p class="t-sec" style="%s">%s</p>'
            '<p class="t-main" style="%s"><span style="%s">%s</span></p>'
            '<p class="t-main" style="%s">%s</p></td></tr>'
            % (sep,
               stile(13, "1.4", "#8FA3BD", "font-weight:700; text-decoration:line-through;"), inline(no, ctx),
               stile(19, "1.35", n, "font-weight:900; letter-spacing:-0.4px; margin-top:4px;"), EVIDENZIATORE, inline(si, ctx),
               stile(15, "1.55", n, "margin-top:6px;"), inline(spieg, ctx)))
        attesi += [testo_puro(no), testo_puro(si), testo_puro(spieg)]
        txt += ["", testo_puro(no) + " → " + testo_puro(si), inline_txt(spieg, ctx)]
    parti.append('<table %s style="margin-top:6px;">%s</table>' % (TABELLA.replace(' style="width:100%;"', ""), "".join(righe)))
    h = ('<table %s><tr><td class="card-motivi" bgcolor="#FFFFFF" style="padding:24px 26px 10px 26px; background-color:#FFFFFF; '
         'border:1px solid %s; border-radius:22px; box-shadow:0 18px 40px -28px rgba(0,37,82,0.45);">%s</td></tr></table>'
         % (TABELLA, C["C_BORDO"], "".join(parti)))
    return h, "\n".join(txt), attesi


def banner_orologio_html(t):
    """Banner nero con un orologio a cifre in rilievo (23:59): l'ultima email, la scadenza vera."""
    v = C["C_VERDE"]
    ore, minuti = t["orologio"]
    def tessera(cifre):
        return ('<td class="ck-t" align="center" valign="middle" bgcolor="#0B1220" style="padding:10px 16px; border-radius:16px; '
                'background-color:#0B1220; background-image:linear-gradient(180deg, #24344D 0%%, #0B1424 49%%, #000611 50%%, #0B1424 51%%, #05080F 100%%); '
                'box-shadow:0 18px 32px -10px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.18), inset 0 -3px 0 rgba(0,0,0,0.6); '
                'font-family:%s; font-size:78px; line-height:80px; font-weight:900; letter-spacing:-2px; color:#FFFFFF; '
                'text-shadow:0 3px 0 rgba(0,0,0,0.6), 0 0 24px rgba(255,255,255,0.15);">%s</td>' % (FONT, esc(cifre)))
    due_punti = ('<td class="ck-p" align="center" valign="middle" style="padding:0 10px; font-family:%s; font-size:64px; line-height:64px; '
                 'font-weight:900; color:%s; text-shadow:0 0 18px rgba(114,250,147,0.9);">:</td>' % (FONT, v))
    pillola = ('<span style="display:inline-block; padding:8px 16px; border-radius:999px; background-color:%s; '
               'background-image:linear-gradient(180deg, #A6FFBE 0%%, %s 100%%); font-family:%s; font-size:11px; line-height:13px; '
               'font-weight:900; letter-spacing:2.6px; color:%s; box-shadow:0 8px 18px -6px rgba(114,250,147,0.8), '
               'inset 0 2px 0 rgba(255,255,255,0.7);">%s</span>' % (v, v, FONT, NERO_BF, esc(t["pillola_bf"])))
    sep = ('<span style="display:inline-block; width:5px; height:5px; border-radius:50%%; background-color:%s; '
           'vertical-align:middle; margin:0 14px;"></span>' % NERO_BF)
    pezzo = sep.join(esc(x) for x in t["fascia"])
    return (
        '<table %s style="border-radius:22px; %s">'
        '<tr><td class="bn-in" align="center" bgcolor="%s" style="padding:30px 24px 30px 24px; border-radius:22px 22px 0 0; '
        'background-color:%s; text-align:center;%s">'
        '%s'
        '<p style="margin:14px 0 0 0; font-family:%s; font-size:12px; line-height:16px; font-weight:800; letter-spacing:2.4px; '
        'color:#FFFFFF; text-align:center;">%s</p>'
        '<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" style="margin:20px auto 0 auto;"><tr>%s%s%s</tr></table>'
        '<p style="margin:20px 0 0 0; font-family:%s; font-size:14px; line-height:20px; font-weight:700; color:%s; text-align:center;">%s</p>'
        '</td></tr>'
        '<tr><td align="center" bgcolor="%s" style="padding:12px 12px; border-radius:0 0 22px 22px; background-color:%s; '
        'box-shadow:inset 0 4px 8px -4px rgba(0,0,0,0.35); font-family:%s; font-size:10px; line-height:14px; font-weight:900; '
        'letter-spacing:3px; color:%s; white-space:nowrap;">%s</td></tr>'
        '</table>'
    ) % (TABELLA.replace(' style="width:100%;"', ' width="100%"'), OMBRA_BANNER, NERO_BF, NERO_BF,
         con_foto(t, "radial-gradient(circle at 50% 55%, rgba(114,250,147,0.22) 0%, rgba(114,250,147,0) 45%), "
                     "linear-gradient(180deg, rgba(0,6,17,0.86) 0%, rgba(0,6,17,0.80) 50%, rgba(0,6,17,0.90) 100%)"),
         pillola, FONT, esc(t["data_bf"]), tessera(ore), due_punti, tessera(minuti),
         FONT, C["C_SU_SCURO"], esc(t["sotto_bf"]),
         v, v, FONT, NERO_BF, pezzo)


BLOCCHI["benefici"] = b_benefici


# --------------------------------------------------------------------------
# Footer, logo, composizione
# --------------------------------------------------------------------------
def footer_html(cfg):
    st = stile(12, "1.6", T["sec"], "text-align:center;")
    tel = ancora(cfg["telefono_link"], esc(cfg["telefono_testo"]), cfg)
    mail = ancora("mailto:" + cfg["email_studio"], esc(cfg["email_studio"]), cfg)
    unsub = '<a href="%s" target="_blank" class="link" style="%s">%s</a>' % (
        attr(cfg["link_disiscrizione"]), stile_link(), FOOTER_DISISCRIZIONE[1])
    p1 = '<strong style="font-weight:800;">%s</strong><br>%s<br>Tel. %s · %s<br>P.IVA %s' % (
        esc(FOOTER_INTESTAZIONE), esc(cfg["sedi"]), tel, mail, esc(cfg["piva"]))
    p2 = "%s<br>%s%s%s" % (esc(FOOTER_AVVISO), esc(FOOTER_DISISCRIZIONE[0]), unsub, esc(FOOTER_DISISCRIZIONE[2]))
    return ('<p class="t-sec" style="%s margin-bottom:12px;">%s</p>\n<p class="t-sec" style="%s">%s</p>'
            % (st, p1, st, p2))


def footer_txt(cfg):
    return "\n".join([
        FOOTER_INTESTAZIONE,
        cfg["sedi"],
        "Tel. %s · %s" % (cfg["telefono_testo"], cfg["email_studio"]),
        "P.IVA %s" % cfg["piva"],
        "",
        FOOTER_AVVISO,
        "%s%s: %s" % (FOOTER_DISISCRIZIONE[0], FOOTER_DISISCRIZIONE[1], cfg["link_disiscrizione"]),
    ])


def logo_dark_html(cfg):
    if not cfg.get("logo_url_dark"):
        return ""
    w = int(cfg["logo_larghezza_px"])
    return (
        '<!--[if !mso]><!--><div class="logo-dark" style="display:none; max-height:0; overflow:hidden; mso-hide:all;">'
        '<img src="%s" width="%d" alt="Studio Mobilitas" style="display:block; margin:0 auto; width:%dpx; max-width:100%%; '
        'height:auto; border:0; outline:none; text-decoration:none; font-family:%s; font-size:18px; '
        'font-weight:700; line-height:1.3; color:%s;"></div><!--<![endif]-->'
    ) % (attr(cfg["logo_url_dark"]), w, w, FONT, C["D_TESTO"])


def componi(cfg, cont, numero):
    usa_tema(cont.get("tema", "chiaro"))
    notte = bool(T.get("editoriale"))
    testata = dict(cfg.get("testata", {}))
    testata.update(cont.get("testata", {}))
    ctx = Ctx(cfg, numero, testata)
    righe_html, parti_txt, attesi, errori = [], [], [], []
    prec = None
    for i, b in enumerate(cont["blocchi"], 1):
        tipo = b.get("tipo")
        if tipo not in BLOCCHI:
            errori.append("Blocco %d: tipo sconosciuto %r (ammessi: %s)" % (i, tipo, ", ".join(BLOCCHI)))
            continue
        render = BLOCCHI_NOTTE.get(tipo, BLOCCHI[tipo]) if notte else BLOCCHI[tipo]
        h, t, att = render(b, ctx)
        chiave = ("evidenza" if b.get("stile") == "evidenza" else
                  "nota_passi" if (tipo == "nota" and b.get("stile") == "passi") else tipo)
        sopra, sotto = SPAZI[chiave]
        gap = 0 if prec is None else max(prec, sopra)
        righe_html.append('<tr><td style="padding:%dpx 0 0 0;">%s</td></tr>' % (gap, h))
        if t:
            parti_txt.append(t)
        attesi.extend(("blocco %d (%s)" % (i, tipo), a) for a in att)
        prec = sotto
    blocchi = ('<table %s>\n' % TABELLA + "\n".join(righe_html) + "\n</table>")

    valori = dict(COLORI)
    valori.update({
        "TITOLO": esc(cont["oggetto"]),
        "PREHEADER": esc(cont["preheader"]),
        "RIEMPIMENTO": "&zwnj;&nbsp;" * 90,
        "FONT": FONT,
        "LOGO_URL": attr(cfg["logo_url"]),
        "LOGO_LARGHEZZA": str(int(cfg["logo_larghezza_px"])),
        "LOGO_DARK": logo_dark_html(cfg),
        "TESTATA": (testata_banner_html(testata) if testata.get("variante") == "banner" else
                    testata_sintesi_html(testata, ctx) if testata.get("variante") == "sintesi" else
                    testata_traguardo_html(testata, ctx) if testata.get("variante") == "traguardo" else
                    testata_centro_html(testata) if T["template"] == "centro.html" else
                    testata_notte_html(testata) if notte else testata_html(testata)),
        "STRISCIA": (striscia_notte_html(testata, C["C_VERDE"]) if T["template"] == "centro.html" else
                     striscia_notte_html(testata) if notte else ""),
        "BLOCCHI": blocchi,
        "FOOTER": footer_html(cfg),
    })
    if T.get("scuro"):
        valori["LOGO_URL"] = attr(cfg.get("logo_url_dark") or cfg["logo_url"])
    # Fascia in alto e pillola: tolte quando c'e' il banner Black Friday (sarebbero ripetizioni)
    banner = testata.get("variante") == "banner"
    if banner or not notte:
        valori["FASCIA_RIGA"], valori["PILLOLA"] = "", ""
    else:
        scura = T["template"] == "centro.html"
        fondo, colore = (C["C_NERO"], "#FFFFFF") if scura else (C["C_VERDE"], C["C_NERO"])
        valori["FASCIA_RIGA"] = (
            '<tr><td align="center" bgcolor="%s" style="padding:11px 12px; background-color:%s; font-family:%s; font-size:10px; '
            'line-height:14px; font-weight:900; letter-spacing:3px; color:%s; white-space:nowrap;">%s</td></tr>'
            % (fondo, fondo, FONT, colore, valori["STRISCIA"]))
        valori["PILLOLA"] = (
            '<span style="display:inline-block; padding:7px 14px; border:1.5px solid %s; border-radius:999px; '
            'background-color:rgba(114,250,147,0.12); font-family:%s; font-size:10px; line-height:12px; font-weight:800; '
            'letter-spacing:2.4px; color:%s; white-space:nowrap;">BLACK FRIDAY 2026</span>' % (C["C_VERDE"], FONT, C["C_NOTTE"]))
    tpl = (BASE / "template" / T["template"]).read_text(encoding="utf-8")
    mancanti = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", tpl)) - set(valori))
    if mancanti:
        raise SystemExit("ERRORE: segnaposto del template senza valore: " + ", ".join(mancanti))
    out_html = re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: valori[m.group(1)], tpl)

    if cont.get("solo_testo"):
        corpo_txt = (cont["solo_testo"].replace("{saluto}", cfg["saluto"])
                     .replace("{link_lp}", ctx.lp).replace("{telefono}", cfg["telefono_testo"]))
    else:
        corpo_txt = "\n\n".join(parti_txt)
    out_txt = corpo_txt.rstrip() + "\n\n---\n\n" + footer_txt(cfg) + "\n"
    return out_html, out_txt, attesi, errori, ctx


# --------------------------------------------------------------------------
# Controlli
# --------------------------------------------------------------------------
class TestoVisibile(HTMLParser):
    SALTA = {"head", "title", "style", "script"}
    BLOCCO = {"p", "div", "td", "tr", "table", "br", "li", "center"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parti, self.salta = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SALTA:
            self.salta += 1
        if tag in self.BLOCCO:
            self.parti.append(" ")

    def handle_endtag(self, tag):
        if tag in self.SALTA and self.salta:
            self.salta -= 1
        if tag in self.BLOCCO:
            self.parti.append(" ")

    def handle_data(self, d):
        if not self.salta:
            self.parti.append(d)


def visibile(frammento):
    p = TestoVisibile()
    p.feed(frammento)
    p.close()
    return normalizza("".join(p.parti))


def controlla(cfg, cont, numero, out_html, out_txt, attesi, errori_comp, ctx):
    rep = []
    ok = lambda m: rep.append(("OK", m))
    avv = lambda m: rep.append(("AVVISO", m))
    err = lambda m: rep.append(("ERRORE", m))
    for e in errori_comp:
        err(e)

    # Peso
    kb = len(out_html.encode("utf-8")) / 1024
    if kb > 100:
        err("Peso HTML %.1f KB: sopra i 100 KB (Gmail taglia sopra i 102 KB)" % kb)
    elif kb > 90:
        avv("Peso HTML %.1f KB: sopra i 90 KB" % kb)
    else:
        ok("Peso HTML %.1f KB" % kb)

    vis_tutto = visibile(out_html)
    vis_blocchi = visibile(out_html.split(MARCA_INIZIO, 1)[-1].split(MARCA_FINE, 1)[0])
    txt_norm = normalizza(out_txt)
    alt_img = " ".join(re.findall(r'<img\b[^>]*\balt="([^"]*)"', out_html))
    pool = "\n".join([cont["oggetto"], cont.get("oggetto_alternativo", ""), cont["preheader"],
                      vis_tutto, out_txt, alt_img])

    # Parole vietate
    trovate = [n for n, rx in PAROLE_VIETATE if re.search(rx, pool, re.IGNORECASE)]
    if trovate:
        err("Parole vietate presenti: " + ", ".join(trovate))
    else:
        ok("Nessuna parola vietata")

    # Emoji
    emo = sorted(set(EMOJI.findall(pool)))
    if emo:
        err("Emoji presenti: " + " ".join("U+%04X" % ord(e) for e in emo))
    else:
        ok("Nessuna emoji")

    # Testi obbligatori (oggetto, preheader, testo visibile dell'HTML o indirizzi dei link)
    hrefs_html = [html.unescape(h) for h in re.findall(r'href="([^"]*)"', out_html)]
    pool_obbl = normalizza(" ".join([cont["oggetto"], cont.get("oggetto_alternativo", ""),
                                     cont["preheader"], vis_tutto] + hrefs_html))
    mancano = [t for t in cont.get("testi_obbligatori", []) if normalizza(t) not in pool_obbl]
    if mancano:
        err("Testi obbligatori mancanti: " + " | ".join(mancano))
    elif cont.get("testi_obbligatori"):
        ok("Testi obbligatori presenti (%d)" % len(cont["testi_obbligatori"]))
    else:
        avv("Nessun testo obbligatorio indicato nel file di contenuto")

    # Testo identico
    diversi = []
    for dove, a in attesi:
        a = normalizza(a)
        if a not in vis_blocchi:
            diversi.append("%s non identico nell'HTML: %r" % (dove, a[:70]))
        if a not in txt_norm:
            diversi.append("%s non identico nel .txt: %r" % (dove, a[:70]))
    if diversi:
        for d in diversi:
            err("Testo: " + d)
    else:
        ok("Testo identico in HTML e .txt (%d testi di blocco)" % len(attesi))
    if "Ciao ," in vis_tutto or "Ciao ," in out_txt:
        err('Trovato "Ciao ," (spazio prima della virgola)')

    # Link alla LP e pulsanti
    lp = cfg["link_lp"]
    hrefs = [html.unescape(h) for h in re.findall(r'href="([^"]*)"', out_html)]
    lp_links = [h for h in hrefs if h.startswith(lp)]
    lp_links += [l for l in re.findall(r"\S+", out_txt) if l.startswith(lp)]
    attese_utm = {"utm_source": cfg["utm_source"], "utm_medium": cfg["utm_medium"],
                  "utm_campaign": cfg["utm_campaign"], "utm_content": "email_%d" % numero}
    sbagliati = []
    for l in lp_links:
        q = l.split("#", 1)[0]
        q = parse_qs(q.split("?", 1)[1]) if "?" in q else {}
        for k, v in attese_utm.items():
            if q.get(k) != [v]:
                sbagliati.append("%s=%s in %s" % (k, q.get(k), l))
    if sbagliati:
        for s in sbagliati:
            err("UTM sbagliata o mancante: " + s)
    elif lp_links:
        ok("Link alla LP con le 4 UTM e utm_content=email_%d (%d link, HTML+txt+VML)" % (numero, len(lp_links)))
    else:
        avv("Nessun link alla LP nell'email")
    n_puls = max(sum(1 for b in cont["blocchi"] if b.get("tipo") == "pulsante"), out_html.count('class="btn-a"'))
    if n_puls > 2:
        err("Pulsanti: %d (massimo 2)" % n_puls)
    else:
        ok("Pulsanti: %d" % n_puls)

    # Immagini
    imgs = re.findall(r"<img\b[^>]*>", out_html)
    senza = [i for i in imgs if not re.search(r'\balt="[^"]+"', i)]
    if senza:
        err("Immagini senza testo alternativo: %d" % len(senza))
    else:
        ok("Immagini con testo alternativo (%d)" % len(imgs))
    if re.search(r"data:image/", out_html, re.IGNORECASE):
        err("Immagini in base64 presenti")
    if re.search(r"<script\b|<form\b", out_html, re.IGNORECASE):
        err("JavaScript o form presenti")

    # Preheader e disiscrizione
    if not cont.get("preheader", "").strip() or esc(cont["preheader"]) not in out_html:
        err("Preheader mancante")
    else:
        ok("Preheader presente")
    unsub = cfg.get("link_disiscrizione", "").strip()
    if not unsub or ('href="%s"' % attr(unsub)) not in out_html or unsub not in out_txt:
        err("Link di disiscrizione mancante")
    else:
        ok("Link di disiscrizione presente (HTML e .txt)")

    # Data e ora rispetto al calendario
    if cont.get("data_invio") != CALENDARIO.get(numero):
        avv("Data di invio %s diversa dal calendario (%s)" % (cont.get("data_invio"), CALENDARIO.get(numero)))
    if cont.get("ora_invio") != ORA_INVIO:
        avv("Ora di invio %s diversa da %s" % (cont.get("ora_invio"), ORA_INVIO))

    # Saluto provvisorio: finché in config.json non c'è il tag del nome della piattaforma
    if not re.search(r"\{\{|\{%|\*\||%[A-Z_]+%", cfg.get("saluto", "")):
        avv("Saluto provvisorio senza nome")

    if "verificare" in cfg.get("piattaforma", "").lower():
        avv("Tag della piattaforma da verificare con un invio di prova (con e senza nome, e link di disiscrizione)")

    # Tag della piattaforma
    piatt =PIATTAFORME.get(re.sub(r"\s+", "", cfg.get("piattaforma", "").lower()))
    if piatt:
        senza_spazi = lambda s: re.sub(r"\s+", "", s)
        if senza_spazi(piatt["disiscrizione"]) not in senza_spazi(unsub):
            avv("link_disiscrizione non contiene il tag della piattaforma (%s)" % piatt["disiscrizione"])
        if senza_spazi(piatt["nome"]) not in senza_spazi(cfg.get("saluto", "")):
            avv("saluto non contiene il tag del nome della piattaforma (%s)" % piatt["nome"])

    # Segnaposto
    segn = sorted(set(SEGNAPOSTO.findall(out_html + "\n" + out_txt + "\n" + json.dumps(cfg, ensure_ascii=False)
                                         + "\n" + json.dumps(cont, ensure_ascii=False))))
    if segn:
        avv("Segnaposto ancora da compilare (%d): l'email NON è pronta per l'invio" % len(segn))
        for s in segn:
            rep.append(("", "  - " + s))
    else:
        ok("Nessun segnaposto da compilare")
    return rep


# --------------------------------------------------------------------------
def data_estesa(iso):
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        return str(iso)
    return "%s %d %s %d" % (GIORNI[d.weekday()], d.day, MESI[d.month - 1], d.year)


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit("Uso: python3 build.py <numero>")
    numero = int(sys.argv[1])
    cfg = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
    f_cont = BASE / "content" / ("email_%d.json" % numero)
    if not f_cont.exists():
        raise SystemExit("ERRORE: manca %s" % f_cont.relative_to(BASE))
    cont = json.loads(f_cont.read_text(encoding="utf-8"))
    for k in ("numero", "data_invio", "ora_invio", "oggetto", "preheader", "blocchi"):
        if k not in cont:
            raise SystemExit("ERRORE: nel file di contenuto manca il campo %r" % k)
    if int(cont["numero"]) != numero:
        raise SystemExit("ERRORE: il file %s ha numero %s" % (f_cont.name, cont["numero"]))

    out_html, out_txt, attesi, errori, ctx = componi(cfg, cont, numero)
    (BASE / "emails").mkdir(exist_ok=True)
    nome = "BF2026_email_%d_%s" % (numero, cont["data_invio"])
    p_html = BASE / "emails" / (nome + ".html")
    p_txt = BASE / "emails" / (nome + ".txt")
    p_html.write_text(out_html, encoding="utf-8")
    p_txt.write_text(out_txt, encoding="utf-8")

    rep = controlla(cfg, cont, numero, out_html, out_txt, attesi, errori, ctx)
    print("\nREPORT · email %d" % numero)
    for livello, msg in rep:
        print(("[%s] " % livello if livello else "") + msg)
    n_err = sum(1 for l, _ in rep if l == "ERRORE")
    n_avv = sum(1 for l, _ in rep if l == "AVVISO")

    print("\nRIEPILOGO PER LA PIATTAFORMA")
    print("Piattaforma:          %s" % cfg.get("piattaforma"))
    print("Mittente:             %s <%s>" % (cfg.get("mittente_nome"), cfg.get("mittente_email")))
    print("Invio:                %s, ore %s (ora italiana)" % (data_estesa(cont["data_invio"]), cont["ora_invio"]))
    print("Oggetto:              %s" % cont["oggetto"])
    if cont.get("oggetto_alternativo"):
        print("Oggetto alternativo:  %s" % cont["oggetto_alternativo"])
    print("Preheader:            %s" % cont["preheader"])
    print("Link LP:              %s" % ctx.lp)
    print("File HTML:            %s" % p_html.relative_to(BASE))
    print("File TXT:             %s" % p_txt.relative_to(BASE))
    print("\nEsito: %d errori, %d avvisi" % (n_err, n_avv))
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
