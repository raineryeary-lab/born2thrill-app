<?php
/**
 * Landingpage Hauskonfigurator (plans/landingpage-hauskonfigurator-v1.md).
 * Erzeugt von born2thrill-local-workbench/scripts/landingpage-snippet.py aus der
 * Seite des Kollegen (https://hausbau-konfigurator.de/vorschlag-landingpage) -- nicht von Hand aendern, neu erzeugen.
 * Gibt auf der Seite "hauskonfigurator" das komplette Dokument ohne Theme aus.
 */
add_action( 'template_redirect', function () {
	if ( ! is_page( 'hauskonfigurator' ) ) {
		return;
	}
	header( 'Content-Type: text/html; charset=utf-8' );
	echo <<<'B2T_LANDINGPAGE'
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hausbau-Konfigurator: Ihr Haus mit Grundriss, Außenansicht und Preis</title>
<!-- In OnePage: in das Feld "Code im Kopfbereich" einfügen (Schrift, Skript). -->
<meta name="theme-color" content="#ffffff">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script>
  // Hausbau-Konfigurator Landingpage
  // Ziel des Funnels (vorläufig die Testseite); Zielgruppen-Kacheln geben ?ziel= mit.
  const FUNNEL_URL = 'https://born2thrill.de/konfigurator/';

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-start]').forEach(a => {
      const url = new URL(FUNNEL_URL);
      if (a.dataset.start) url.searchParams.set('ziel', a.dataset.start);
      a.href = url.toString();
    });

    // Häufige Fragen: immer genau eine Antwort offen, Bereich behält seine Höhe
    const list = document.querySelector('.faq-list');
    if (!list) return;
    const items = [...list.querySelectorAll('details')];

    items.forEach(item => {
      item.querySelector('summary').addEventListener('click', event => {
        event.preventDefault();
        if (item.open) return;
        items.forEach(other => { other.open = other === item; });
      });
    });

    // Höhe der Liste auf die längste Antwort festlegen, damit nichts springt
    const lockHeight = () => {
      const current = items.find(item => item.open);
      list.style.minHeight = '';
      let max = 0;
      items.forEach(item => {
        items.forEach(other => { other.open = other === item; });
        max = Math.max(max, list.offsetHeight);
      });
      items.forEach(other => { other.open = other === current; });
      list.style.minHeight = max + 'px';
    };
    lockHeight();
    window.addEventListener('resize', lockHeight);
  });
</script>

<style>
/* Hausbau-Konfigurator Landingpage
   In OnePage: Inhalt dieser Datei in das Feld "Eigenes CSS" der Seite einfügen. */

/* Nur für OnePage: blendet den leeren Seitenbereich des Baukastens aus,
   damit die eigene Seite oben beginnt und nichts unsichtbar über den Knöpfen liegt.
   Lokal und in WordPress ohne Wirkung. */
#root {
  min-height: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
}

#root .con-kit-page {
  pointer-events: none !important;
}

/* Farben und Schrift wie im Funnel (hausklar-flug): weiß, rot, eckig.
   Sand ist 4 Helligkeitsstufen (L*) dunkler als Weiß, damit Abschnitte sichtbar wechseln.
   Blautöne sind 10 % und 5 % Blau auf Weiß. Alle Texte erfüllen WCAG AA (4,5:1). */
:root {
  --blue: #1d4e89;
  --accent: #d42a10;
  --accent-dark: #b8240b;
  --bg: #f8f4ea;
  --paper: #ffffff;
  --blue-tint: #e8edf3;
  --blue-soft: #f4f6f9;
  --ink: #201e1d;
  --muted: #6b6968;
  --rule: rgba(32, 30, 29, .14);
  --font: "Archivo", "Segoe UI", system-ui, sans-serif;
  --header: 64px;
}

* {
  box-sizing: border-box
}

html,
body {
  margin: 0
}

/* Grundfarbe weiß: Safari färbt damit die Flächen hinter den Browserleisten oben und unten.
   Das Sand liegt nur auf den Abschnitten selbst. */
html,
body {
  background: var(--paper)
}

.hero,
section {
  background: var(--bg)
}

body {
  color: var(--ink);
  font-family: var(--font);
  line-height: 1.45;
  -webkit-font-smoothing: antialiased
}

svg {
  display: block
}

/* Zeilen möglichst gleich lang umbrechen */
h1,
h2,
h3,
.ask,
.lead,
.goal b,
.goal small,
.facts b,
.path b {
  text-wrap: balance
}

