"""Countdown ueber dem Grundriss-Katalog (plans/katalog-countdown-v1.md).

Rainer, 2026-11-07: "could you add this list to the grundrisskatalog? towards
the top so i can countdown?"

Liest die Hausliste der Workbench (dieselben Zustaende wie /haus) und schreibt
wordpress/katalog-countdown.php -- einen Code Snippet, der ueber den Filtern
des Katalogs "X von N fertig" und die offenen Schritte zeigt. Nur fuer
eingeloggte Bearbeiter (edit_posts), nie fuer Kunden. Die Zahlen sind ein
Stand zum Zeitpunkt des Erzeugens: neu erzeugen und Snippet ersetzen.

Aufruf:  python katalog-countdown-snippet.py   (Workbench auf :3020 muss laufen)
"""
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HERE, "..", "wordpress", "katalog-countdown.php")
STATE_URL = "http://127.0.0.1:3020/api/floorplan-workbench/state"
GRUNDRISSE = os.path.join(os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
                          or r"E:\born2thrill-local-workbench-data", "katalog-grundrisse")

FERTIG = {"fertig", "fertig_update"}
# Reihenfolge = Reihenfolge der Arbeit. Ein Haus steht genau in einem Schritt.
SCHRITTE = [
    ("Haus zeichnen / vermessen (Annotator)", {"unbegonnen", "keine_vorlage", "vermessung_noetig"}),
    ("Geschosse ausrichten (Annotator)", {"ausrichtung_noetig"}),
    ("Bauen", {"baubereit", "bau_veraltet"}),
    ("Codex-Bilder fehlen", {"warten_auf_codex"}),
    ("Bilder hochladen", {"bilder_hochladen"}),
    ("Bilder freigeben", {"bilder_freigeben", "warten_auf_freigabe", "veroeffentlicht_build_alt"}),
    ("Sonstiges", set()),
]


def zaehlen(haeuser, grundriss_bilder=()):
    """Haeuser -> {gesamt, fertig, offen, schritte:[{titel, plaene}]}.

    Ein Haus, dessen einziges Katalogbild das gezeichnete Grundrissbild ist,
    meldet die Workbench als "Bilder freigeben" -- in Wahrheit fehlen dort
    noch die Codex-Bilder. Es zaehlt deshalb unter "Codex-Bilder fehlen".
    """
    grundriss_bilder = set(grundriss_bilder)
    gruppen = {titel: [] for titel, _ in SCHRITTE}
    fertig = 0
    for h in sorted(haeuser, key=lambda h: h["plan"]):
        state = h.get("state")
        if state in FERTIG:
            fertig += 1
            continue
        if state == "bilder_freigeben" and h["plan"] in grundriss_bilder \
                and int(h.get("catalogue_images") or 0) <= 1:
            gruppen["Codex-Bilder fehlen"].append(h["plan"])
            continue
        titel = next((t for t, menge in SCHRITTE if state in menge), "Sonstiges")
        gruppen[titel].append(h["plan"])
    schritte = [{"titel": t, "plaene": gruppen[t]} for t, _ in SCHRITTE if gruppen[t]]
    return {"gesamt": len(haeuser), "fertig": fertig, "offen": len(haeuser) - fertig,
            "schritte": schritte}


# Baum des Chefs (REGELN 37): Hausart -> Wohnflaeche -> Zimmer. 19 Felder.
# Rainer, 2026-11-09: fehlende Haeuser als Gedankenstuetze im Countdown, je Feld
# Haeuser, die man nach Vorschau duplizieren und etwas groesser/kleiner machen koennte.
MATRIX = os.path.join(os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
                      or r"E:\born2thrill-local-workbench-data", "konfigurator-matrix.csv")
