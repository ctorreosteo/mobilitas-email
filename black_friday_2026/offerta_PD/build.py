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
  "blocchi": [
    {"tipo": "saluto"},                      usa "saluto" di config.json ("testo" per sovrascriverlo)
    {"tipo": "paragrafo", "testo": "..."},
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
    "C_BIANCO": "#FFFFFF",      # sfondo dell'email
    "C_NOTTE": "#002552",       # testo, link, testo del pulsante
    "C_GRIGIO": "#F4F4F4",      # riquadro, fascia footer, linea sopra il P.S.
    "C_CORALLO": "#FA7272",     # SOLO sfondo del pulsante
    "C_AZZURRO": "#72B1FA",     # linea sotto il logo, bordo sinistro del riquadro
    "C_SECONDARIO": "#4A5F7A",  # testo secondario, prezzo barrato
    # dark mode
    "D_SFONDO": "#002552",
    "D_TESTO": "#F4F4F4",
    "D_SECONDARIO": "#B8C4D4",
    "D_RIQUADRO": "#0B3366",
    "D_BORDO": "#72B1FA",
    "D_FOOTER": "#0B3366",
}
C = COLORI
FONT = "Montserrat, Arial, Helvetica, sans-serif"

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
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿️⌚⌛"
    "⏩-⏺⤴⤵〰〽㊗㊙]"
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
    "saluto": (0, 18), "paragrafo": (0, 18), "chiusura": (0, 18), "firma": (0, 18),
    "nota": (0, 18), "riquadro": (24, 24), "pulsante": (24, 24), "ps": (24, 0),
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


def stile(size=16, lh="1.65", colore=None, extra=""):
    colore = colore or C["C_NOTTE"]
    return ("margin:0; font-family:%s; font-size:%dpx; line-height:%s; color:%s;%s"
            % (FONT, size, lh, colore, (" " + extra) if extra else ""))


STILE_LINK = "color:%s; text-decoration:underline;" % C["C_NOTTE"]


class Ctx:
    def __init__(self, cfg, numero):
        self.cfg = cfg
        self.numero = numero
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
    st = STILE_LINK + (" white-space:nowrap;" if url.startswith("tel:") else "")
    return '<a href="%s"%s class="link" style="%s">%s</a>' % (attr(url), blank, st, testo_html)


def inline(s, ctx):
    """Testo del blocco -> HTML: escape, grassetto, link, telefono, a capo."""
    def segmento(t):
        t = BOLD_MD.sub(r'<strong style="font-weight:700;">\1</strong>', esc(t))
        tel = esc(ctx.cfg["telefono_testo"])
        if tel and tel in t:
            t = t.replace(tel, ancora(ctx.cfg["telefono_link"], tel, ctx.cfg))
        return t

    out, pos = [], 0
    for m in LINK_MD.finditer(s):
        out.append(segmento(s[pos:m.start()]))
        testo_link = BOLD_MD.sub(r'<strong style="font-weight:700;">\1</strong>', esc(m.group(1)))
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


# --------------------------------------------------------------------------
# Blocchi: ognuno restituisce (html, txt, [testi attesi])
# --------------------------------------------------------------------------
def b_testo(b, ctx, testo=None):
    t = testo if testo is not None else b["testo"]
    h = '<p class="t-main" style="%s">%s</p>' % (stile(), inline(t, ctx))
    return h, inline_txt(t, ctx), [testo_puro(t)]


def b_saluto(b, ctx):
    return b_testo(b, ctx, b.get("testo", ctx.cfg["saluto"]))


def b_firma(b, ctx):
    t = b.get("testo", "Studio Mobilitas")
    h = '<p class="t-main" style="%s">%s</p>' % (stile(extra="font-weight:700;"), inline(t, ctx))
    return h, testo_puro(t), [testo_puro(t)]