.text,
.path p,
.facts span,
.col li span {
  text-wrap: pretty
}

.wrap {
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding-left: max(32px, env(safe-area-inset-left, 0px));
  padding-right: max(32px, env(safe-area-inset-right, 0px))
}

/* Kopfzeile weiß mit Linie, damit sie sich vom sandfarbenen ersten Bildschirm abhebt */
body>header {
  background: var(--paper);
  border-bottom: 1px solid var(--rule)
}

header .wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header)
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 20px;
  letter-spacing: -.015em;
  color: var(--ink);
  text-decoration: none
}

.logo b {
  font-weight: 800;
  color: var(--blue)
}

.head-note {
  font-size: 14px;
  color: var(--muted)
}

/* Erster Bildschirm: Versprechen, Einstieg, Los geht's – ohne Scrollen */
.hero {
  min-height: calc(100svh - var(--header));
  display: flex;
  align-items: center;
  padding: clamp(16px, 4vh, 48px) 0
}

/* Beide Spalten gleich hoch: Ober- und Unterkanten liegen auf einer Linie */
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr);
  gap: clamp(40px, 5vw, 72px);
  align-items: center
}

.hero-text {
  display: flex;
  flex-direction: column
}

.eyebrow {
  display: inline-block;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: clamp(12px, 2.6vh, 24px)
}

h1 {
  /* erste Zeile ist ca. 10,6 × Schriftgröße breit und muss in die linke Spalte passen */
  font-size: max(30px, min(4.5vw, 58px, 8.5vh));
  line-height: 1.02;
  letter-spacing: -.035em;
  font-weight: 800;
  margin: 0 0 clamp(16px, 3.4vh, 32px)
}

/* Zwei Zeilen, beide etwa gleich breit (ca. 10,6 × Schriftgröße) */
h1>span {
  display: block;
  white-space: nowrap
}

h1 em {
  font-style: normal;
  color: var(--blue)
}

.lead {
  font-size: clamp(16px, 2.8vh, 21px);
  color: var(--muted);
  margin: 0 0 clamp(24px, 5vh, 48px);
  max-width: 30em
}

/* Emotionaler Einstieg: Besucher ordnet sich selbst zu */
.panel {
  background: var(--paper);
  padding: clamp(20px, 4vh, 36px);
  display: flex;
  flex-direction: column
}

.ask {
  font-weight: 800;
  font-size: clamp(18px, 2.6vh, 21px);
  letter-spacing: -.015em;
  line-height: 1.2;
  margin: 0 0 clamp(12px, 2.4vh, 20px)
}

.goals {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: 1fr;
  gap: 10px;
  margin: 0
}

.goal {
  position: relative;
  font: inherit;
  cursor: pointer;
  background: var(--paper);
  border: 1.5px solid var(--rule);
  padding: clamp(12px, 2.6vh, 24px) 18px;
  justify-content: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--ink);
  text-decoration: none;
  text-align: left;
  transition: border-color .15s, background-color .15s, transform .15s
}

/* Icon in getöntem, eckigem Kästchen */
.goal svg {
  box-sizing: border-box;
  width: 44px;
  height: 44px;
  padding: 9px;
  color: var(--blue);
  background: var(--blue-tint);
  margin-bottom: clamp(4px, 1.2vh, 10px);
  transition: background-color .2s ease, color .2s ease
}

.panel .goal:hover svg,
.panel .goal:focus-visible svg {
  color: var(--paper);
  background: var(--blue)
}

.goal b {
  font-size: 17px;
  line-height: 1.2
}

.goal small {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.3;
  white-space: nowrap
}

/* Kacheln sind Links in den Funnel: deutlicher Hover mit Pfeil */
.panel .goal::after {
  content: "→";
  position: absolute;
  top: 14px;
  right: 16px;
  font-size: 20px;
  font-weight: 700;
  color: var(--blue);
  opacity: 0;
  transform: translateX(-6px);
  transition: opacity .15s, transform .15s
}

.panel .goal:hover,
.panel .goal:focus-visible {
  border-color: var(--blue);
  background-color: var(--blue-soft);
  transform: translateY(-2px);
  outline: none
}

.panel .goal:hover b,
.panel .goal:focus-visible b {
  color: var(--blue)
}