KLASSEN = {"g1": ("bis 130 m²", 0, 130), "g2": ("131–160 m²", 131, 160), "g3": ("über 160 m²", 161, 9999)}
BAUM = [("efh", "g1", 4), ("efh", "g1", 5), ("efh", "g2", 4), ("efh", "g2", 5), ("efh", "g3", 4), ("efh", "g3", 5),
        ("dhh", "g1", 4), ("dhh", "g1", 5), ("dhh", "g2", 4), ("dhh", "g2", 5),
        ("zfh", "g3", 3), ("zfh", "g3", 4),
        ("bungalow", "g1", 3), ("bungalow", "g1", 4), ("bungalow", "g1", 5),
        ("bungalow", "g2", 4), ("bungalow", "g2", 5), ("bungalow", "g3", 4), ("bungalow", "g3", 5)]
ARTNAME = {"efh": "EFH", "dhh": "DH", "zfh": "ZFH", "bungalow": "Bungalow"}
# Wer als Vorlage taugt: erst dieselbe Hausart, dann die naechstverwandte.
SPENDER = {"efh": ["efh", "dhh"], "dhh": ["dhh", "efh"], "zfh": ["zfh", "efh"], "bungalow": ["bungalow"]}
DUENN = 2          # Felder mit weniger fertigen Haeusern bekommen Vorschlaege
MAX_FLAECHE = 0.30  # hoechstens 30 % groesser/kleiner
MAX_KANDIDATEN = 6


def klasse(m2):
    return "g1" if m2 <= 130 else "g2" if m2 <= 160 else "g3"


def matrix_lesen(pfad=MATRIX):
    import csv
    zeilen = []
    try:
        with open(pfad, encoding="utf-8") as f:
            for z in csv.DictReader(f, delimiter=";"):
                try:
                    m2 = int(round(float(z.get("wohnflaeche_m2") or 0)))
                    zi = int(float(z.get("zimmer") or 0))
                except ValueError:
                    continue
                if m2 <= 0:
                    continue
                zeilen.append({"plan": z["plan"], "art": z.get("haustyp") or "", "m2": m2, "zi": zi,
                               "fertig": z.get("fertig") == "ja", "dusche": z.get("gaeste_wc_dusche") == "ja"})
    except OSError:
        pass
    return zeilen