def b_riquadro(b, ctx):
    righe = b["righe"]
    parti = []
    for i, r in enumerate(righe):
        mb = "0" if i == len(righe) - 1 else "10px"
        m = PREZZO.match(r) if i == 1 else None
        if i == 0:
            parti.append('<p class="t-main" style="%s">%s</p>' % (
                stile(17, "1.45", extra="font-weight:700; margin-bottom:%s;" % mb), inline(r, ctx)))
        elif m:
            parti.append(
                '<p class="t-main" style="%s">'
                '<span style="font-family:%s; font-size:32px; line-height:1.15; font-weight:900;">%s</span>'
                '<span style="font-size:16px; font-weight:400;">%s</span>'
                '<span class="t-sec" style="font-size:16px; font-weight:400; color:%s; text-decoration:line-through;">%s</span>'
                '<span style="font-size:16px; font-weight:400;">%s</span></p>' % (
                    stile(16, "1.3", extra="margin-bottom:%s;" % mb), FONT,
                    esc(m.group(1)), esc(m.group(2)), C["C_SECONDARIO"], esc(m.group(3)), esc(m.group(4))))
        elif i == 1:
            parti.append('<p class="t-main" style="%s">%s</p>' % (
                stile(16, "1.5", extra="margin-bottom:%s;" % mb), inline(r, ctx)))
        else:
            parti.append('<p class="t-sec" style="%s">%s</p>' % (
                stile(14, "1.55", C["C_SECONDARIO"], "margin-bottom:%s;" % mb), inline(r, ctx)))
    h = (
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" style="width:100%%;">'
        '<tr><td class="bg-box" bgcolor="%s" style="background-color:%s; border-left:4px solid %s; '
        'border-radius:8px; padding:20px 22px;">%s</td></tr></table>'
    ) % (C["C_GRIGIO"], C["C_GRIGIO"], C["C_AZZURRO"], "".join(parti))
    txt = "\n".join(inline_txt(r, ctx) for r in righe)
    return h, txt, [testo_puro(r) for r in righe]


def b_pulsante(b, ctx):
    testo = b["testo"]
    url = ctx.risolvi(b.get("link", "lp"))
    larg_testo = len(testo) * 9.6
    w = int(min(536, larg_testo + 56))
    righe = max(1, math.ceil(larg_testo / (536 - 56)))
    alt = 52 + (righe - 1) * 20
    h = (
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" style="width:100%%;">'
        '<tr><td align="center" style="padding:0;">'
        '<!--[if mso]>'
        '<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" '
        'href="%(url)s" style="height:%(alt)dpx; v-text-anchor:middle; width:%(w)dpx;" arcsize="50%%" '
        'strokecolor="%(cor)s" fillcolor="%(cor)s"><w:anchorlock/>'
        '<center style="color:%(notte)s; font-family:Arial, Helvetica, sans-serif; font-size:16px; font-weight:bold;">%(testo)s</center>'
        '</v:roundrect>'
        '<![endif]-->'
        '<!--[if !mso]><!-->'
        '<table role="presentation" class="btn-table" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;">'
        '<tr><td class="btn-td" align="center" bgcolor="%(cor)s" style="border-radius:30px; background-color:%(cor)s;">'
        '<a class="btn-a" href="%(url)s" target="_blank" style="display:inline-block; padding:16px 28px; '
        'font-family:%(font)s; font-size:16px; font-weight:800; line-height:20px; color:%(notte)s; '
        'text-decoration:none; border-radius:30px; text-align:center;">%(testo)s</a>'
        '</td></tr></table>'
        '<!--<![endif]-->'
        '</td></tr></table>'
    ) % {"url": attr(url), "alt": alt, "w": w, "cor": C["C_CORALLO"], "notte": C["C_NOTTE"],
         "font": FONT, "testo": esc(testo)}
    return h, "%s\n%s" % (testo, url), [testo]


def b_nota(b, ctx):
    t = b["testo"]
    h = '<p class="t-sec" style="%s">%s</p>' % (
        stile(14, "1.6", C["C_SECONDARIO"], "text-align:center;"), inline(t, ctx))
    return h, inline_txt(t, ctx), [testo_puro(t)]


