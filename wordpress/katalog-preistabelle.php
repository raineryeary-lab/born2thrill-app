<?php
/**
 * Katalog-Preistabelle (plans/katalog-preistabelle-v1.md). Erzeugt von
 * born2thrill-local-workbench/scripts/katalog-preistabelle-snippet.py -- nicht
 * von Hand aendern, neu erzeugen. Stand 2026-11-11 17:52: 275 Haeuser.
 * Fuer Bearbeiter und Team (Website-Zugang), nur auf Seiten mit [grundriss_katalog].
 */
add_action( 'wp_footer', function () {
	// Team: auch wer mit dem Website-Zugang (Snippet 13) drin ist, sieht die Regler.
	if ( is_admin() || ! ( current_user_can( 'edit_posts' ) || ( function_exists( 'b2t_zugang_ok' ) && b2t_zugang_ok() ) ) ) {
		return;
	}
	$post = get_post();
	if ( ! $post || ! has_shortcode( $post->post_content, 'grundriss_katalog' ) ) {
		return;
	}
	?>
<style id="gk-preistabelle-css">
.gk-pt{background:#1d2023;color:#e8e8e8;border:1px solid #3a3f44;margin:0 0 14px;font:14px/1.45 system-ui,sans-serif}
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
.gk-pt label{cursor:pointer}.gk-pt-titel{margin:16px 0 2px;font-size:15px;color:#e8e8e8}.gk-pt-qm span{background:#25292d;border-radius:5px;padding:3px 10px}.gk-pt-qm b{color:#7fc8a9}
</style>
<script id="gk-preistabelle-js">
(function () {
	// D = [hausart, satztyp, zimmer, m2, preis_heute, volumen_m3]
	var D = [["Einfamilienhaus","A",6.0,626.0,1878000,1700],["Zweifamilienhaus","Z",6.0,315.0,945000,823],["Einfamilienhaus","Z",5.0,311.0,933000,815],["Doppelhaus","Z",6.0,302.0,906000,754],["Zweifamilienhaus","Z",7.0,294.0,882000,767],["Einfamilienhaus","A",5.0,291.0,873000,694],["Einfamilienhaus","Z",4.0,279.0,837000,704],["Einfamilienhaus","Z",5.0,271.0,813000,711],["Einfamilienhaus","A",6.0,264.0,792000,656],["Einfamilienhaus","Z",5.0,263.0,789000,687],["Einfamilienhaus","Z",5.0,260.0,780000,704],["Einfamilienhaus","Z",6.0,256.0,768000,690],["Einfamilienhaus","Z",5.0,250.0,750000,635],["Doppelhaus","Z",4.0,246.0,738000,605],["Einfamilienhaus","A",5.0,244.0,732000,578],["Einfamilienhaus","A",5.0,244.0,732000,569],["Einfamilienhaus","A",4.0,243.0,729000,601],["Einfamilienhaus","Z",5.0,242.0,726000,634],["Einfamilienhaus","A",5.0,242.0,726000,595],["Einfamilienhaus","Z",4.0,236.0,708000,489],["Einfamilienhaus","Z",5.0,235.0,705000,608],["Einfamilienhaus","Z",5.0,235.0,705000,616],["Einfamilienhaus","Z",5.0,235.0,705000,609],["Einfamilienhaus","Z",6.0,233.0,699000,629],["Einfamilienhaus","A",2.0,228.0,684000,541],["Doppelhaus","Z",4.0,228.0,684000,610],["Bungalow","B",5.0,227.0,681000,602],["Einfamilienhaus","A",5.0,226.0,678000,554],["Einfamilienhaus","A",5.0,223.0,669000,558],["Einfamilienhaus","A",6.0,221.0,663000,531],["Einfamilienhaus","A",5.0,221.0,663000,530],["Einfamilienhaus","A",4.0,221.0,663000,571],["Einfamilienhaus","Z",5.0,219.0,657000,572],["Einfamilienhaus","A",5.0,219.0,657000,542],["Einfamilienhaus","Z",6.0,219.0,657000,515],["Einfamilienhaus","A",4.0,218.0,654000,564],["Zweifamilienhaus","Z",7.0,218.0,654000,572],["Bungalow","B",4.0,217.0,651000,570],["Einfamilienhaus","Z",5.0,217.0,651000,563],["Bungalow","B",4.0,216.0,648000,566],["Einfamilienhaus","A",6.0,216.0,648000,527],["Einfamilienhaus","A",5.0,215.0,645000,518],["Einfamilienhaus","A",5.0,215.0,645000,524],["Einfamilienhaus","Z",5.0,215.0,645000,558],["Bungalow","B",3.0,214.0,642000,568],["Einfamilienhaus","A",5.0,213.0,639000,508],["Einfamilienhaus","Z",4.0,213.0,639000,547],["Einfamilienhaus","Z",4.0,213.0,639000,544],["Einfamilienhaus","Z",4.0,213.0,639000,542],["Einfamilienhaus","Z",5.0,211.0,633000,579],["Einfamilienhaus","A",5.0,211.0,633000,520],["Einfamilienhaus","Z",4.0,211.0,633000,555],["Einfamilienhaus","Z",4.0,211.0,633000,559],["Einfamilienhaus","Z",5.0,211.0,633000,551],["Einfamilienhaus","Z",4.0,210.0,630000,545],["Einfamilienhaus","A",6.0,209.0,627000,509],["Einfamilienhaus","Z",4.0,209.0,627000,540],["Einfamilienhaus","Z",4.0,209.0,627000,724],["Einfamilienhaus","A",5.0,208.0,624000,510],["Einfamilienhaus","Z",5.0,208.0,624000,547],["Einfamilienhaus","Z",4.0,207.0,621000,545],["Einfamilienhaus","Z",3.0,206.0,618000,539],["Einfamilienhaus","Z",5.0,206.0,618000,523],["Einfamilienhaus","A",5.0,205.0,615000,505],["Einfamilienhaus","Z",5.0,205.0,615000,517],["Einfamilienhaus","Z",4.0,204.0,612000,539],["Einfamilienhaus","Z",4.0,204.0,612000,550],["Einfamilienhaus","Z",4.0,204.0,612000,526],["Einfamilienhaus","A",4.0,203.0,609000,501],["Einfamilienhaus","A",5.0,201.0,603000,496],["Einfamilienhaus","Z",5.0,201.0,603000,529],["Zweifamilienhaus","Z",4.0,200.0,600000,522],["Einfamilienhaus","Z",5.0,200.0,600000,527],["Einfamilienhaus","Z",5.0,200.0,600000,527],["Einfamilienhaus","Z",6.0,199.0,597000,526],["Einfamilienhaus","A",6.0,198.0,594000,486],["Einfamilienhaus","A",5.0,196.0,588000,484],["Einfamilienhaus","Z",4.0,196.0,588000,504],["Einfamilienhaus","Z",4.0,196.0,588000,515],["Bungalow","B",4.0,195.0,585000,504],["Einfamilienhaus","A",4.0,193.0,579000,477],["Einfamilienhaus","Z",4.0,192.0,576000,528],["Einfamilienhaus","Z",4.0,192.0,576000,498],["Einfamilienhaus","A",5.0,189.0,567000,432],["Einfamilienhaus","Z",5.0,189.0,567000,497],["Einfamilienhaus","Z",5.0,188.0,564000,551],["Einfamilienhaus","Z",6.0,187.0,561000,494],["Einfamilienhaus","A",5.0,186.0,558000,457],["Einfamilienhaus","A",6.0,186.0,558000,457],["Einfamilienhaus","A",5.0,185.0,555000,499],["Einfamilienhaus","A",4.0,184.0,552000,452],["Einfamilienhaus","Z",4.0,184.0,552000,473],["Bungalow","B",3.0,183.0,549000,481],["Einfamilienhaus","Z",5.0,183.0,549000,478],["Einfamilienhaus","Z",3.0,183.0,549000,479],["Einfamilienhaus","Z",4.0,183.0,549000,477],["Einfamilienhaus","A",5.0,182.0,546000,416],["Einfamilienhaus","A",5.0,182.0,546000,443],["Einfamilienhaus","A",4.0,182.0,546000,450],["Einfamilienhaus","Z",4.0,182.0,546000,480],["Bungalow","B",4.0,181.0,543000,473],["Einfamilienhaus","Z",4.0,181.0,543000,476],["Einfamilienhaus","Z",4.0,181.0,543000,524],["Einfamilienhaus","A",4.0,180.0,540000,440],["Einfamilienhaus","Z",4.0,180.0,540000,448],["Einfamilienhaus","A",4.0,179.0,537000,437],["Einfamilienhaus","A",4.0,179.0,537000,440],["Einfamilienhaus","Z",5.0,179.0,537000,469],["Bungalow","B",3.0,178.0,534000,468],["Einfamilienhaus","A",5.0,177.0,531000,434],["Einfamilienhaus","A",5.0,176.0,528000,438],["Einfamilienhaus","A",4.0,175.0,525000,418],["Einfamilienhaus","Z",6.0,174.0,522000,551],["Einfamilienhaus","A",4.0,173.0,519000,439],["Einfamilienhaus","A",4.0,173.0,519000,419],["Einfamilienhaus","Z",4.0,173.0,519000,458],["Bungalow","B",4.0,172.0,516000,450],["Bungalow","B",3.0,172.0,516000,452],["Einfamilienhaus","Z",5.0,172.0,516000,451],["Einfamilienhaus","Z",5.0,172.0,516000,453],["Einfamilienhaus","A",4.0,171.0,513000,416],["Einfamilienhaus","A",5.0,171.0,513000,443],["Bungalow","B",4.0,170.0,510000,446],["Einfamilienhaus","Z",4.0,170.0,510000,449],["Einfamilienhaus","A",3.0,169.0,507000,408],["Einfamilienhaus","Z",4.0,169.0,507000,441],["Einfamilienhaus","Z",4.0,169.0,507000,444],["Einfamilienhaus","Z",5.0,168.0,504000,478],["Doppelhaus","A",5.0,167.0,501000,400],["Einfamilienhaus","Z",5.0,167.0,501000,440],["Bungalow","B",4.0,166.0,498000,435],["Bungalow","B",5.0,165.0,495000,433],["Einfamilienhaus","Z",5.0,165.0,495000,455],["Bungalow","B",4.0,164.0,492000,429],["Einfamilienhaus","Z",4.0,164.0,492000,432],["Einfamilienhaus","A",4.0,164.0,492000,401],["Einfamilienhaus","Z",4.0,163.0,489000,414],["Einfamilienhaus","Z",5.0,163.0,489000,346],["Einfamilienhaus","Z",5.0,163.0,489000,403],["Bungalow","B",4.0,162.0,486000,425],["Bungalow","B",4.0,162.0,486000,422],["Einfamilienhaus","A",5.0,162.0,486000,398],["Einfamilienhaus","Z",6.0,161.0,483000,484],["Einfamilienhaus","Z",4.0,161.0,483000,427],["Einfamilienhaus","A",5.0,160.0,480000,384],["Bungalow","B",3.0,159.0,477000,408],["Bungalow","B",5.0,158.0,474000,414],["Einfamilienhaus","A",5.0,157.0,471000,383],["Einfamilienhaus","A",3.0,157.0,471000,383],["Einfamilienhaus","A",4.0,157.0,471000,374],["Einfamilienhaus","Z",5.0,157.0,471000,384],["Einfamilienhaus","Z",5.0,155.0,465000,433],["Bungalow","B",4.0,153.0,459000,400],["Bungalow","B",4.0,153.0,459000,400],["Bungalow","B",3.0,152.0,456000,402],["Bungalow","B",5.0,152.0,456000,397],["Bungalow","B",4.0,152.0,456000,398],["Bungalow","B",3.0,151.0,453000,401],["Einfamilienhaus","A",4.0,151.0,453000,340],["Einfamilienhaus","A",5.0,151.0,453000,370],["Bungalow","B",3.0,150.0,450000,393],["Einfamilienhaus","A",5.0,150.0,450000,369],["Bungalow","B",4.0,149.0,447000,391],["Bungalow","B",4.0,148.0,444000,386],["Bungalow","B",4.0,148.0,444000,388],["Bungalow","B",4.0,147.0,441000,386],["Bungalow","B",4.0,146.0,438000,384],["Bungalow","B",4.0,146.0,438000,383],["Bungalow","B",3.0,145.0,435000,383],["Einfamilienhaus","A",5.0,145.0,435000,353],["Einfamilienhaus","Z",4.0,143.0,429000,354],["Bungalow","B",4.0,141.0,423000,369],["Einfamilienhaus","A",4.0,141.0,423000,338],["Bungalow","B",3.0,140.0,420000,368],["Bungalow","B",4.0,140.0,420000,364],["Einfamilienhaus","A",4.0,140.0,420000,360],["Einfamilienhaus","Z",4.0,140.0,420000,359],["Bungalow","B",4.0,139.0,417000,368],["Bungalow","B",3.0,139.0,417000,368],["Bungalow","B",3.0,138.0,414000,361],["Bungalow","B",4.0,137.0,411000,360],["Bungalow","B",3.0,137.0,411000,360],["Bungalow","B",4.0,137.0,411000,359],["Einfamilienhaus","Z",5.0,137.0,411000,361],["Einfamilienhaus","Z",5.0,137.0,411000,348],["Bungalow","B",4.0,136.0,408000,357],["Bungalow","B",4.0,136.0,408000,357],["Bungalow","B",4.0,136.0,408000,356],["Bungalow","B",3.0,135.0,405000,354],["Bungalow","B",4.0,135.0,405000,356],["Bungalow","B",3.0,135.0,405000,355],["Bungalow","B",4.0,135.0,405000,355],["Bungalow","B",4.0,135.0,405000,354],["Bungalow","B",4.0,134.0,402000,351],["Bungalow","B",4.0,134.0,402000,351],["Bungalow","B",4.0,133.0,399000,347],["Bungalow","B",4.0,133.0,399000,352],["Bungalow","B",4.0,132.0,396000,346],["Bungalow","B",3.0,132.0,396000,350],["Bungalow","B",3.0,132.0,396000,347],["Bungalow","B",3.0,132.0,396000,347],["Bungalow","B",4.0,132.0,396000,347],["Bungalow","B",4.0,131.0,393000,345],["Bungalow","B",3.0,131.0,393000,342],["Bungalow","B",3.0,131.0,393000,343],["Bungalow","B",4.0,130.0,390000,340],["Bungalow","B",3.0,130.0,390000,341],["Bungalow","B",3.0,130.0,390000,342],["Bungalow","B",4.0,130.0,390000,342],["Bungalow","B",4.0,129.0,387000,338],["Bungalow","B",3.0,129.0,387000,337],["Bungalow","B",3.0,129.0,387000,338],["Einfamilienhaus","A",4.0,129.0,387000,286],["Bungalow","B",3.0,128.0,384000,336],["Bungalow","B",5.0,128.0,384000,337],["Bungalow","B",3.0,128.0,384000,335],["Bungalow","B",3.0,126.0,378000,331],["Bungalow","B",3.0,126.0,378000,334],["Bungalow","B",4.0,126.0,378000,330],["Bungalow","B",4.0,126.0,378000,331],["Bungalow","B",3.0,126.0,378000,332],["Bungalow","B",3.0,126.0,378000,330],["Bungalow","B",4.0,126.0,378000,331],["Bungalow","B",4.0,125.0,375000,329],["Bungalow","B",3.0,125.0,375000,329],["Bungalow","B",3.0,125.0,375000,327],["Einfamilienhaus","A",3.0,125.0,375000,296],["Bungalow","B",3.0,124.0,372000,325],["Bungalow","B",3.0,124.0,372000,325],["Bungalow","B",3.0,124.0,372000,327],["Bungalow","B",3.0,123.0,369000,322],["Bungalow","B",3.0,123.0,369000,323],["Bungalow","B",4.0,122.0,366000,321],["Bungalow","B",4.0,122.0,366000,321],["Bungalow","B",3.0,119.0,357000,313],["Bungalow","B",4.0,119.0,357000,313],["Bungalow","B",3.0,118.0,354000,308],["Bungalow","B",4.0,118.0,354000,310],["Bungalow","B",3.0,117.0,351000,307],["Bungalow","B",4.0,117.0,351000,305],["Bungalow","B",3.0,116.0,348000,306],["Bungalow","B",4.0,116.0,348000,304],["Bungalow","B",4.0,116.0,348000,304],["Bungalow","B",3.0,116.0,348000,361],["Bungalow","B",4.0,116.0,348000,304],["Bungalow","B",3.0,115.0,345000,301],["Bungalow","B",3.0,115.0,345000,302],["Bungalow","B",3.0,114.0,342000,299],["Bungalow","B",3.0,113.0,339000,295],["Bungalow","B",4.0,113.0,339000,296],["Bungalow","B",3.0,112.0,336000,297],["Bungalow","B",3.0,112.0,336000,294],["Bungalow","B",4.0,111.0,333000,290],["Bungalow","B",3.0,111.0,333000,291],["Bungalow","B",4.0,110.0,330000,287],["Bungalow","B",4.0,109.0,327000,287],["Bungalow","B",3.0,108.0,324000,281],["Bungalow","B",3.0,108.0,324000,285],["Bungalow","B",3.0,106.0,318000,278],["Bungalow","B",3.0,106.0,318000,278],["Bungalow","B",4.0,106.0,318000,280],["Bungalow","B",3.0,105.0,315000,275],["Bungalow","B",3.0,102.0,306000,266],["Bungalow","B",3.0,101.0,303000,265],["Bungalow","B",3.0,100.0,300000,261],["Bungalow","B",3.0,100.0,300000,262],["Bungalow","B",3.0,97.0,291000,256],["Bungalow","B",3.0,97.0,291000,254],["Bungalow","B",2.0,92.0,276000,242],["Bungalow","B",3.0,92.0,276000,240],["Bungalow","B",3.0,91.0,273000,240],["Bungalow","B",2.0,88.0,264000,232],["Bungalow","B",2.0,81.0,243000,208],["Bungalow","B",3.0,80.0,240000,215],["Bungalow","B",2.0,77.0,231000,202]];
	var STAND = '2026-11-11 17:52';
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
})();
</script>
	<?php
} );