def luecken(zeilen):
    """Je Baumfeld: fertige Haeuser, Haeuser in Arbeit und anpassbare Vorlagen."""
    felder = []
    for art, kl, zi in BAUM:
        name, lo, hi = KLASSEN[kl]
        drin = [z for z in zeilen if z["art"] == art and klasse(z["m2"]) == kl and z["zi"] == zi]
        fertig = [z for z in drin if z["fertig"]]
        feld = {"titel": "{} · {} · {} Zimmer".format(ARTNAME[art], name, zi),
                "fertig": len(fertig), "dusche": sum(z["dusche"] for z in fertig),
                "arbeit": sorted(z["plan"] for z in drin if not z["fertig"]), "kandidaten": []}
        if len(fertig) < DUENN:
            kand = []
            for z in zeilen:
                if z in drin or z["art"] not in SPENDER[art] or abs(z["zi"] - zi) > 1:
                    continue
                ziel = min(max(z["m2"], lo), hi)
                anteil = (ziel - z["m2"]) / z["m2"]
                if abs(anteil) > MAX_FLAECHE:
                    continue
                art_wechsel = z["art"] != art
                punkte = abs(anteil) * 100 + 15 * abs(z["zi"] - zi) + (0 if z["fertig"] else 8) + (6 if art_wechsel else 0)
                teile = []
                if ziel != z["m2"]:
                    teile.append("{:+d} m² ({:+.0f} %)".format(ziel - z["m2"], anteil * 100).replace("-", "−"))
                if z["zi"] != zi:
                    teile.append("{:+d} Zimmer".format(zi - z["zi"]).replace("-", "−"))
                if art_wechsel:
                    teile.append("{} → {}".format(ARTNAME.get(z["art"], z["art"]), ARTNAME[art]))
                if not z["fertig"]:
                    teile.append("noch nicht fertig")
                # aufgaben-v1 (Rainer, 2026-11-12): sagen, WAS zu tun ist.
                tun = "hier eine {}-m²-Variante erstellen".format(int(ziel)) if ziel != z["m2"]                     else "hier eine Kopie erstellen ({} m²)".format(int(ziel))
                dann = []
                if zi > z["zi"]:
                    dann.append("{} Zimmer mehr zeichnen".format(zi - z["zi"]))
                if zi < z["zi"]:
                    dann.append("{} Zimmer weniger zeichnen".format(z["zi"] - zi))
                if art_wechsel:
                    dann.append("Hausart auf {} stellen".format(ARTNAME[art]))
                kand.append((punkte, {"plan": z["plan"], "ziel": int(ziel), "tun": tun,
                                      "dann": ("dann " + ", ".join(dann)) if dann else "",
                                      "info": "{} m², {} Zi: {}".format(z["m2"], z["zi"], ", ".join(teile))}))
            feld["kandidaten"] = [k for _, k in sorted(kand, key=lambda t: (t[0], t[1]["plan"]))[:MAX_KANDIDATEN]]
        # Gaeste-WC als Duschbad (REGELN 37): je Feld beide Fassungen.
        feld["duba"] = []
        if fertig:
            mit = [z for z in fertig if z["dusche"]]
            ohne = [z for z in fertig if not z["dusche"]]
            if not mit:
                feld["duba"] = [{"plan": z["plan"], "ziel": z["m2"],
                                 "tun": "hier Kopie mit Duschbad erstellen",
                                 "dann": "dann Gäste-WC zum Duschbad umbauen"} for z in ohne[:2]]
            elif not ohne:
                feld["duba"] = [{"plan": z["plan"], "ziel": z["m2"],
                                 "tun": "hier Kopie ohne Duschbad erstellen",
                                 "dann": "dann Duschbad zum Gäste-WC zurückbauen"} for z in mit[:2]]
        # ergebnisse-38-v1 (Rainer, 2026-11-12: "we want to have at least one per
        # questionair summery"): je Feld zwei Fragebogen-Ergebnisse, ohne/mit Dusche.
        feld["fehlt"] = [n for n, hat in (("ohne Dusche", feld["fertig"] - feld["dusche"]),
                                          ("mit Dusche", feld["dusche"])) if not hat]
        felder.append(feld)
    return {"leer": sum(1 for f in felder if f["fertig"] == 0), "gesamt": len(felder), "felder": felder,
            "ergebnisse": 2 * len(felder), "ergebnisse_offen": sum(len(f["fehlt"]) for f in felder)}


CSS = """.gk-cd{background:#1d2023;color:#e8e8e8;border:1px solid #3a3f44;padding:14px 18px;margin:0 0 14px;font:14px/1.45 system-ui,sans-serif}
.gk-cd-kopf{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 16px}
.gk-cd-zahl{font-size:22px;font-weight:700;color:#fff}
.gk-cd-rest{font-size:16px;color:#ffd166;font-weight:600}
.gk-cd-stand{margin-left:auto;font-size:12px;color:#9aa0a6}
.gk-cd-balken{height:8px;background:#33383d;margin:10px 0 8px;border-radius:4px;overflow:hidden}
.gk-cd-balken i{display:block;height:100%;background:#4caf50}
.gk-cd details{border-top:1px solid #33383d;padding:6px 0}
.gk-cd summary{cursor:pointer;display:flex;gap:10px}
.gk-cd summary b{min-width:3em;text-align:right;color:#ffd166}
.gk-cd-namen{display:flex;flex-wrap:wrap;gap:4px 6px;margin:6px 0 2px 3.6em}
.gk-cd-namen a{color:#9fd3ff;text-decoration:none;font-size:12px;border:1px solid #3a4a58;padding:1px 6px;border-radius:3px;cursor:pointer}
.gk-cd-namen a:hover{background:#2a3a48}
.gk-cd-baum{margin:6px 0 2px 3.6em;display:grid;gap:8px}
.gk-cd-feld b{color:#fff}.gk-cd-feld .leer{color:#ff8a80}.gk-cd-feld .duenn{color:#ffd166}
.gk-cd-feld small{color:#9aa0a6;margin-left:6px}
.gk-cd-feld ul{margin:3px 0 0;padding-left:18px;font-size:12px;color:#c8ccd0}
.gk-cd-feld li a{color:#9fd3ff;text-decoration:none}"""

