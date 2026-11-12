"""Preistabelle Hausart x Zimmer x Budget auf dem Grundriss-Katalog
(plans/katalog-preistabelle-v1.md).

Rainer, 2026-11-07: "that one i need" ... "on the grundrisskatalog site".
Dieselbe Rechnung wie die Chefseite (preislogik-konfigurator.html):
Marktpreis = m2 x 0,8 x Satz (Bungalow 2700, 1,5-Geschosser 2500,
2-Geschosser 2650) x Faktor; "heute" = Matrixpreis (3.000 EUR/m2).
Nur fuer eingeloggte Bearbeiter. Stand = Zeitpunkt des Erzeugens.

Aufruf:  python katalog-preistabelle-snippet.py
"""
import csv
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR") or r"E:\born2thrill-local-workbench-data"
QUELLE = os.path.join(DATA, "konfigurator-matrix.csv")
ZIEL = os.path.join(HERE, "..", "wordpress", "katalog-preistabelle.php")
PROJECTS = os.path.join(HERE, "..", "..", "floorplan-simplifier", "projects")
HAUSART = {"bungalow": "Bungalow", "efh": "Einfamilienhaus", "dhh": "Doppelhaus",
           "zfh": "Zweifamilienhaus", "mfh": "Mehrfamilienhaus"}