def b_ps(b, ctx):
    t = b["testo"]
    if t.startswith("P.S."):
        corpo = '<strong style="font-weight:700;">P.S.</strong>' + inline(t[4:], ctx)
    else:
        corpo = inline(t, ctx)
    h = (
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" style="width:100%%;">'
        '<tr><td class="ps-line" style="border-top:2px solid %s; padding:18px 0 0 0;">'
        '<p class="t-main" style="%s">%s</p></td></tr></table>'
    ) % (C["C_GRIGIO"], stile(15, "1.6"), corpo)
    return h, inline_txt(t, ctx), [testo_puro(t)]


BLOCCHI = {
    "saluto": b_saluto,
    "paragrafo": b_testo,
    "chiusura": b_testo,
    "riquadro": b_riquadro,
    "pulsante": b_pulsante,
    "nota": b_nota,
    "firma": b_firma,
    "ps": b_ps,
}


# --------------------------------------------------------------------------
# Footer, logo, composizione
# --------------------------------------------------------------------------
def footer_html(cfg):
    st = stile(12, "1.6", C["C_SECONDARIO"], "text-align:center;")
    tel = ancora(cfg["telefono_link"], esc(cfg["telefono_testo"]), cfg)
    mail = ancora("mailto:" + cfg["email_studio"], esc(cfg["email_studio"]), cfg)
    unsub = '<a href="%s" target="_blank" class="link" style="%s">%s</a>' % (
        attr(cfg["link_disiscrizione"]), STILE_LINK, FOOTER_DISISCRIZIONE[1])
    p1 = "%s<br>%s<br>Tel. %s · %s<br>P.IVA %s" % (
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
        '<img src="%s" width="%d" alt="Studio Mobilitas" style="display:block; width:%dpx; max-width:100%%; '
        'height:auto; border:0; outline:none; text-decoration:none; font-family:%s; font-size:18px; '
        'font-weight:700; line-height:1.3; color:%s;"></div><!--<![endif]-->'
    ) % (attr(cfg["logo_url_dark"]), w, w, FONT, C["D_TESTO"])


def componi(cfg, cont, numero):
    ctx = Ctx(cfg, numero)
    righe_html, parti_txt, attesi, errori = [], [], [], []
    prec = None
    for i, b in enumerate(cont["blocchi"], 1):
        tipo = b.get("tipo")
        if tipo not in BLOCCHI:
            errori.append("Blocco %d: tipo sconosciuto %r (ammessi: %s)" % (i, tipo, ", ".join(BLOCCHI)))
            continue
        h, t, att = BLOCCHI[tipo](b, ctx)
        sopra, sotto = SPAZI[tipo]
        gap = 0 if prec is None else max(prec, sopra)
        righe_html.append('<tr><td style="padding:%dpx 0 0 0;">%s</td></tr>' % (gap, h))
        parti_txt.append(t)
        attesi.extend(("blocco %d (%s)" % (i, tipo), a) for a in att)
        prec = sotto
    blocchi = ('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;">\n'
               + "\n".join(righe_html) + "\n</table>")

    valori = dict(COLORI)
    valori.update({
        "TITOLO": esc(cont["oggetto"]),
        "PREHEADER": esc(cont["preheader"]),
        "RIEMPIMENTO": "&zwnj;&nbsp;" * 90,
        "FONT": FONT,
        "LOGO_URL": attr(cfg["logo_url"]),
        "LOGO_LARGHEZZA": str(int(cfg["logo_larghezza_px"])),
        "LOGO_DARK": logo_dark_html(cfg),
        "BLOCCHI": blocchi,
        "FOOTER": footer_html(cfg),
    })
    tpl = (BASE / "template" / "base.html").read_text(encoding="utf-8")
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
    n_puls = sum(1 for b in cont["blocchi"] if b.get("tipo") == "pulsante")
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
