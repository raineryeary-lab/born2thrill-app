"""Baut das WordPress-Zusatz-Snippet "Katalog Fragebogen-Filter".

Rainer, 2026-11-05: "could you also make a checkbox for the dropdowns on top
to replicate the questions?" -- auf born2thrill.de/grundriss-katalog, "da wo
alles andere schon ist". Das Snippet haengt eine Zeile unter die Filter von
Snippet 9 (Grundriss-Katalog): Haekchen "Wie im Fragebogen", Hausart, Zimmer
(EFH/DHH nur 4/5, Frage 7), Gaeste-WC mit Dusche, "nur im Preisfenster".
Snippet 9 bleibt unberuehrt; der Filter blendet Karten nur aus.

Die Werte kommen aus konfigurator-matrix.csv (konfigurator-matrix.py,
REGELN 37) und stehen als Liste im Snippet. Neu laufen lassen, wenn sich die
Matrix aendert, dann das Snippet in Code Snippets ersetzen.

v2, Rainer 2026-11-07: "redo the grundriss catalog so that the filters on the
top just have me filter according to the questionaire + the name". Snippet 10
blendet jetzt die Filterzeile und die Schlagwoerter von Snippet 9 aus und setzt
an ihre Stelle: Name (ID oder Anzeigename), Budget (wie Frage 3, unterste
Antwort "bis 450.000"), Hausart, Zimmer, Gaeste-WC mit Dusche. Kein Haekchen
mehr, die Filter gelten immer. Baustil und Dachform waehlen nur das Bild.

v3, Rainer 2026-11-09: neuer Baum des Chefs (docs/Grundriss Pfad 1.pdf, REGELN 37):
Hausart -> Wohnflaeche (bis 130 / 131-160 / ueber 160 m2) -> Zimmer -> Gaeste-WC
als Duschbad. Budget-Filter faellt weg (Preis bleibt als Anhaltspunkt auf der
Karte); Flaeche und Zimmer bieten je Hausart nur die Aeste des Baums an.

Ausgabe: wordpress/katalog-fragebogen-filter.php
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
if not DATA:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- siehe .env.local.")
ZIEL = os.path.join(HERE, "..", "wordpress", "katalog-fragebogen-filter.php")
PROJECTS = os.path.join(HERE, "..", "..", "floorplan-simplifier", "projects")


def anzeigename(plan):
    try:
        with open(os.path.join(PROJECTS, plan, "anzeigename.json"), encoding="utf-8") as f:
            return str(json.load(f).get("anzeigename") or "")
    except (OSError, ValueError):
        return ""


def werte(pfad):
    daten = {}
    with open(pfad, encoding="utf-8") as f:
        for z in csv.DictReader(f, delimiter=";"):
            try:
                zimmer = min(int(float(z.get("zimmer") or 0)), 5)
            except ValueError:
                continue
            daten[z["plan"]] = [z.get("haustyp") or "", zimmer, int(float(z.get("preis_eur") or 0)),
                                1 if z.get("gaeste_wc_dusche") == "ja" else 0,
                                anzeigename(z["plan"]),
                                int(float(z.get("wohneinheiten") or 1)),
                                int(round(float(z.get("wohnflaeche_m2") or 0)))]
    return daten


def ohne_matrix_nach_wohneinheiten(daten):
    """Haeuser ohne Matrixzeile (kein Massstab, also keine Flaeche und kein
    Preis), deren Zeichnung 2+ Wohneinheiten hat, kommen trotzdem unter
    Hausart Zweifamilienhaus/Mehrfamilienhaus. Zimmer und Preis bleiben 0 --
    sie passen also nur, solange diese Filter leer sind.
    Rainer, 2026-11-07: "WHY ARE MY 2 FAMILIENHAEUSER NOT BEING SHOWN"."""
    daten = dict(daten)
    try:
        plaene = sorted(os.listdir(PROJECTS))
    except OSError:
        return daten
    for plan in plaene:
        if plan in daten:
            continue
        try:
            with open(os.path.join(PROJECTS, plan, "annotations.json"), encoding="utf-8") as f:
                we = int(json.load(f).get("wohneinheiten") or 1)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
        if we >= 2:
            daten[plan] = ["mfh" if we >= 3 else "zfh", 0, 0, 0, anzeigename(plan), we, 0]
    return daten


JS = r"""
(function () {
	// D[id] = [hausart, zimmer, preis, gaeste_wc_dusche, anzeigename, wohneinheiten, wohnflaeche_m2]
	var D = __DATEN__;
	// Baum des Chefs (REGELN 37): Hausart -> Wohnflaeche -> Zimmer. mfh steht nicht im Baum: alles frei.
	var BAUM = {
		efh: { g1: ['4', '5'], g2: ['4', '5'], g3: ['4', '5'] },
		dhh: { g1: ['4', '5'], g2: ['4', '5'] },
		zfh: { g3: ['3', '4'] },
		bungalow: { g1: ['3', '4', '5'], g2: ['4', '5'], g3: ['4', '5'] }
	};
	function klasse(m2) { return !m2 ? '' : m2 <= 130 ? 'g1' : m2 <= 160 ? 'g2' : 'g3'; }
	function start() {
		var form = document.querySelector('.gk-wrap form.gk-search');
		var grid = document.querySelector('.gk-wrap');
		if (!form || form.querySelector('.gk-fb')) return;
		var zeile = document.createElement('div');
		zeile.className = 'gk-row gk-fb';
		zeile.innerHTML =
			'<div class="gk-field"><label>Name</label><input type="search" data-fb="name" placeholder="z. B. bungalow_007 oder BAH"></div>' +
			'<div class="gk-field"><label>Hausart</label><select data-fb="art"><option value="">egal</option>' +
			'<option value="efh">Einfamilienhaus</option><option value="bungalow">Bungalow</option>' +
			'<option value="dhh">Doppelhaus / Doppelhaushälfte</option><option value="zfh">Zweifamilienhaus</option>' +
			'<option value="mfh">Mehrfamilienhaus</option></select></div>' +
			'<div class="gk-field"><label>Wohnfläche</label><select data-fb="fl"><option value="">egal</option>' +
			'<option value="g1">bis 130 m²</option><option value="g2">131 – 160 m²</option>' +
			'<option value="g3">größer 160 m²</option></select></div>' +
			'<div class="gk-field"><label>Zimmer</label><select data-fb="zi"><option value="">egal</option>' +
			'<option value="3">3 Zimmer</option><option value="4">4 Zimmer</option><option value="5">5 und mehr Zimmer</option></select></div>' +
			'<div class="gk-field"><label>Gäste-WC mit Dusche</label><select data-fb="du"><option value="">egal</option>' +
			'<option value="1">Ja</option><option value="0">Nein</option></select></div>' +
			'<button type="button" class="gk-reset" data-fb="reset">Zurücksetzen</button>' +
			'<div class="gk-field gk-fb-zahl" data-fb="zahl"></div>';
		form.insertBefore(zeile, form.firstChild);
		var q = function (n) { return zeile.querySelector('[data-fb="' + n + '"]'); };
		var name = q('name'), fl = q('fl'), art = q('art'), zi = q('zi'), du = q('du'), zahl = q('zahl');
		function passt(id) {
			var w = D[id];
			var such = name.value.trim().toLowerCase();
			if (such && (id + ' ' + (w ? w[4] : '')).toLowerCase().indexOf(such) < 0) return false;
			if (!fl.value && !art.value && !zi.value && !du.value) return true;
			if (!w) return false;
			if (art.value && w[0] !== art.value) return false;
			// Mehrfamilienhaus: nach Wohnungen statt Zimmern (Rainer, 2026-11-07, "By number of flats")
			if (zi.value && String(art.value === 'mfh' ? Math.min(w[5] || 1, 5) : w[1]) !== zi.value) return false;
			if (du.value && String(w[3]) !== du.value) return false;
			if (fl.value && klasse(w[6]) !== fl.value) return false;
			return true;
		}
		var beob = new MutationObserver(anwenden);
		function beobachten() { beob.observe(grid, { childList: true, subtree: true }); }
		function anwenden() {
			// Waehrend wir selbst Karten aendern, nicht auf uns selbst reagieren.
			beob.disconnect();
			var sichtbar = 0;
			grid.querySelectorAll('.gk-card').forEach(function (karte) {
				var h = karte.querySelector('h3');
				var id = h ? h.textContent.trim() : '';
				var ok = passt(id);
				karte.style.display = ok ? '' : 'none';
				// Nur das Grundriss-Bild (katalog-grundriss-bild-v1) ist kein Render:
				var st = karte.querySelector('.gk-state'), cov = karte.querySelector('.gk-view img');
				var einBild = [].some.call(karte.querySelectorAll('.gk-pill'), function (x) { return x.textContent.trim() === '1 Bilder'; });
				if (st && cov && einBild && cov.src.indexOf('/' + id + '-grundriss') >= 0
						&& karte.getAttribute('data-done') === 'bild') {
					st.textContent = 'offen';
					karte.setAttribute('data-done', 'offen');
				}
				var alt = karte.querySelector('.gk-fb-info');
				if (alt) alt.remove();
				if (ok && D[id]) {
					var info = document.createElement('p');
					info.className = 'gk-fb-info';
					info.textContent = (D[id][4] ? D[id][4] + ' · ' : '') +
						(D[id][5] >= 3 ? D[id][5] + ' Wohnungen · ' : D[id][5] === 2 ? '2 Wohnungen · ' : '') +
						(D[id][2] ? (D[id][6] ? D[id][6] + ' m² · ' : '') + D[id][1] + ' Zimmer · ca. ' + Math.round(D[id][2] / 1000) + ' Tsd. €' : 'Maße folgen') +
						(D[id][3] ? ' · Gäste-WC mit Dusche' : '');
					var kopf = karte.querySelector('.gk-meta') || h;
					kopf.parentNode.insertBefore(info, kopf.nextSibling);
				}
				if (ok) sichtbar++;
			});
			zahl.textContent = sichtbar + ' passende Häuser';
			beobachten();
		}
		function schalten() {
			var wohnungen = art.value === 'mfh';
			zi.parentNode.querySelector('label').textContent = wohnungen ? 'Wohnungen' : 'Zimmer';
			var namen = wohnungen ? ['3 Wohnungen', '4 Wohnungen', '5 und mehr Wohnungen']
				: ['3 Zimmer', '4 Zimmer', '5 und mehr Zimmer'];
			Array.prototype.forEach.call(zi.options, function (o, i) { if (i > 0) o.textContent = namen[i - 1]; });
			// Flaeche: nur Aeste der Hausart; Zimmer: nur Aeste von Hausart + Flaeche.
			var ast = BAUM[art.value];
			Array.prototype.forEach.call(fl.options, function (o) { o.disabled = !!o.value && !!ast && !ast[o.value]; });
			if (fl.value && ast && !ast[fl.value]) fl.value = '';
			var erlaubt = ['3', '4', '5'];
			if (ast) {
				erlaubt = [];
				Object.keys(ast).forEach(function (g) {
					if (!fl.value || g === fl.value) ast[g].forEach(function (z) { if (erlaubt.indexOf(z) < 0) erlaubt.push(z); });
				});
			}
			Array.prototype.forEach.call(zi.options, function (o) {
				o.disabled = !!o.value && erlaubt.indexOf(o.value) < 0;
			});
			if (zi.value && erlaubt.indexOf(zi.value) < 0) zi.value = '';
			anwenden();
		}
		[fl, art, zi, du].forEach(function (el) { el.addEventListener('change', schalten); });
		name.addEventListener('input', anwenden);
		q('reset').addEventListener('click', function () {
			name.value = ''; fl.value = ''; art.value = ''; zi.value = ''; du.value = '';
			schalten();
		});
		// Snippet 9 zeichnet die Karten bei jedem Laden neu.
		schalten();
	}
	if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
	else start();
	setTimeout(start, 1500);
})();
"""

CSS = """.gk-search > .gk-row:not(.gk-fb), .gk-search > .gk-tags{display:none !important}
.gk-fb{align-items:end}
.gk-fb input[type=search]{min-width:15rem}
.gk-fb-zahl{align-self:center;opacity:.8}
.gk-fb-info{margin:.3rem 0 0;font-size:.85rem;font-weight:600}"""


def main():
    daten = ohne_matrix_nach_wohneinheiten(werte(os.path.join(DATA, "konfigurator-matrix.csv")))
    js = JS.replace("__DATEN__", json.dumps(daten, separators=(",", ":"), sort_keys=True))
    php = f"""<?php