.panel .goal:hover::after,
.panel .goal:focus-visible::after {
  opacity: 1;
  transform: none
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: var(--accent);
  color: var(--paper);
  text-decoration: none;
  font-weight: 800;
  font-size: 21px;
  padding: 20px 56px;
  transition: background .2s
}

.btn:hover {
  background: var(--accent-dark)
}


.btn svg {
  width: 22px;
  height: 22px;
  transition: transform .2s
}

.btn:hover svg {
  transform: translateX(4px)
}

.cta-row {
  display: flex;
  align-items: center;
  gap: 24px
}

.checks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 4px;
  font-size: 14px;
  font-weight: 700;
  color: var(--muted)
}

.checks li {
  display: flex;
  align-items: center;
  gap: 7px
}

.checks svg {
  width: 15px;
  height: 15px;
  color: var(--blue)
}

/* Unterhalb: Problem, Big Picture, wer dahinter steht, zweiter Aufruf */
/* Abschnitte wechseln zwischen Sand (var(--bg)) und Weiß (.alt) */
section {
  padding-block: clamp(56px, 9vh, 96px)
}

section.alt {
  background: var(--paper)
}

section.alt .facts li {
  background: var(--bg)
}

.section-cta {
  margin-top: 40px
}

.btn--md {
  font-size: 18px;
  padding: 16px 32px
}

.faq-grid {
  display: grid;
  grid-template-columns: minmax(0, 9fr) minmax(0, 15fr);
  gap: 56px;
  align-items: start
}

.faq-grid .section-cta {
  margin-top: 28px
}

.faq-list {
  display: grid;
  gap: 10px
}

.faq-list details {
  background: var(--paper)
}

.faq-list summary {
  list-style: none;
  cursor: pointer;
  padding: 20px 56px 20px 24px;
  font-weight: 700;
  font-size: 18px;
  position: relative;
  text-wrap: balance
}

.faq-list summary::-webkit-details-marker {
  display: none
}

.faq-list summary::after {
  content: "+";
  position: absolute;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 24px;
  font-weight: 400;
  color: var(--blue)
}

.faq-list details[open] summary::after {
  content: "–"
}

.faq-list summary:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px
}

.faq-list details p {
  margin: 0;
  padding: 0 24px 22px;
  color: var(--muted);
  font-size: 16px;
  text-wrap: pretty
}

.kicker {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 12px
}

h2 {
  font-size: clamp(28px, 3.4vw, 42px);
  line-height: 1.1;
  letter-spacing: -.025em;
  font-weight: 800;
  margin: 0 0 16px;
  max-width: 20em
}

.text {
  font-size: 18px;
  color: var(--muted);
  max-width: 40em;
  margin: 0
}

.path {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 40px
}

.path div {
  background: var(--paper);
  padding: 24px;
  border-top: 4px solid var(--rule)
}

/* Zweispaltige Abschnitte: Text mit Knopf und Kacheln, im Wechsel links/rechts.
   .flip tauscht die Seiten auf breiten Bildschirmen; auf dem Handy steht der Text immer zuerst. */
.how {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 56px;
  align-items: center
}

.how .section-cta {
  margin-top: 32px
}

.how .path {
  grid-template-columns: 1fr;
  margin-top: 0
}

.how .compare {
  grid-template-columns: 1fr;
  margin-top: 0
}

@media (min-width:901px) {
  /* Text unter der Headline: Zeilen fest wie im HTML (eine Zeile pro span) */
  .lead {
    max-width: none
  }

  .lead>span {
    display: block;
    white-space: nowrap
  }

  .flip > :first-child {
    order: 2
  }
}

.how .path div {
  border-top: 0;
  border-left: 4px solid var(--rule)
}

.how .path div.now {
  border-left-color: var(--accent)
}

.path div.now {
  border-top-color: var(--accent)
}

.path small {
  display: block;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px
}

.path .now small {
  color: var(--accent)
}

.path b {
  display: block;
  font-size: 19px;
  margin-bottom: 6px
}

.path p {
  margin: 0;
  color: var(--muted);
  font-size: 15px
}

.compare {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 10px;
  margin-top: 40px
}

.col {
  padding: 28px
}

.col--other {
  /* ganze Pixel, sonst zeichnet Safari auf dem iPhone die seitlichen Striche nicht */
  border: 2px dashed var(--rule)
}

.col--us {
  background: var(--blue);
  color: var(--paper)
}

.col h3 {
  font-size: 19px;
  margin: 0 0 18px
}

