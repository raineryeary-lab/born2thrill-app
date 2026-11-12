/* Hausbau-Konfigurator als Video-Strecke.
 * Fragen und Logik nach dem Fragebogen-PDF (REGELN 37), Szenen aus
 * ../szenen.json (plans/fragebogen-videos-v1.md). Jede Frage ist ein kurzer
 * Clip; am Ende bleibt das letzte Bild stehen und die Antworten erscheinen.
 * Eine Antwort spielt, wenn vorhanden, ihre eigene kurze Szene ab.
 * Laeuft ohne Server: haeuser.json und clips/ liegen neben dieser Datei.
 * Kontaktdaten gehen an window.HK_KONTAKT_SENDEN(daten), falls die
 * einbettende Seite das setzt; sonst bleiben sie im Browser. */
(function () {
  "use strict";

  var CLIPS = window.HK_CLIPS || "clips/";
  var STANDBILD = window.HK_STANDBILD || "familie-figuren.png";

  // (Budget, Hausart) -> Zimmerstufen; die letzte heisst "n+" wie in
  // konfigurator-matrix.py, damit die Feldnamen in haeuser.json passen.
  var ZIMMER = { efh: [4, 5], dhh: [4, 5], bungalow: [3, 4, 5], zfh: [3, 4, 5] };

  var SCHRITTE = [
    { id: "start", clip: "00-start", frage: "Ihr Haus mit Grundriss, Außenansicht und Preis",
      hinweis: "100 % kostenlos und unverbindlich",
      antworten: [{ wert: "los", text: "Jetzt Haus konfigurieren", haupt: true }] },
    { id: "grundstueck", clip: "01-grundstueck", frage: "Hast du bereits ein Grundstück?",
      antworten: [{ wert: "ja", text: "Ja", clip: "01a-ja" },
                  { wert: "in_aussicht", text: "In Aussicht", clip: "01b-in-aussicht" },
                  { wert: "nein", text: "Nein", clip: "01c-nein" }] },
    { id: "grundstueck_details", clip: null, formular: "grundstueck" },
    { id: "budget", clip: "02-budget", frage: "Wie viel möchtest du für dein Haus investieren?",
      hinweis: "Alle Angaben verstehen sich zuzüglich Grundstücks- und Baunebenkosten.",
      // Die Budget-Clips schliessen aneinander an: Motten -> Sohn -> Buggy.
      antworten: [{ wert: "b450", text: "300.000 – 450.000 €", clip: ["02a-budget-klein"] },
                  { wert: "b600", text: "450.000 – 600.000 €", clip: ["02a-budget-klein", "02b-budget-mittel"] },
                  { wert: "b600p", text: "Mehr als 600.000 €",
                    clip: ["02a-budget-klein", "02b-budget-mittel", "02c-budget-gross"] }] },
    { id: "hausart", clip: "03-hausart", frage: "Was möchtest du bauen?",
      antworten: [{ wert: "efh", text: "Einfamilienhaus", clip: "03a-efh" },
                  { wert: "bungalow", text: "Bungalow", clip: "03b-bungalow" },
                  { wert: "dhh", text: "Doppelhaus / Doppelhaushälfte", clip: "03c-dhh" },
                  { wert: "zfh", text: "Zweifamilienhaus", clip: "03d-zfh" }] },
    { id: "baustil", clip: "04-baustil", frage: "Welcher Baustil spricht dich am meisten an?",
      antworten: [{ wert: "klassisch", text: "Klassisch" }, { wert: "modern", text: "Modern" }] },
    { id: "dachform", clip: "05-dachform", frage: "Welcher Look gefällt dir am besten?",
      antworten: [{ wert: "satteldach", text: "Satteldach" }, { wert: "walmdach", text: "Walmdach" },
                  { wert: "pultdach", text: "Pultdach" }, { wert: "flachdach", text: "Flachdach" }] },
    { id: "zimmer", clip: "06-zimmer", frage: "Wie viel Platz soll dein neues Zuhause bieten?",
      hinweis: "Die Zimmeranzahl versteht sich zusätzlich zu Küche und Bad.",
      antworten: function (a) {
        return ZIMMER[a.hausart || "efh"].map(function (n) {
          return { wert: n, text: n + " Zimmer", clip: "06" + "abc"[n - 3] + "-zimmer-" + n };
        });
      } },
    { id: "gaeste_wc", clip: "07-gaeste-wc", frage: "Möchtest du eine zusätzliche Dusche in deinem Gäste-WC?",
      antworten: [{ wert: true, text: "Ja" }, { wert: false, text: "Nein" }] },
    { id: "kontakt", clip: "08-kontakt", formular: "kontakt" },
    { id: "ergebnis", clip: "09-ergebnis", ergebnis: true }
  ];

  var el = function (id) { return document.getElementById(id); };
  var video = el("hk-video"), bild = el("hk-standbild"), kasten = el("hk-frage");
  var antworten = {}, verlauf = [], haeuser = [], schritt = 0, abspielNr = 0;

  var ziel = new URLSearchParams(location.search).get("ziel");
  if (ziel) antworten.ziel = ziel;   // Vorauswahl von der Landingpage

  fetch("haeuser.json").then(function (r) { return r.json(); })
    .then(function (d) { haeuser = d; }).catch(function () { haeuser = []; });

  el("hk-ton").addEventListener("click", function () {
    video.muted = !video.muted;
    this.textContent = video.muted ? "Ton an" : "Ton aus";
  });
  el("hk-zurueck").addEventListener("click", zurueck);

  // Spielt einen Clip und ruft danach fertig() -- auch wenn der Clip fehlt
  // oder nicht abspielt: dann steht das Figurenblatt als Standbild da.
  function spiele(name, fertig) {
    if (Array.isArray(name)) {   // mehrere Clips nahtlos hintereinander
      var rest = name.slice(1);
      return spiele(name[0], rest.length ? function () { spiele(rest, fertig); } : fertig);
    }
    var nr = ++abspielNr;
    kasten.hidden = true;
    var weiter = function () { if (nr === abspielNr) fertig(); };
    if (!name) { weiter(); return; }
    bild.hidden = true; video.hidden = false;
    video.onended = weiter;
    video.onerror = function () {
      video.hidden = true; bild.src = STANDBILD; bild.hidden = false; weiter();
    };
    video.src = CLIPS + name + ".mp4";
    var p = video.play();
    if (p && p.catch) p.catch(function () { video.onerror(); });
  }

  function zeigeSchritt(i, ohneClip) {
    schritt = i;
    var s = SCHRITTE[i];
    el("hk-balken").style.width = Math.round(100 * i / (SCHRITTE.length - 1)) + "%";
    el("hk-zurueck").hidden = verlauf.length === 0;
    spiele(ohneClip ? null : s.clip, function () { baueKasten(s); });
  }

  function baueKasten(s) {
    var box = el("hk-antworten");
    box.innerHTML = "";
    kasten.classList.toggle("hk-voll", !!(s.formular || s.ergebnis));
    el("hk-hinweis").textContent = s.hinweis || "";
    if (s.formular === "grundstueck") return formularGrundstueck(box);
    if (s.formular === "kontakt") return formularKontakt(box);
    if (s.ergebnis) return zeigeErgebnis(box);
    el("hk-fragetext").textContent = s.frage;
    var liste = typeof s.antworten === "function" ? s.antworten(antworten) : s.antworten;
    liste.forEach(function (a) {
      var b = document.createElement("button");
      b.type = "button"; b.textContent = a.text;
      if (a.haupt) b.className = "hk-haupt";
      b.addEventListener("click", function () { waehle(s, a); });
      box.appendChild(b);
    });
    kasten.hidden = false;
    var erster = box.querySelector("button, input");
    if (erster) erster.focus({ preventScroll: true });
  }

  function waehle(s, a) {
    verlauf.push({ schritt: schritt, antworten: JSON.parse(JSON.stringify(antworten)) });
    if (s.id !== "start") antworten[s.id] = a.wert;
    if (s.id === "hausart") delete antworten.zimmer;   // Zimmerstufen haengen an der Hausart
    spiele(a.clip, function () { zeigeSchritt(schritt + 1); });
  }

  function zurueck() {
    var v = verlauf.pop();
    if (!v) return;
    antworten = v.antworten;
    zeigeSchritt(v.schritt, true);
  }

  function feld(name, beschriftung, typ, wert, ganz) {
    var l = document.createElement("label");
    if (ganz) l.className = "hk-ganz";
    l.textContent = beschriftung;
    var i = document.createElement("input");
    i.name = name; i.type = typ || "text"; i.value = wert || "";
    l.appendChild(i);
    return l;
  }

  function formular(box, titel, felder, knopf, pruefe, weiter) {
    el("hk-fragetext").textContent = titel;
    var f = document.createElement("form");
    f.className = "hk-formular"; f.noValidate = true;
    felder.forEach(function (x) { f.appendChild(x); });
    var fehler = document.createElement("p"); fehler.className = "hk-fehler hk-ganz";
    var b = document.createElement("button"); b.type = "submit"; b.className = "hk-haupt hk-ganz"; b.textContent = knopf;
    f.appendChild(fehler); f.appendChild(b);
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var d = {};
      new FormData(f).forEach(function (v, k) { d[k] = String(v).trim(); });
      var msg = pruefe(d);
      if (msg) { fehler.textContent = msg; return; }
      verlauf.push({ schritt: schritt, antworten: JSON.parse(JSON.stringify(antworten)) });
      weiter(d);
    });
    box.appendChild(f);
    kasten.hidden = false;
    f.querySelector("input").focus({ preventScroll: true });
  }

  function formularGrundstueck(box) {
    var hat = antworten.grundstueck !== "nein";
    var g = antworten.grundstueck_details || {};
    formular(box, hat ? "Wo liegt dein Grundstück?" : "Wo suchst du ein Grundstück?", [
      feld("ort", hat ? "Ort / PLZ: Wo befindet sich dein Grundstück?" : "Ort / PLZ: Wo suchst du ein Grundstück?", "text", g.ort, true),
      feld("groesse", hat ? "Wie groß ist dein Grundstück? (m²)" : "Wie groß soll dein Grundstück sein? (m²)", "text", g.groesse, true)
    ], "Weiter", function (d) {
      return d.ort ? "" : "Bitte Ort oder PLZ angeben.";
    }, function (d) {
      antworten.grundstueck_details = d;
      zeigeSchritt(schritt + 1);
    });
  }

  function formularKontakt(box) {
    var k = antworten.kontakt || {};
    formular(box, "Wohin dürfen wir dein Ergebnis schicken?", [
      feld("vorname", "Vorname", "text", k.vorname),
      feld("nachname", "Nachname", "text", k.nachname),
      feld("handy", "Handynummer", "tel", k.handy),
      feld("email", "E-Mail-Adresse", "email", k.email)
    ], "Mein Ergebnis anzeigen", function (d) {
      if (!d.vorname || !d.nachname) return "Bitte Vor- und Nachnamen angeben.";
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)) return "Bitte eine gültige E-Mail-Adresse angeben.";
      if (d.handy.replace(/\D/g, "").length < 6) return "Bitte eine Handynummer angeben.";
      return "";
    }, function (d) {
      antworten.kontakt = d;
      if (typeof window.HK_KONTAKT_SENDEN === "function") {
        try { window.HK_KONTAKT_SENDEN(JSON.parse(JSON.stringify(antworten))); } catch (e) { /* Ergebnis trotzdem zeigen */ }
      }
      zeigeSchritt(schritt + 1);
    });
  }

  function stufenName(n, stufen) {
    return n === stufen[stufen.length - 1] ? n + "+" : String(n);
  }

  // Das passende fertige Haus: gleiches Feld (Budget-Hausart-Zimmer), ein
  // Dusch-WC wie gewuenscht zuerst; sonst dieselbe Hausart im Preis am
  // naechsten an der Budgetmitte.
  function passendesHaus(a) {
    var stufen = ZIMMER[a.hausart];
    var name = a.budget + "-" + a.hausart + "-" + stufenName(a.zimmer, stufen);
    var im = haeuser.filter(function (h) { return h.feld === name; });
    if (im.length) {
      im.sort(function (x, y) { return (y.dusch_wc === a.gaeste_wc) - (x.dusch_wc === a.gaeste_wc); });
      return { haus: im[0], genau: true };
    }
    var mitte = { b450: 375000, b600: 525000, b600p: 700000 }[a.budget];
    var art = haeuser.filter(function (h) { return h.typ === a.hausart; });
    art.sort(function (x, y) { return Math.abs(x.preis - mitte) - Math.abs(y.preis - mitte); });
    return art.length ? { haus: art[0], genau: false } : null;
  }

  function euro(n) {
    return (Math.round(n / 5000) * 5000).toLocaleString("de-DE") + " €";
  }

  function zeigeErgebnis(box) {
    var t = passendesHaus(antworten);
    el("hk-fragetext").textContent = "Dein Hausvorschlag, " + ((antworten.kontakt || {}).vorname || "") ;
    var e = document.createElement("div");
    e.className = "hk-ergebnis";
    if (!t) {
      e.innerHTML = '<div class="hk-karte">Für diese Kombination erstellen wir deinen Grundriss persönlich. ' +
        'Wir melden uns in Kürze bei dir.</div>';
    } else {
      var h = t.haus;
      e.innerHTML =
        '<div class="hk-preis">ca. ' + euro(h.preis) + "</div>" +
        '<div class="hk-hinweis">zuzüglich Grundstücks- und Baunebenkosten</div>' +
        '<div class="hk-karte"><strong>Grundriss:</strong> ' + h.qm + " m² Wohnfläche" +
        (t.genau ? "" : " (nächstliegender Vorschlag)") + "<br><small>" + h.plan + "</small></div>" +
        '<div class="hk-karte"><strong>Außenansicht:</strong> ' + antworten.baustil + ", " + antworten.dachform +
        "<br><small>Bilder folgen aus dem Katalog.</small></div>";
    }
    box.appendChild(e);
    kasten.hidden = false;
  }

  zeigeSchritt(0);
})();