/**
 * Katalog Fragebogen-Filter (Zusatz zu Snippet 9 "Grundriss-Katalog").
 * Erzeugt von born2thrill-local-workbench/scripts/katalog-fragebogen-snippet.py
 * -- nicht von Hand aendern, neu erzeugen. {len(daten)} Haeuser.
 * Nur Frontend, nur auf Seiten mit [grundriss_katalog]. Liest nichts aus der
 * Datenbank und schreibt nichts.
 */
add_action( 'wp_footer', function () {{
	if ( is_admin() ) {{
		return;
	}}
	$post = get_post();
	if ( ! $post || ! has_shortcode( $post->post_content, 'grundriss_katalog' ) ) {{
		return;
	}}
	?>
<style id="gk-fragebogen-css">
{CSS}
</style>
<script id="gk-fragebogen-js">
{js.strip()}
</script>
	<?php
}}, 100 );
"""
    with open(ZIEL, "w", encoding="utf-8", newline="\n") as f:
        f.write(php)
    with open(ZIEL.replace(".php", ".js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("(function(){var s=document.createElement('style');s.textContent=" + json.dumps(CSS)
                + ";document.head.appendChild(s);})();\n" + js)
    print(f"{os.path.abspath(ZIEL)}: {len(daten)} Haeuser")


if __name__ == "__main__":
    main()
