<?php
/**
 * Katalog Fragebogen-Filter (Zusatz zu Snippet 9 "Grundriss-Katalog").
 * Erzeugt von born2thrill-local-workbench/scripts/katalog-fragebogen-snippet.py
 * -- nicht von Hand aendern, neu erzeugen. 257 Haeuser.
 * Nur Frontend, nur auf Seiten mit [grundriss_katalog]. Liest nichts aus der
 * Datenbank und schreibt nichts.
 */
add_action( 'wp_footer', function () {
	if ( is_admin() ) {
		return;
	}
	$post = get_post();
	if ( ! $post || ! has_shortcode( $post->post_content, 'grundriss_katalog' ) ) {
		return;
	}
	?>
<style id="gk-fragebogen-css">
.gk-search > .gk-row:not(.gk-fb), .gk-search > .gk-tags{display:none !important}
.gk-fb{align-items:end}
.gk-fb input[type=search]{min-width:15rem}
.gk-fb-zahl{align-self:center;opacity:.8}
.gk-fb-info{margin:.3rem 0 0;font-size:.85rem;font-weight:600}
</style>
<script id="gk-fragebogen-js">
(function () {
	// D[id] = [hausart, zimmer, preis, gaeste_wc_dusche, anzeigename, wohneinheiten, wohnflaeche_m2]
	var D = {"bungalow_001":["bungalow",3,354000,0,"",1,118],"bungalow_003":["efh",5,561000,0,"",1,187],"bungalow_007":["efh",4,576000,1,"2-Geschosser am Hang (BAH)",1,192],"bungalow_008":["bungalow",3,348000,0,"",1,116],"bungalow_009":["bungalow",2,231000,1,"",1,77],"bungalow_010":["bungalow",4,333000,0,"",1,111],"bungalow_011":["bungalow",3,300000,0,"",1,100],"bungalow_012":["bungalow",4,348000,1,"",1,116],"bungalow_013":["bungalow",3,315000,0,"",1,105],"bungalow_014":["bungalow",4,354000,0,"",1,118],"bungalow_015":["bungalow",3,378000,0,"",1,126],"bungalow_016":["bungalow",3,357000,0,"",1,119],"bungalow_017":["bungalow",4,393000,0,"",1,131],"bungalow_018":["bungalow",4,375000,0,"",1,125],"bungalow_019":["bungalow",4,390000,0,"",1,130],"bungalow_021":["bungalow",3,339000,0,"",1,113],"bungalow_022":["bungalow",2,264000,1,"",1,88],"bungalow_023":["bungalow",3,405000,0,"",1,135],"bungalow_024":["bungalow",4,459000,0,"",1,153],"bungalow_025":["bungalow",3,369000,1,"",1,123],"bungalow_027":["bungalow",3,372000,0,"",1,124],"bungalow_028":["bungalow",3,306000,1,"",1,102],"bungalow_029":["bungalow",4,348000,0,"",1,116],"bungalow_030":["bungalow",4,411000,1,"",1,137],"bungalow_031":["bungalow",4,396000,1,"",1,132],"bungalow_032":["bungalow",3,420000,1,"",1,140],"bungalow_033":["bungalow",4,399000,1,"",1,133],"bungalow_034":["efh",5,726000,1,"Villa",1,242],"bungalow_035":["bungalow",4,486000,0,"",1,162],"bungalow_037":["bungalow",3,300000,0,"",1,100],"bungalow_040_10":["bungalow",4,387000,0,"",1,129],"bungalow_040_11":["bungalow",4,405000,0,"",1,135],"bungalow_040_12":["bungalow",3,378000,0,"",1,126],"bungalow_040_13":["bungalow",3,405000,0,"",1,135],"bungalow_040_14":["bungalow",3,396000,0,"",1,132],"bungalow_040_15":["bungalow",3,456000,1,"",1,152],"bungalow_040_17":["bungalow",4,438000,0,"",1,146],"bungalow_040_18":["bungalow",3,435000,0,"",1,145],"bungalow_040_185":["efh",5,855000,1,"",1,285],"bungalow_040_20":["bungalow",3,348000,1,"",1,116],"bungalow_040_200":["bungalow",3,351000,0,"",1,117],"bungalow_040_21":["bungalow",3,453000,1,"",1,151],"bungalow_040_22":["bungalow",4,417000,0,"",1,139],"bungalow_040_23":["bungalow",4,516000,0,"",1,172],"bungalow_040_24":["bungalow",4,441000,0,"",1,147],"bungalow_040_26":["bungalow",4,492000,0,"",1,164],"bungalow_040_27":["bungalow",3,549000,0,"",1,183],"bungalow_040_28":["bungalow",5,474000,1,"",1,158],"bungalow_040_29":["bungalow",4,459000,0,"",1,153],"bungalow_040_3":["bungalow",3,318000,0,"",1,106],"bungalow_040_30":["bungalow",5,495000,1,"",1,165],"bungalow_040_34":["bungalow",3,396000,0,"",1,132],"bungalow_040_37":["bungalow",4,402000,0,"",1,134],"bungalow_040_38":["bungalow",4,357000,0,"",1,119],"bungalow_040_4":["bungalow",3,342000,0,"",1,114],"bungalow_040_41":["bungalow",4,447000,0,"",1,149],"bungalow_040_43":["bungalow",4,498000,1,"",1,166],"bungalow_040_44":["bungalow",4,378000,0,"",1,126],"bungalow_040_45":["bungalow",4,438000,1,"",1,146],"bungalow_040_46":["bungalow",4,408000,0,"",1,136],"bungalow_040_47":["bungalow",5,456000,0,"",1,152],"bungalow_040_48":["bungalow",5,384000,1,"",1,128],"bungalow_040_5":["bungalow",4,441000,0,"",1,147],"bungalow_040_66":["bungalow",3,534000,1,"",1,178],"bungalow_040_8":["bungalow",3,390000,0,"",1,130],"bungalow_2_familienhaus":["zfh",4,603000,1,"2.Geschosser",2,201],"bungalow_3_600":["bungalow",3,642000,0,"",1,214],"bungalow_4_600k_1":["bungalow",5,681000,1,"",1,227],"bungalow_4_600k_2":["bungalow",4,648000,1,"",1,216],"bungalow_4_600k_3":["bungalow",4,651000,1,"",1,217],"bungalow_generationat":["efh",2,765000,0,"Ausbaureserve in DG",1,255],"bungalow_m":["bungalow",2,243000,1,"",1,81],"bungalow_t":["bungalow",4,420000,0,"",1,140],"bungalow_tv1":["bungalow",3,450000,0,"",1,150],"bungalow_v1":["bungalow",3,516000,1,"",1,172],"bungalow_xb":["bungalow",3,414000,0,"",1,138],"bungalow_xbv1":["bungalow",3,477000,0,"",1,159],"bungalow_xbv2":["bungalow",4,585000,0,"",1,195],"bungalow_xvv6":["efh",5,666000,1,"",1,222],"cubicasa_review_high_quality_architectural_832":["bungalow",3,240000,0,"",1,80],"german_catalog_review_bungalow_3_1_1_b85":["bungalow",3,291000,0,"",1,97],"german_catalog_review_bungalow_3_1_2_b_85":["bungalow",3,303000,0,"",1,101],"german_catalog_review_bungalow_3_2_1_b_100_1":["bungalow",4,399000,0,"",1,133],"german_catalog_review_bungalow_3_2_2_b_100_1":["bungalow",3,387000,0,"",1,129],"german_catalog_review_bungalow_3_2_3_b_100_1":["bungalow",3,318000,0,"",1,106],"german_catalog_review_bungalow_3_2_4_b_100_1":["bungalow",3,378000,0,"",1,126],"german_catalog_review_bungalow_3_2_5_b_100_1":["bungalow",4,321000,0,"",1,107],"german_catalog_review_bungalow_3_3_1_b_100_2":["bungalow",4,402000,0,"",1,134],"german_catalog_review_bungalow_3_3_2_b_100_2":["bungalow",3,405000,0,"",1,135],"german_catalog_review_bungalow_3_3_3_b_100_2":["bungalow",3,336000,0,"",1,112],"german_catalog_review_bungalow_3_3_4_b_100_2":["bungalow",3,291000,0,"",1,97],"german_catalog_review_bungalow_3_4_1_b120":["bungalow",3,390000,1,"",1,130],"german_catalog_review_bungalow_3_4_2_b_120":["bungalow",4,456000,1,"",1,152],"german_catalog_review_bungalow_3_4_3_b_120":["bungalow",4,366000,0,"",1,122],"german_catalog_review_bungalow_3_4_4_b_120":["bungalow",3,372000,0,"",1,124],"german_catalog_review_bungalow_3_4_5_b_120":["bungalow",3,393000,0,"",1,131],"german_catalog_review_bungalow_3_4_6_b_120":["bungalow",3,345000,1,"",1,115],"german_catalog_review_bungalow_3_4_7_b_120":["bungalow",3,375000,1,"",1,125],"german_catalog_review_bungalow_3_5_1_b_145":["bungalow",4,483000,1,"",1,161],"german_catalog_review_bungalow_3_5_7_b_145":["bungalow",4,510000,1,"",1,170],"german_catalog_review_bungalow_4_1_1_wb_105":["bungalow",3,417000,0,"",1,139],"german_catalog_review_bungalow_4_1_2_wb_105":["bungalow",4,348000,1,"",1,116],"german_catalog_review_bungalow_4_1_3_wb_105":["bungalow",3,324000,0,"",1,108],"german_catalog_review_bungalow_4_1_4_wb_105":["bungalow",3,324000,0,"",1,108],"german_catalog_review_bungalow_4_1_5_wb_105":["bungalow",3,336000,0,"",1,112],"german_catalog_review_bungalow_4_1_6_wb_105":["bungalow",3,396000,0,"",1,132],"german_catalog_review_bungalow_4_1_7_wb_105":["bungalow",4,414000,0,"",1,138],"german_catalog_review_bungalow_4_2_1_wb_115":["bungalow",3,387000,0,"",1,129],"german_catalog_review_bungalow_4_2_2_wb_115":["bungalow",3,369000,0,"",1,123],"german_catalog_review_bungalow_4_2_3_wb_115":["bungalow",4,444000,0,"",1,148],"german_catalog_review_bungalow_4_2_4_wb_115":["bungalow",3,372000,0,"",1,124],"german_catalog_review_bungalow_4_2_5_wb_115":["bungalow",4,408000,0,"",1,136],"german_catalog_review_bungalow_4_2_6_wb_115":["bungalow",4,378000,1,"",1,126],"german_catalog_review_bungalow_4_3_1_wb_125":["bungalow",4,366000,0,"",1,122],"german_catalog_review_bungalow_4_3_2_wb_125":["bungalow",4,408000,0,"",1,136],"german_catalog_review_bungalow_4_3_3_wb_125":["bungalow",4,405000,1,"",1,135],"german_catalog_review_bungalow_4_3_4_wb_125":["bungalow",4,390000,0,"",1,130],"german_catalog_review_bungalow_4_3_5_wb_125":["bungalow",4,405000,1,"",1,135],"german_catalog_review_bungalow_4_3_6_wb_125":["bungalow",4,423000,1,"",1,141],"german_catalog_review_bungalow_4_3_7_wb_125":["bungalow",4,396000,0,"",1,132],"german_catalog_review_onehalfstorey_1_1_1_efh_120":["efh",4,519000,0,"",1,173],"german_catalog_review_onehalfstorey_1_1_2_efh_120":["efh",4,414000,0,"",1,138],"german_catalog_review_onehalfstorey_1_2_1_efh_140_1":["efh",4,420000,0,"",1,140],"german_catalog_review_onehalfstorey_1_2_2_efh_140_1":["efh",5,561000,1,"",1,187],"german_catalog_review_onehalfstorey_1_5_16_efh_160":["efh",5,558000,1,"",1,186],"german_catalog_review_onehalfstorey_1_5_1_efh_160":["efh",5,549000,0,"",1,183],"german_catalog_review_onehalfstorey_1_6_1_efh_190":["efh",5,699000,1,"",1,233],"german_catalog_review_onehalfstorey_1_6_2_efh_190":["efh",5,645000,0,"",1,215],"german_catalog_review_twostorey_5_1_1_sv_130":["efh",4,492000,0,"",1,164],"german_catalog_review_twostorey_5_1_2_sv_130":["efh",4,531000,0,"",1,177],"german_catalog_review_twostorey_5_3_1_sv_145":["efh",5,666000,0,"",1,222],"german_catalog_review_twostorey_5_3_6_sv_145":["efh",5,522000,1,"",1,174],"german_catalog_review_twostorey_5_4_1_sv_170_1":["efh",5,720000,1,"",1,240],"german_catalog_review_twostorey_5_6_1_sv_195":["efh",5,822000,1,"",1,274],"german_catalog_review_twostorey_5_6_3_sv_195":["efh",5,897000,0,"",1,299],"onehalfstorey_002":["efh",5,732000,0,"",1,244],"onehalfstorey_003":["efh",5,435000,1,"",1,145],"onehalfstorey_005":["efh",5,603000,0,"",1,201],"onehalfstorey_006":["efh",4,492000,0,"",1,164],"onehalfstorey_007":["efh",4,552000,0,"",1,184],"onehalfstorey_008":["efh",5,546000,1,"",1,182],"onehalfstorey_009":["efh",5,471000,1,"",1,157],"onehalfstorey_010":["efh",5,480000,1,"",1,160],"onehalfstorey_011":["efh",4,579000,0,"",1,193],"onehalfstorey_012":["efh",3,390000,0,"",1,130],"onehalfstorey_012_129":["efh",3,387000,0,"",1,129],"onehalfstorey_012_129_129":["efh",4,387000,0,"",1,129],"onehalfstorey_013":["efh",4,537000,0,"",1,179],"onehalfstorey_014":["efh",5,669000,0,"",1,223],"onehalfstorey_015":["efh",5,558000,0,"",1,186],"onehalfstorey_016":["efh",5,645000,0,"",1,215],"onehalfstorey_017":["efh",5,486000,1,"",1,162],"onehalfstorey_018":["efh",5,450000,1,"",1,150],"onehalfstorey_019":["efh",5,663000,0,"",1,221],"onehalfstorey_020":["efh",5,453000,0,"",1,151],"onehalfstorey_021":["efh",3,471000,0,"",1,157],"onehalfstorey_022":["efh",4,423000,0,"",1,141],"onehalfstorey_023":["efh",4,471000,0,"",1,157],"onehalfstorey_024":["efh",4,546000,0,"",1,182],"onehalfstorey_025":["efh",4,525000,0,"",1,175],"onehalfstorey_026":["efh",4,729000,0,"",1,243],"onehalfstorey_027":["efh",5,657000,0,"",1,219],"onehalfstorey_028":["efh",4,663000,0,"",1,221],"onehalfstorey_029":["efh",5,639000,0,"",1,213],"onehalfstorey_030":["efh",4,513000,0,"",1,171],"onehalfstorey_031":["efh",5,615000,0,"",1,205],"onehalfstorey_032":["efh",5,633000,0,"",1,211],"onehalfstorey_033":["efh",4,654000,0,"",1,218],"onehalfstorey_034":["efh",4,609000,0,"",1,203],"onehalfstorey_035":["efh",5,588000,0,"",1,196],"onehalfstorey_036":["efh",5,528000,0,"",1,176],"onehalfstorey_037":["efh",5,531000,0,"",1,177],"onehalfstorey_038":["efh",5,594000,1,"",1,198],"onehalfstorey_039":["efh",4,540000,0,"",1,180],"onehalfstorey_040":["efh",5,873000,1,"",1,291],"onehalfstorey_041":["efh",5,792000,1,"",1,264],"onehalfstorey_043":["efh",5,555000,1,"",1,185],"onehalfstorey_044":["efh",4,633000,0,"",1,211],"onehalfstorey_045":["efh",5,630000,0,"",1,210],"onehalfstorey_046":["dhh",5,522000,0,"",1,174],"onehalfstorey_efh120_s129":["efh",4,354000,0,"",1,118],"onehalfstorey_efh120_s129_dusche":["efh",4,354000,1,"",1,118],"onehalfstorey_ve":["efh",5,633000,0,"",1,211],"onehalfstorey_vm2":["efh",5,699000,1,"",1,233],"onehalfstorey_vv1":["efh",3,462000,0,"",1,154],"onehalfstorey_vv2":["efh",4,516000,0,"",1,172],"onehalfstorey_vv3":["efh",5,585000,0,"",1,195],"onehalfstorey_xv":["efh",5,615000,0,"",1,205],"onehalfstorey_xvv1":["efh",5,714000,1,"",1,238],"onehalfstorey_xvv2":["efh",5,690000,0,"",1,230],"other_1_5_story_with_cellar":["efh",5,1878000,0,"",1,626],"other_2_familienhaus":["zfh",5,654000,0,"",2,218],"other_2_famlilienhaus":["zfh",5,879000,0,"",2,293],"other_vito":["dhh",4,750000,0,"",1,250],"other_xvitv1":["dhh",5,891000,1,"",1,297],"twostorey_003":["efh",5,516000,0,"",1,172],"twostorey_004":["efh",4,612000,0,"",1,204],"twostorey_005":["efh",5,600000,0,"",1,200],"twostorey_007":["efh",5,567000,1,"",1,189],"twostorey_008":["efh",5,537000,1,"",1,179],"twostorey_009":["efh",5,501000,0,"",1,167],"twostorey_010":["efh",5,471000,1,"",1,157],"twostorey_011":["efh",5,705000,1,"",1,235],"twostorey_012":["efh",5,411000,1,"",1,137],"twostorey_012_129":["efh",5,390000,1,"",1,130],"twostorey_013":["efh",5,603000,0,"",1,201],"twostorey_014":["efh",4,576000,0,"",1,192],"twostorey_015":["efh",4,588000,0,"",1,196],"twostorey_016":["efh",4,552000,0,"",1,184],"twostorey_017":["efh",4,489000,0,"",1,163],"twostorey_018":["efh",4,441000,0,"",1,147],"twostorey_019":["efh",4,507000,0,"",1,169],"twostorey_020":["efh",4,708000,0,"",1,236],"twostorey_021":["efh",4,543000,0,"",1,181],"twostorey_022":["efh",4,630000,0,"",1,210],"twostorey_023":["efh",5,489000,1,"",1,163],"twostorey_024":["efh",5,597000,0,"",1,199],"twostorey_025":["efh",4,387000,0,"",1,129],"twostorey_025_143":["efh",4,429000,0,"",1,143],"twostorey_026":["efh",5,411000,0,"",1,137],"twostorey_027":["efh",5,489000,0,"",1,163],"twostorey_028":["efh",5,600000,0,"",1,200],"twostorey_029":["efh",4,519000,0,"",1,173],"twostorey_030":["efh",4,543000,0,"",1,181],"twostorey_031":["efh",5,651000,1,"",1,217],"twostorey_032":["efh",5,615000,0,"",1,205],"twostorey_033":["efh",4,612000,0,"",1,204],"twostorey_034":["efh",4,633000,0,"",1,211],"twostorey_035":["efh",4,507000,0,"",1,169],"twostorey_036":["efh",4,540000,0,"",1,180],"twostorey_037":["efh",5,504000,0,"",1,168],"twostorey_038":["efh",5,699000,1,"",1,233],"twostorey_039":["efh",5,657000,1,"",1,219],"twostorey_040":["efh",4,837000,1,"",1,279],"twostorey_041":["efh",5,750000,1,"",1,250],"twostorey_042":["efh",5,549000,1,"",1,183],"twostorey_043":["efh",4,633000,0,"",1,211],"twostorey_045":["efh",5,576000,0,"",1,192],"twostorey_048":["efh",5,744000,0,"",1,248],"twostorey_053":["efh",4,648000,0,"",1,216],"twostorey_054":["efh",3,639000,0,"",1,213],"twostorey_055":["efh",3,666000,0,"",1,222],"twostorey_056":["efh",4,708000,0,"",1,236],"twostorey_057":["efh",4,645000,0,"",1,215],"twostorey_058":["efh",4,528000,0,"",1,176],"twostorey_059":["efh",5,609000,0,"",1,203],"twostorey_060":["efh",4,537000,1,"",1,179],"twostorey_2_familien":["zfh",5,945000,0,"",2,315],"twostorey_xvbah":["efh",4,639000,1,"",1,213],"twostorey_xvi":["efh",5,597000,0,"",1,199],"twostorey_xvit":["dhh",4,684000,0,"",1,228],"twostorey_xvv1":["efh",5,780000,1,"",1,260],"twostorey_xvv2":["efh",5,675000,1,"",1,225],"twostorey_xvv2_2":["efh",4,648000,0,"",1,216],"twostorey_xvv4":["efh",5,768000,1,"",1,256],"twostorey_xvv5":["efh",5,645000,1,"",1,215],"twostorey_xvv6":["efh",4,648000,1,"",1,216]};
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
</script>
	<?php
}, 100 );