JS = """(function () {
	var C = __DATEN__;
	function start() {
		var wrap = document.querySelector('.gk-wrap');
		if (!wrap || wrap.querySelector('.gk-cd')) return;
		var box = document.createElement('div');
		box.className = 'gk-cd';
		var anteil = C.gesamt ? Math.round(100 * C.fertig / C.gesamt) : 0;
		var html = '<div class="gk-cd-kopf"><span class="gk-cd-zahl">' + C.fertig + ' von ' + C.gesamt +
			' fertig</span><span class="gk-cd-rest">noch ' + C.offen + '</span>' +
			'<span class="gk-cd-stand">Stand ' + C.stand + ' · nur für Team sichtbar · Namen öffnen Annotator bzw. /haus</span></div>' +
			'<div class="gk-cd-balken"><i style="width:' + anteil + '%"></i></div>';
		C.schritte.forEach(function (s) {
			html += '<details><summary><b>' + s.plaene.length + '</b><span>' + s.titel + '</span></summary>' +
				'<div class="gk-cd-namen">' + s.plaene.map(function (p) {
					// Rainer, 2026-11-08: anklicken = Haus bearbeiten (neuer Tab, nur auf
					// Rainers Rechner). Zeichnen/Ausrichten im Annotator (8765), alles
					// danach (Einrichten, Bauen, Codex-Bilder) auf /haus der Workbench (3020).
					var annot = s.titel.indexOf('(Annotator)') >= 0;
					var ziel = annot ? 'http://localhost:8765/annotate.html?project=' : 'http://localhost:3020/haus?plan=';
					return '<a data-plan="' + p + '" target="_blank" rel="noopener" title="' + (annot ? 'Im Annotator öffnen' : 'Auf /haus öffnen') +
						'" href="' + ziel + encodeURIComponent(p) + '">' + p + '</a>';
				}).join('') + '</div></details>';
		});
		var B = C.baum;
		if (B && B.felder) {
			// Rainer, 2026-11-09: auf /haus (3020), dort auch Moebel, Bauen, Bilder.
			var annot = function (p) { return '<a target="_blank" rel="noopener" title="Auf /haus öffnen" href="http://localhost:3020/haus?plan=' + encodeURIComponent(p) + '">' + p + '</a>'; };
			// ergebnisse-38-v1: gezaehlt wird je Fragebogen-Ergebnis (Feld x Dusche ja/nein).
			var duenn = B.felder.filter(function (f) { return (f.fehlt || []).length; });
			html += '<details><summary><b>' + B.ergebnisse_offen + '</b><span>von ' + B.ergebnisse + ' Fragebogen-Ergebnissen ohne fertiges Haus – je Ergebnis mindestens eins fertig machen</span></summary><div class="gk-cd-baum">';
			duenn.forEach(function (f) {
				var fertigOhne = f.fertig - f.dusche;
				html += '<div class="gk-cd-feld"><b>' + f.titel + '</b> <span class="' + (f.fertig ? 'duenn' : 'leer') + '">fehlt: ' + f.fehlt.join(' und ') + '</span>' +
					'<small>fertig: ' + fertigOhne + ' ohne Dusche, ' + f.dusche + ' mit Dusche</small><ul>';
				if (f.arbeit.length) html += '<li>fertig machen: ' + f.arbeit.map(annot).join(', ') + '</li>';
				var kopieLink = function (k) { return '<a target="_blank" rel="noopener" title="Kopie anlegen (Original bleibt). Erst mit „Anlegen + Möbel übertragen“ entsteht die Kopie – danach in der KOPIE weiterarbeiten." href="http://localhost:3020/haus?plan=' + encodeURIComponent(k.plan) + '&kopie=' + k.ziel + '"><b>' + (k.tun || ('Kopie ' + k.ziel + ' m² anlegen')) + '</b></a>' + (k.dann ? ', ' + k.dann : ''); };
				(f.duba || []).forEach(function (k) { html += '<li>' + kopieLink(k) + ' – Vorlage ' + annot(k.plan) + ', ' + k.ziel + ' m²</li>'; });
				f.kandidaten.forEach(function (k) { html += '<li>' + kopieLink(k) + ' – Vorlage ' + annot(k.plan) + ': ' + k.info + '</li>'; });
				if (!f.arbeit.length && !f.kandidaten.length && !(f.duba || []).length) html += '<li>keine passende Vorlage (±30 % Fläche, ±1 Zimmer) – neu zeichnen</li>';
				html += '</ul></div>';
			});
			html += '</div></details>';
		}
		box.innerHTML = html;
		wrap.insertBefore(box, wrap.firstChild);
	}
	if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
	else start();
	setTimeout(start, 1500);
})();"""


