<?php
/**
 * Katalog-Countdown (plans/katalog-countdown-v1.md). Erzeugt von
 * born2thrill-local-workbench/scripts/katalog-countdown-snippet.py -- nicht von
 * Hand aendern, neu erzeugen. Stand 2026-11-08 11:03: 119 von 274 fertig.
 * Nur fuer eingeloggte Bearbeiter, nur auf Seiten mit [grundriss_katalog].
 */
add_action( 'wp_footer', function () {
	// Team: auch wer mit dem Website-Zugang (Snippet 13) drin ist, sieht den Countdown.
	if ( is_admin() || ! ( current_user_can( 'edit_posts' ) || ( function_exists( 'b2t_zugang_ok' ) && b2t_zugang_ok() ) ) ) {
		return;
	}
	$post = get_post();
	if ( ! $post || ! has_shortcode( $post->post_content, 'grundriss_katalog' ) ) {
		return;
	}
	?>
<style id="gk-countdown-css">
.gk-cd{background:#1d2023;color:#e8e8e8;border:1px solid #3a3f44;padding:14px 18px;margin:0 0 14px;font:14px/1.45 system-ui,sans-serif}
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
</style>
<script id="gk-countdown-js">
(function () {
	var C = {"gesamt":274,"fertig":119,"offen":155,"schritte":[{"titel":"Bauen","plaene":["bungalow_3_600","bungalow_4_600k_1","bungalow_4_600k_2","bungalow_4_600k_3","cubicasa_review_high_quality_architectural_832","german_catalog_review_bungalow_3_1_1_b85","german_catalog_review_onehalfstorey_1_1_1_efh_120","german_catalog_review_onehalfstorey_1_2_1_efh_140_1","german_catalog_review_onehalfstorey_1_5_16_efh_160","german_catalog_review_onehalfstorey_1_6_1_efh_190","german_catalog_review_onehalfstorey_1_6_2_efh_190","german_catalog_review_twostorey_5_1_1_sv_130","german_catalog_review_twostorey_5_1_2_sv_130","german_catalog_review_twostorey_5_3_1_sv_145","german_catalog_review_twostorey_5_4_1_sv_170_1","german_catalog_review_twostorey_5_6_3_sv_195","onehalfstorey_003","onehalfstorey_006","onehalfstorey_012","onehalfstorey_020","onehalfstorey_022","onehalfstorey_023","onehalfstorey_027","onehalfstorey_028","onehalfstorey_033","onehalfstorey_037","onehalfstorey_038","onehalfstorey_040","onehalfstorey_041","other_1_5_story_with_cellar","other_2_familienhaus","other_2_famlilienhaus","twostorey_007","twostorey_010","twostorey_012","twostorey_015","twostorey_017","twostorey_023","twostorey_026","twostorey_028","twostorey_029","twostorey_030","twostorey_032","twostorey_033","twostorey_034","twostorey_042","twostorey_2_familien"]},{"titel":"Codex-Bilder fehlen","plaene":["bungalow_003","bungalow_008","bungalow_009","bungalow_010","bungalow_011","bungalow_012","bungalow_016","bungalow_017","bungalow_018","bungalow_019","bungalow_022","bungalow_023","bungalow_024","bungalow_025","bungalow_027","bungalow_029","bungalow_030","bungalow_031","bungalow_032","bungalow_034","bungalow_035","bungalow_040_10","bungalow_040_11","bungalow_040_12","bungalow_040_13","bungalow_040_14","bungalow_040_15","bungalow_040_16","bungalow_040_17","bungalow_040_18","bungalow_040_19","bungalow_040_20","bungalow_040_21","bungalow_040_22","bungalow_040_23","bungalow_040_26","bungalow_040_27","bungalow_040_29","bungalow_040_3","bungalow_040_30","bungalow_040_37","bungalow_040_4","bungalow_040_41","bungalow_040_43","bungalow_040_45","bungalow_040_5","bungalow_040_6","bungalow_040_7","bungalow_040_8","bungalow_040_9","bungalow_2_familienhaus","german_catalog_review_bungalow_3_4_4_b_120","german_catalog_review_bungalow_3_5_7_b_145","german_catalog_review_bungalow_4_1_6_wb_105","german_catalog_review_bungalow_4_2_3_wb_115","german_catalog_review_twostorey_5_3_6_sv_145","german_catalog_review_twostorey_5_6_1_sv_195","onehalfstorey_002","onehalfstorey_005","onehalfstorey_008","onehalfstorey_009","onehalfstorey_011","onehalfstorey_013","onehalfstorey_014","onehalfstorey_015","onehalfstorey_016","onehalfstorey_017","onehalfstorey_018","onehalfstorey_019","onehalfstorey_024","onehalfstorey_025","onehalfstorey_026","onehalfstorey_030","onehalfstorey_031","onehalfstorey_032","onehalfstorey_034","onehalfstorey_035","onehalfstorey_036","onehalfstorey_039","onehalfstorey_043","twostorey_003","twostorey_004","twostorey_005","twostorey_008","twostorey_009","twostorey_011","twostorey_013","twostorey_014","twostorey_016","twostorey_018","twostorey_019","twostorey_020","twostorey_021","twostorey_022","twostorey_024","twostorey_025","twostorey_027","twostorey_031","twostorey_035","twostorey_036","twostorey_037","twostorey_038","twostorey_039","twostorey_040","twostorey_041","twostorey_043","twostorey_044","twostorey_057"]}],"stand":"2026-11-08 11:03"};
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
		box.innerHTML = html;
		wrap.insertBefore(box, wrap.firstChild);
	}
	if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
	else start();
	setTimeout(start, 1500);
})();
</script>
	<?php
} );