def geschosse(plan):
    try:
        with open(os.path.join(PROJECTS, plan, "annotations.json"), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return set()
    return {a.get("floor_level") for a in (d.get("annotations") or []) if a.get("floor_level")}


def satztyp(z):
    """B Bungalow, A 1,5-Geschosser, Z 2-Geschosser (wie die Chefseite)."""
    p = z["plan"]
    if z["haustyp"] == "bungalow":
        return "B"
    g = geschosse(p)
    if "onehalfstorey" in p or "1_5" in p or ("attic" in g and "upperfloor" not in g):
        return "A"
    return "Z"


def daten(zeilen):
    aus = []
    for z in zeilen:
        if not z.get("wohnflaeche_m2") or not z.get("haustyp"):
            continue
        aus.append([HAUSART.get(z["haustyp"], z["haustyp"]), satztyp(z), float(z["zimmer"] or 0),
                    float(z["wohnflaeche_m2"]), int(float(z.get("preis_eur") or 0)),
                    int(float(z.get("volumen_m3") or 0))])
    return aus


CSS = """.gk-pt{background:#1d2023;color:#e8e8e8;border:1px solid #3a3f44;margin:0 0 14px;font:14px/1.45 system-ui,sans-serif}
.gk-pt > summary{cursor:pointer;padding:10px 18px;font-weight:600}
.gk-pt-innen{padding:0 18px 14px}
.gk-pt-zeile{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;margin:6px 0}
.gk-pt-zeile input[type=range]{width:220px}
.gk-pt-wert{font-weight:700;min-width:3.2em}
.gk-pt button{border:1px solid #3a3f44;background:#25292d;color:#e8e8e8;border-radius:5px;padding:3px 10px;cursor:pointer;font:inherit}
.gk-pt button[aria-pressed=true]{border-color:#7fc8a9;color:#7fc8a9;font-weight:700}
.gk-pt-erkl{color:#9aa0a6;font-size:13px;margin:4px 0 10px}
.gk-pt table{border-collapse:separate;border-spacing:4px;width:100%;max-width:760px}
.gk-pt th{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#9aa0a6;text-align:right;font-weight:600;padding:4px 8px}
.gk-pt th:nth-child(-n+2),.gk-pt td:nth-child(-n+2){text-align:left}
.gk-pt td{padding:6px 10px}
.gk-pt td.z{text-align:right;font-weight:700;border-radius:4px;background:rgba(127,200,169,var(--a))}
.gk-pt td.z.leer{background:#4a2421;color:#f0b8b0}
.gk-pt-fuss{color:#9aa0a6;font-size:12px;margin-top:8px}
.gk-pt-block{border-left:3px solid #3a3f44;padding:4px 0 4px 12px;margin:8px 0}
.gk-pt-block.aktiv{border-left-color:#7fc8a9}
.gk-pt-block.aktiv > .gk-pt-zeile > b:first-child{color:#7fc8a9}
.gk-pt-grid{display:grid;grid-template-columns:minmax(0,860px) minmax(300px,1fr);gap:36px;align-items:start}@media (max-width:1150px){.gk-pt-grid{grid-template-columns:minmax(0,1fr)}}.gk-pt-markt{position:sticky;top:16px;border:1px solid #3a3f44;border-radius:8px;padding:12px 16px;background:#1d2023}.gk-pt-markt h4{margin:0 0 4px;font-size:16px;color:#7fc8a9}.gk-pt-markt table{max-width:none}.gk-pt-markt td{padding:6px 8px;border-bottom:1px solid #2c3034;vertical-align:top}.gk-pt-markt th{text-align:left!important}.gk-pt-markt small{color:#9aa0a6}.gk-pt-markt ul{margin:10px 0;padding-left:18px;font-size:13px;color:#c8ccd0}.gk-pt-markt li{margin:4px 0}
.gk-pt label{cursor:pointer}.gk-pt-titel{margin:16px 0 2px;font-size:15px;color:#e8e8e8}.gk-pt-qm span{background:#25292d;border-radius:5px;padding:3px 10px}.gk-pt-qm b{color:#7fc8a9}"""

JS = """(function () {
	// D = [hausart, satztyp, zimmer, m2, preis_heute, volumen_m3]
	var D = __DATEN__;
	var STAND = '__STAND__';
	var SATZ = { B: 2700, A: 2500, Z: 2650 };
	var FELDER = [['Einfamilienhaus', [4, 5]], ['Bungalow', [3, 4, 5]], ['Doppelhaus', [4, 5]], ['Zweifamilienhaus', [3, 4, 5]]];
	// Rainer, 2026-11-08: beide Regler behalten, per Haekchen m2, m3 oder beide.
	// Bei beiden stehen zwei Tabellen untereinander (Team entscheidet mit).
	// Marktpreis je m3 unseres Volumens: 2-Geschosser 0,8 x 2650 / 2,55 m3 je m2 = rund 830 EUR.
	var M3_MARKT = 830;
	var heute = false;
	function komma(f) { return f.toFixed(2).replace('.', ','); }
	function qm(e) { return (Math.round(e / 10) * 10).toLocaleString('de-DE') + ' €'; }
	function spalte(p) { return p < 450000 ? 0 : p < 600000 ? 1 : 2; }
	function start() {
		var wrap = document.querySelector('.gk-wrap');
		if (!wrap || wrap.querySelector('.gk-pt')) return;
		var box = document.createElement('details');
		box.className = 'gk-pt';
		box.innerHTML = '<summary>Preislogik: Häuser je Hausart, Zimmer und Budget</summary><div class="gk-pt-innen"><div class="gk-pt-grid"><div class="gk-pt-links">' +
			'<div class="gk-pt-zeile"><b>Rechnen nach:</b>' +
			'<label><input type="checkbox" data-an="qm" checked> m² Wohnfläche</label>' +
			'<label><input type="checkbox" data-an="m3" checked> m³ umbauter Raum</label></div>' +
			'<div class="gk-pt-block aktiv" data-block="qm"><div class="gk-pt-zeile"><b>Nach Fläche: Faktor über Markt</b>' +
			'<input data-regler="qm" type="range" min="1" max="1.6" step="0.05" value="1.3"><span class="gk-pt-wert" data-wert="qm"></span></div>' +
			'<div class="gk-pt-zeile gk-pt-qm" data-qm></div>' +
			'<div class="gk-pt-zeile"><button data-f="1">1,0 Markt</button><button data-f="1.2">1,2</button>' +
			'<button data-f="1.3">1,3</button><button data-f="1.4">1,4</button>' +
			'<button data-heute>heute zum Vergleich</button></div></div>' +
			'<div class="gk-pt-block aktiv" data-block="m3"><div class="gk-pt-zeile"><b>Nach Volumen: € je m³ umbauter Raum</b>' +
			'<input data-regler="m3" type="range" min="600" max="1400" step="10" value="1080"><span class="gk-pt-wert" data-wert="m3"></span></div>' +
			'<div class="gk-pt-zeile"><button data-e="830">830 ≈ Markt</button><button data-e="1000">1.000</button>' +
			'<button data-e="1080">1.080</button><button data-e="1160">1.160</button></div></div>' +
			'<div data-tabellen></div>' +
			'<div class="gk-pt-fuss">Zahl = Häuser, die der Kunde bei dieser Kombination sieht. Rot = keine Häuser. ' +
			'Wohnfläche = gezeichnete Fläche × 0,8. Umbauter Raum = Außenumriss je Geschoss × 2,62 m; ' +
			'Dach- und 1,5-Geschoss mit der nutzbaren Höhe unter der Schräge (Kniestock 1,0 m, 40°), das Dach selbst zählt nicht. ' +
			'Stand ' + STAND + ' · nur für Team und Bearbeiter sichtbar (Website-Zugang)</div></div>' +
			'<aside class="gk-pt-markt"><h4>Womit wir rechnen</h4>' +
			'<p class="gk-pt-erkl">Unser Marktsatz je m² Wohnfläche stammt aus Hausanbieter-Portalen, <b>überwiegend Fertighaus-Angebote</b> ' +
			'(fertighaus.de, musterhaus.net, fertighausexperte.com, bauen.de, baukostenplan.de). Unabhängige Zahlen je Haustyp gab es nicht frei. ' +
			'Der Faktor soll den Abstand zu unserem Niveau abdecken (Massivbau, Region, Ausstattung).</p>' +
			'<table><thead><tr><th>Haustyp</th><th>unser Marktsatz €/m²<br><small>Faktor 1,0</small></th><th>Vergleich Chrome-KI €/m²</th><th>Vergleich Chrome-KI €/m³</th></tr></thead><tbody>' +
			'<tr><td>Bungalow</td><td><b>2.700</b></td><td>2.400–2.900</td><td>680–800</td></tr>' +
			'<tr><td>1,5-Geschosser<br><small>EG + Dachgeschoss</small></td><td><b>2.500</b></td><td>2.200–2.700</td><td>580–700</td></tr>' +
			'<tr><td>2-Geschosser<br><small>Stadtvilla, DHH, ZFH</small></td><td><b>2.650</b></td><td>2.500–3.000</td><td>620–730</td></tr>' +
			'</tbody></table>' +
			'<p class="gk-pt-erkl">Chrome-KI-Werte nur zum Vergleich, ohne Quelle und ohne Angabe Fertig- oder Massivhaus. ' +
			'Je m² liegen unsere Sätze mitten in diesen Spannen. Je m³: unser Volumen-Marktwert 830 € (Faktor 1,0, alle Haustypen gleich) liegt am oberen Rand, 1.080 € deutlich darüber.</p>' +
			'<p class="gk-pt-erkl">Wohnfläche = gezeichnete Fläche × 0,8 (geschätzt, noch an Originalplänen nachzumessen). Grundstück nicht enthalten.</p></aside></div></div>';
		var rq = box.querySelector('[data-regler="qm"]'), rv = box.querySelector('[data-regler="m3"]');
		var anQ = box.querySelector('[data-an="qm"]'), anV = box.querySelector('[data-an="m3"]');
		var tabellen = box.querySelector('[data-tabellen]');
		function tabelle(titel, erkl, preis, nurMitVolumen) {
			var html = '';
			FELDER.forEach(function (feld) {
				feld[1].forEach(function (z) {
					var n = [0, 0, 0];
					D.forEach(function (h) {
						if (nurMitVolumen && !h[5]) return;
						if (h[0] === feld[0] && Math.min(Math.floor(h[2]), 5) === z) n[spalte(preis(h))]++;
					});
					html += '<tr><td>' + feld[0] + '</td><td>' + z + '</td>' + n.map(function (c) {
						return '<td class="z' + (c === 0 ? ' leer' : '') + '" style="--a:' + (Math.min(c / 50, 1) * 0.45) + '">' + c + '</td>';
					}).join('') + '</tr>';
				});
			});
			return '<h4 class="gk-pt-titel">' + titel + '</h4><div class="gk-pt-erkl">' + erkl + '</div>' +
				'<table><thead><tr><th>Hausart</th><th>Zimmer</th><th>bis 450.000 €</th>' +
				'<th>450.000–600.000 €</th><th>über 600.000 €</th></tr></thead><tbody>' + html + '</tbody></table>';
		}
		function zeichne() {
			var f = Number(rq.value), e = Number(rv.value);
			box.querySelector('[data-wert="qm"]').textContent = komma(f) + (f === 1 ? ' (Markt)' : ' (+' + Math.round((f - 1) * 100) + ' %)');
			box.querySelector('[data-qm]').innerHTML = '<span>Bungalow <b>' + qm(SATZ.B * f) + '/m²</b></span>' +
				'<span>1,5-Geschosser <b>' + qm(SATZ.A * f) + '/m²</b></span>' +
				'<span>2-Geschosser / Doppelhaus / ZFH <b>' + qm(SATZ.Z * f) + '/m²</b></span>';
			box.querySelector('[data-wert="m3"]').textContent = e.toLocaleString('de-DE') + ' €/m³ (≈ Faktor ' + komma(e / M3_MARKT) + ')';
			box.querySelector('[data-block="qm"]').hidden = !anQ.checked;
			box.querySelector('[data-block="m3"]').hidden = !anV.checked;
			box.querySelectorAll('button').forEach(function (k) {
				var an = k.hasAttribute('data-heute') ? heute
					: k.dataset.f ? (!heute && Number(k.dataset.f) === f) : Number(k.dataset.e) === e;
				k.setAttribute('aria-pressed', String(an));
			});
			var html = '';
			if (anQ.checked) {
				html += heute
					? tabelle('Nach Fläche – heute zum Vergleich', 'Heute: 3.000 € je m² gezeichneter Fläche = 3.750 € je m² Wohnfläche, für jeden Haustyp gleich.',
						function (h) { return h[4]; }, false)
					: tabelle('Nach Fläche – Faktor ' + komma(f), 'Preis = Wohnfläche × Marktpreis je Haustyp × Faktor.',
						function (h) { return h[3] * 0.8 * SATZ[h[1]] * f; }, false);
			}
			if (anV.checked) {
				html += tabelle('Nach Volumen – ' + e.toLocaleString('de-DE') + ' € je m³',
					'Für jeden Haustyp gleich. Dachschrägen machen ein Haus günstiger, ein Luftraum zählt voll mit. Häuser ohne Außenumriss fehlen hier.',
					function (h) { return h[5] * e; }, true);
			}
			tabellen.innerHTML = html || '<p class="gk-pt-erkl">Mindestens ein Häkchen setzen.</p>';
		}
		rq.addEventListener('input', function () { heute = false; zeichne(); });
		rv.addEventListener('input', zeichne);
		anQ.addEventListener('change', zeichne);
		anV.addEventListener('change', zeichne);
		box.addEventListener('click', function (ev) {
			var k = ev.target.closest('button');
			if (!k) return;
			if (k.hasAttribute('data-heute')) heute = !heute;
			if (k.dataset.f) { rq.value = k.dataset.f; heute = false; }
			if (k.dataset.e) rv.value = k.dataset.e;
			zeichne();
		});
		zeichne();
		var cd = wrap.querySelector('.gk-cd');
		if (cd) cd.parentNode.insertBefore(box, cd.nextSibling); else wrap.insertBefore(box, wrap.firstChild);
	}
	if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
	else start();
	setTimeout(start, 1600);
})();"""


def php(d, stand):
    js = JS.replace("__DATEN__", json.dumps(d, ensure_ascii=False, separators=(",", ":"))).replace("__STAND__", stand)
    return f"""<?php
/**
 * Katalog-Preistabelle (plans/katalog-preistabelle-v1.md). Erzeugt von
 * born2thrill-local-workbench/scripts/katalog-preistabelle-snippet.py -- nicht
 * von Hand aendern, neu erzeugen. Stand {stand}: {len(d)} Haeuser.
 * Fuer Bearbeiter und Team (Website-Zugang), nur auf Seiten mit [grundriss_katalog].
 */
add_action( 'wp_footer', function () {{
	// Team: auch wer mit dem Website-Zugang (Snippet 13) drin ist, sieht die Regler.
	if ( is_admin() || ! ( current_user_can( 'edit_posts' ) || ( function_exists( 'b2t_zugang_ok' ) && b2t_zugang_ok() ) ) ) {{
		return;
	}}
	$post = get_post();
	if ( ! $post || ! has_shortcode( $post->post_content, 'grundriss_katalog' ) ) {{
		return;
	}}
	?>
<style id="gk-preistabelle-css">
{CSS}
</style>
<script id="gk-preistabelle-js">
{js}
</script>
	<?php
}} );
"""


def main():
    with open(QUELLE, encoding="utf-8-sig") as f:
        d = daten(csv.DictReader(f, delimiter=";"))
    text = php(d, time.strftime("%Y-%m-%d %H:%M"))
    with open(ZIEL, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    from collections import Counter
    print(os.path.abspath(ZIEL), len(d), dict(Counter(h[0] for h in d)))


if __name__ == "__main__":
    main()