def php(daten, stand):
    daten = dict(daten, stand=stand)
    js = JS.replace("__DATEN__", json.dumps(daten, ensure_ascii=False, separators=(",", ":")))
    return f"""<?php
/**
 * Katalog-Countdown (plans/katalog-countdown-v1.md). Erzeugt von
 * born2thrill-local-workbench/scripts/katalog-countdown-snippet.py -- nicht von
 * Hand aendern, neu erzeugen. Stand {stand}: {daten['fertig']} von {daten['gesamt']} fertig.
 * Nur fuer eingeloggte Bearbeiter, nur auf Seiten mit [grundriss_katalog].
 */
add_action( 'wp_footer', function () {{
	// Team: auch wer mit dem Website-Zugang (Snippet 13) drin ist, sieht den Countdown.
	if ( is_admin() || ! ( current_user_can( 'edit_posts' ) || ( function_exists( 'b2t_zugang_ok' ) && b2t_zugang_ok() ) ) ) {{
		return;
	}}
	$post = get_post();
	if ( ! $post || ! has_shortcode( $post->post_content, 'grundriss_katalog' ) ) {{
		return;
	}}
	?>
<style id="gk-countdown-css">
{CSS}
</style>
<script id="gk-countdown-js">
{js}
</script>
	<?php
}} );
"""


def main():
    with urllib.request.urlopen(STATE_URL, timeout=120) as antwort:
        haeuser = json.load(antwort)["houses"]
    try:
        grundriss = {n[:-len("-grundriss.png")] for n in os.listdir(GRUNDRISSE)
                     if n.endswith("-grundriss.png")}
    except OSError:
        grundriss = set()
    daten = zaehlen(haeuser, grundriss)
    daten["baum"] = luecken(matrix_lesen())
    text = php(daten, time.strftime("%Y-%m-%d %H:%M"))
    with open(ZIEL, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(os.path.abspath(ZIEL), "--", daten["fertig"], "von", daten["gesamt"], "fertig")
    for s in daten["schritte"]:
        print("  {:4d}  {}".format(len(s["plaene"]), s["titel"]))
    print("Baum: {} von {} Feldern leer".format(daten["baum"]["leer"], daten["baum"]["gesamt"]))
    for f in daten["baum"]["felder"]:
        if f["fertig"] < DUENN:
            print("  {:2d}  {}  arbeit={} vorlagen={}".format(f["fertig"], f["titel"], f["arbeit"],
                                                             [k["plan"] for k in f["kandidaten"]]))


if __name__ == "__main__":
    main()