.col--other h3 {
  color: var(--muted)
}

.col ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 14px
}

.col li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  font-size: 17px
}

.col--other li {
  color: var(--muted)
}

.col li svg {
  width: 20px;
  height: 20px;
  flex: none;
  margin-top: 3px
}

.about {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 56px;
  align-items: center
}

.facts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 10px
}

.facts li {
  background: var(--paper);
  padding: 18px 20px;
  font-size: 16px
}

.facts b {
  display: block;
  font-size: 17px;
  margin-bottom: 2px
}

.facts span {
  color: var(--muted)
}


.final {
  background: var(--blue);
  color: var(--paper);
  border: 0
}

.final .wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 40px
}

.final h2 {
  color: var(--paper);
  margin: 0 0 12px
}

.final .text {
  color: rgba(255, 255, 255, .8)
}

.final .btn {
  flex: none
}

footer {
  font-size: 13px;
  color: var(--muted);
  background: var(--paper)
}

footer .wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
  padding-block: 18px;
  justify-content: space-between;
  align-items: center
}

footer nav {
  display: flex;
  gap: 18px
}

footer a {
  color: inherit;
  text-decoration: none
}

@media (max-width:900px) {
  .hero-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 24px
  }


  .final .wrap {
    flex-direction: column;
    align-items: flex-start
  }

  .path,
  .compare,
  .faq-grid,
  .how {
    grid-template-columns: 1fr
  }

  .faq-grid {
    gap: 28px
  }

  .about {
    grid-template-columns: 1fr;
    gap: 28px
  }
}

@media (max-width:600px) {
  :root {
    --header: 54px
  }

  .wrap {
    padding-left: max(16px, env(safe-area-inset-left, 0px));
    padding-right: max(16px, env(safe-area-inset-right, 0px))
  }

  .head-note {
    display: none
  }

  /* Erster Bildschirm: mittig, Reihenfolge Überschrift, Text, Kacheln, Knopf */
  .hero {
    padding-block: 24px
  }

  .hero-text {
    display: contents
  }

  .hero-grid {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 0
  }

  .hero-text .eyebrow,
  .hero h1 {
    align-self: flex-start
  }

  /* "Oder direkt starten" passt nicht, wenn die Kacheln vor dem Knopf stehen */
  .panel .eyebrow {
    display: none
  }

  .hero-text .eyebrow {
    order: 1
  }

  .hero h1 {
    order: 2
  }

  .lead {
    order: 3;
    margin-bottom: 24px
  }

  .panel {
    order: 4
  }

  .cta-row {
    order: 5;
    margin-top: 24px
  }

  .eyebrow {
    margin-bottom: 10px
  }

  h1 {
    font-size: clamp(26px, 7.6vw, 36px);
    margin-bottom: 12px
  }

  .lead {
    font-size: 16px;
    text-wrap: pretty
  }

  .panel {
    padding: 0;
    background: none
  }

  .ask {
    font-size: 15px;
    margin-bottom: 10px
  }

  /* Kacheln: Icon links, Titel und Unterzeile daneben (Unterzeile nie ausblenden) */
  .goal {
    padding: 10px 12px;
    display: grid;
    grid-template-columns: 34px 1fr;
    column-gap: 10px;
    row-gap: 2px;
    align-items: center;
    align-content: center
  }

  .goal svg {
    grid-row: span 2;
    width: 34px;
    height: 34px;
    padding: 7px;
    margin: 0;
    flex: none
  }

  .goal b {
    font-size: 15px;
    white-space: nowrap
  }

  /* Unterzeile immer zweizeilig, eine Zeile pro span */
  .goal small {
    display: block;
    font-size: 12.5px
  }

  .goal small span {
    display: block
  }

  .panel .goal::after {
    top: 50%;
    right: 12px;
    font-size: 16px;
    transform: translateY(-50%)
  }

  .logo {
    font-size: 17px
  }

  /* Knöpfe: volle Breite, eine Zeile, nicht zu wuchtig */
  .btn {
    width: 100%;
    justify-content: center;
    padding: 16px;
    font-size: 18px;
    white-space: nowrap
  }

  .btn--md {
    font-size: 16px;
    padding: 14px 16px
  }

  .btn svg {
    width: 18px;
    height: 18px
  }

  .section-cta,
  .how .section-cta {
    margin-top: 28px
  }

  .cta-row {
    flex-direction: column;
    align-items: stretch;
    gap: 14px
  }

  /* Häkchen als Leiste mit drei Spalten unter dem Knopf */
  .checks {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    font-size: 13px;
    line-height: 1.25;
    text-align: center
  }

  .checks li {
    flex-direction: column;
    gap: 4px;
    text-wrap: balance
  }


  .text {
    font-size: 16px
  }
}

@media (prefers-reduced-motion:reduce) {
  * {
    transition: none !important;
    animation: none !important
  }
}

/* Emojis: sparsam eingesetzt, nie kursiv oder rot eingefärbt */
.emo {
  font-style: normal;
  font-weight: 400;
  white-space: nowrap;
}

h1 .emo {
  font-size: .82em;
}

</style>
</head>
<body>
<!-- Hausbau-Konfigurator Landingpage: Seiteninhalt
     In OnePage: in das Feld für Code im Body einfügen. -->
<header>
  <div class="wrap">
    <a class="logo" href="/" aria-label="Hausbau-Konfigurator">
      <span>Hausbau-<b>Konfigurator</b></span>
    </a>
    <span class="head-note">Kostenlos und unverbindlich</span>
  </div>
</header>

<main>
  <div class="hero">
    <div class="wrap hero-grid">
      <div class="hero-text">
        <span class="eyebrow">Für alle, die ein Haus bauen möchten</span>
        <h1><span>Ihr Haus mit Grundriss,</span> <span>Außenansicht und</span> <span><em>Preisschätzung.</em></span></h1>
        <p class="lead"><span>Sie möchten bauen, wissen aber noch nicht, welches Haus</span> <span>passt und was es heute realistisch kostet? Ein paar</span> <span>Fragen genügen für eine erste Hausnummer. <i class="emo" aria-hidden="true">😉</i></span></p>

        <div class="cta-row">
          <a class="btn" id="cta" href="#" data-start>
            Los geht's
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"
              stroke-linejoin="round" aria-hidden="true">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </a>
          <ul class="checks">
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"
                stroke-linejoin="round">
                <path d="M5 12.5l4.5 4.5L19 7.5" />
              </svg>6 kurze Fragen</li>
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"
                stroke-linejoin="round">
                <path d="M5 12.5l4.5 4.5L19 7.5" />
              </svg>Unverbindlich</li>
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"
                stroke-linejoin="round">
                <path d="M5 12.5l4.5 4.5L19 7.5" />
              </svg>Kostenlos</li>
          </ul>
        </div>
      </div>

      <div class="panel">
        <span class="eyebrow">Oder direkt starten</span>
        <p class="ask">Was ist Ihnen beim Bauen am wichtigsten?</p>
        <!-- Icons: Lucide 0.460.0 (lucide.dev), Lizenz ISC -->
        <div class="goals" role="group" aria-label="Was ist Ihnen beim Bauen am wichtigsten?">
          <a class="goal" href="#" data-start="familie">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
            <b>Familie</b><small><span>Sicherheit</span> <span>und Garten</span></small>
          </a>
          <a class="goal" href="#" data-start="design">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 7 8.7 2.7a2.41 2.41 0 0 0-3.4 0L2.7 5.3a2.41 2.41 0 0 0 0 3.4L7 13" /><path d="m8 6 2-2" /><path d="m18 16 2-2" /><path d="m17 11 4.3 4.3c.94.94.94 2.46 0 3.4l-2.6 2.6c-.94.94-2.46.94-3.4 0L11 17" /><path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" /><path d="m15 5 4 4" /></svg>
            <b>Design</b><small><span>Exklusiv</span> <span>und smart</span></small>
          </a>
          <a class="goal" href="#" data-start="kosten">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5c-1.5 0-2.8 1.4-3 2-3.5-1.5-11-.3-11 5 0 1.8 0 3 2 4.5V20h4v-2h3v2h4v-4c1-.5 1.7-1 2-2h2v-4h-2c0-1-.5-1.5-1-2V5z" /><path d="M2 9v1c0 1.1.9 2 2 2h1" /><path d="M16 11h.01" /></svg>
            <b>Budget</b><small><span>Kosten und</span> <span>Förderung</span></small>
          </a>
          <a class="goal" href="#" data-start="komfort">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8" /><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /></svg>
            <b>Komfort</b><small><span>Barrierefrei</span> <span>wohnen</span></small>
          </a>
        </div>
      </div>
    </div>
  </div>


  <!-- Warum wir: positive Abgrenzung zu klassischen Portalen, ohne Namen und ohne Anti-Verkauf -->
  <section class="alt">
    <div class="wrap how flip">
      <div class="how-intro">
        <p class="kicker">Warum Hausbau-Konfigurator</p>
        <h2>Erst sehen Sie Ihr Haus. Dann planen wir gemeinsam den nächsten Schritt.</h2>
        <p class="text">Wer sich heute über ein Hausbau-Portal informiert, bekommt oft Prospekte statt Antworten.
          Wir machen es umgekehrt: Sie sehen zuerst, was für Sie möglich ist.</p>
        <div class="section-cta">
          <a class="btn btn--md" href="#" data-start>Jetzt Hausvorschlag erhalten <svg viewBox="0 0 24 24"
            fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"
            aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg></a>
        </div>
      </div>
      <div class="compare">
        <div class="col col--other">
          <h3>Bei vielen Hausbau-Portalen</h3>
          <ul>
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
                <path d="M6 6l12 12M18 6L6 18" />
              </svg><span>Sie fordern Kataloge an und haben danach immer noch keine Vorstellung von Ihrem Haus.</span>
            </li>
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
                <path d="M6 6l12 12M18 6L6 18" />
              </svg><span>Oft lange Formulare, bevor Sie überhaupt etwas von Ihrem Haus zu sehen bekommen.</span></li>
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
                <path d="M6 6l12 12M18 6L6 18" />
              </svg><span>Am Ende haben Sie viele Prospekte in der Hand, aber immer noch keinen Preis.</span></li>
          </ul>
        </div>
        <div class="col col--us">
          <h3>Bei uns</h3>
          <ul>
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"
                stroke-linejoin="round">
                <path d="M5 12.5l4.5 4.5L19 7.5" />
              </svg><span>Sechs kurze Fragen, danach erhalten Sie Grundriss, Außenansicht und ungefähren Preis.</span></li>
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"
                stroke-linejoin="round">
                <path d="M5 12.5l4.5 4.5L19 7.5" />
              </svg><span>Ein Ansprechpartner aus unserem eigenen Team bespricht Ihren Vorschlag persönlich mit
                Ihnen.</span></li>
            <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"
                stroke-linejoin="round">
                <path d="M5 12.5l4.5 4.5L19 7.5" />
              </svg><span>Wir bringen Sie mit Baupartnern zusammen, die zu Ihren Wünschen und Ihrem Budget
                passen.</span></li>
          </ul>
        </div>
      </div>
    </div>
  </section>

  <!-- Problem + Big Picture: der Vorschlag ist der erste Schritt, nicht das ganze Projekt -->
  <section>
    <div class="wrap how">
      <div class="how-intro">
      <p class="kicker">So funktioniert's</p>
      <h2>Bauen wird teurer.</h2>
      <p class="text">Höhere Zinsen und gestiegene Baukosten: Viele zögern, weil sie nicht wissen, was für sie
        realistisch ist. Wir fragen nur, was für Ihren Grundriss wirklich nötig ist, und
        zeigen Ihnen ein Haus, das Sie sehen und einschätzen können, bevor Sie mit einem Anbieter sprechen.</p>
      <div class="section-cta">
        <a class="btn btn--md" href="#" data-start>Mit Schritt 1 starten <svg viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"
            aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg></a>
      </div>
      </div>
      <div class="path">
        <div class="now">
          <small>Heute, in etwa einer Minute</small>
          <b>Ihr Hausvorschlag <i class="emo" aria-hidden="true">✨</i></b>
          <p>Grundriss, Außenansicht und ein ungefährer Preis. Eine klare Orientierung, mit der Sie weiterplanen
            können.</p>
        </div>
        <div>
          <small>Danach</small>
          <b>Persönliche Beratung <i class="emo" aria-hidden="true">🤝</i></b>
          <p>Finanzierung, Fördermittel, Grundstück und Ausstattung: Was ein Vorschlag nicht klären kann, besprechen
            Sie mit einem passenden Baupartner.</p>
        </div>
        <div>
          <small>Am Ende</small>
          <b>Ihr Haus <i class="emo" aria-hidden="true">🏡</i></b>
          <p>Gebaut nach Ihren Wünschen und geplant mit Zahlen, die zu Ihnen passen.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Experte: wer steckt dahinter, drei Gründe -->
  <section class="alt">
    <div class="wrap about flip">
      <div>
        <p class="kicker">Wer dahinter steht</p>
        <h2>Erfahrung aus vielen Jahren Hausbau.</h2>
        <p class="text">Hinter Hausbau-Konfigurator steht ein Team mit langjähriger Erfahrung im Hausbau: aus der
          Beratung von Bauherren und der Zusammenarbeit mit Bauunternehmen. Dieses Wissen steckt in jeder Frage und
          in jedem Vorschlag.</p>
        <div class="section-cta">
          <a class="btn btn--md" href="#" data-start>Mein Haus entwerfen <svg viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg></a>
        </div>
      </div>
      <ul class="facts">
        <li><b>Über 30 Jahre Hausbau-Erfahrung im Team</b><span>Aus der täglichen Arbeit mit Bauherren und
            Bauunternehmen. Wir wissen, welche Fragen am Anfang wirklich zählen.</span></li>
        <li><b>Gemacht für den Anfang</b><span>Sie brauchen weder Grundstück noch Fachwissen, nur eine Vorstellung
            davon, wie Sie wohnen möchten.</span></li>
        <li><b>Sorgfältig mit Ihren Daten</b><span>Wir geben Ihre Anfrage nur an passende Baupartner weiter und nur
            mit Ihrer Einwilligung.</span></li>
      </ul>
    </div>
  </section>

  <!-- Häufige Fragen: Einwände vorwegnehmen -->
  <section>
    <div class="wrap faq-grid">
      <div>
        <p class="kicker">Häufige Fragen</p>
        <h2>Gut zu wissen, bevor Sie starten.</h2>
        <p class="text">Die wichtigsten Antworten auf einen Blick.</p>
        <div class="section-cta">
          <a class="btn btn--md" href="#" data-start>Los geht's <svg viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"
              aria-hidden="true">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg></a>
        </div>
      </div>
      <div class="faq-list">
        <details name="faq" open>
          <summary>Was kostet mich das?</summary>
          <p>Nichts. Ihr Vorschlag mit Grundriss, Außenansicht und ungefährem Preis ist kostenlos und unverbindlich.
          </p>
        </details>
        <details name="faq">
          <summary>Wie genau ist der Preis?</summary>
          <p>Eine erste Hausnummer, aber eine realistische: Die Preisschätzung basiert auf Ihren Angaben und ist unverbindlich, also kein Angebot und kein Festpreis. Den genauen Preis ermittelt
            später ein Baupartner, wenn Grundstück, Ausstattung und Details feststehen.</p>
        </details>
        <details name="faq">
          <summary>Brauche ich schon ein Grundstück?</summary>
          <p>Nein. Viele starten ohne Grundstück. Ihr Vorschlag hilft Ihnen auch dabei, einzuschätzen, was Sie suchen.
          </p>
        </details>
        <details name="faq">
          <summary>Was wird abgefragt?</summary>
          <p>Nur das, was für Ihren Grundriss nötig ist, zum Beispiel Budget, Haustyp und Stil. Fachwissen brauchen
            Sie dafür nicht.</p>
        </details>
        <details name="faq">
          <summary>Wer meldet sich bei mir?</summary>
          <p>Ein Ansprechpartner aus unserem Team ruft Sie an, bespricht Ihren Vorschlag und klärt offene Fragen.</p>
        </details>
        <details name="faq">
          <summary>Was passiert mit meinen Daten?</summary>
          <p>Wir nutzen Ihre Angaben, um Ihren Vorschlag zu erstellen und Sie zu beraten. An passende Baupartner geben
            wir sie nur mit Ihrer Einwilligung weiter.</p>
        </details>
      </div>
    </div>
  </section>

  <section class="final">
    <div class="wrap">
      <div>
        <h2>Wie wird Ihr Zuhause aussehen?</h2>
        <p class="text">Finden Sie es heraus. Ihr Entwurf ist nur ein paar Fragen entfernt.</p>
      </div>
      <a class="btn" href="#" data-start>
        Los geht's
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"
          stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      </a>
    </div>
  </section>
</main>

<footer>
  <div class="wrap">
    <span>© 2026 hausbau-konfigurator.de</span>
    <nav><a href="#">Impressum</a><a href="#">Datenschutz</a></nav>
  </div>
</footer>

</body>
</html>
B2T_LANDINGPAGE;
	exit;
}, 20 );
