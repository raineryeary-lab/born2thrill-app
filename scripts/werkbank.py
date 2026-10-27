#!/usr/bin/env python3
"""Die Werkbank: ein Haus vor dir, Knoepfe daneben, weiter zum naechsten.

    python werkbank.py
    -> http://localhost:8800

Kein Batch, kein Log. Du siehst das Haus -- die gezeichneten Raeume und, wenn
es gebaut ist, die Renderings -- daneben steht, woran es haengt, und darunter
sind die Knoepfe, die genau diesen Schritt machen. Ein Haus erledigt, weiter
zum naechsten.

Was der Knopf tut, tut er hier im Vordergrund und schreibt das Ergebnis auf die
Seite. Freigeben bleibt bewusst ein eigener Knopf mit Begruendungsfeld -- das
ist eine Rechteerklaerung, keine Routine.
"""

import http.server
import json
import mimetypes
import os
import socketserver
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
# Eine Wahrheit fuer Dachform und Massstab (siehe scripts/hausdaten.py).
import hausdaten  # noqa: E402

SUITE = os.path.dirname(os.path.dirname(HERE))
PROJECTS = os.path.join(SUITE, "floorplan-simplifier", "projects")
# Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein Skript,
# das ohne gesetzte Variable still auf den alten C:-Nachbarordner
# zurueckfiele, wuerde unbemerkt gegen veraltete Daten arbeiten -- exakt
# der root-merge-Fehler vom 18.08., nur seitenverkehrt. Gleiches Muster wie
# build-simplifier-render-plan.py.workbench_data_root().
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
            "den Datenordner zu erraten. Siehe .env.local.")
DATA = os.path.abspath(_konfiguriert)
LEDGER = os.path.join(SUITE, "born2thrill-local-workbench", "data",
                      "simplifier-v2", "corpus-ledger.json")
PORT = 8800
PY = sys.executable
RASTER = (".png", ".jpg", ".jpeg", ".pdf")


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return default


def renders(name):
    d = os.path.join(DATA, "corrections", name, "renders", "go-baseline")
    if not os.path.isdir(d):
        return []
    return sorted(x for x in os.listdir(d)
                  if x.endswith(".png")
                  and not any(x.lower().endswith(s + ".png")
                              for s in ("-depth", "-edge", "-mask")))


def stufen(name):
    """Die Hausakte: jede Stufe der Kette mit ihrem Stand.

    Rainer, 2026-08-20: "walls windows doors stairs floors environment furniture
    rooftypes blender models render all floorplans renderall extoiereiors" --
    das sind die Stufen, die er sehen will. Sie werden nicht geraten, sondern
    aus dem gebauten Plan und den Artefakten gezaehlt.
    """
    d = os.path.join(DATA, "corrections", name, "renders", "go-baseline")
    plan = read_json(os.path.join(d, "plan-modern.json"))
    classic = read_json(os.path.join(d, "plan-classic.json"))
    folder = os.path.join(PROJECTS, name)
    a = read_json(os.path.join(folder, "annotations.json")) or {}
    # Massstab und Dachform stehen je nach Haus in der Annotation ODER im
    # Sidecar. Zusammengefuehrt wird das nur an einer Stelle, mit derselben
    # Vorrangregel wie der Bau: scripts/hausdaten.py.
    daten = hausdaten.hausdaten(folder)
    fur = os.path.join(DATA, "corrections", name, "furniture")
    moebel_datei = sum(len((read_json(os.path.join(fur, f)) or {}).get("symbols") or [])
                       for f in os.listdir(fur)) if os.path.isdir(fur) else 0

    reihe = []

    def stufe(titel, wert, gut, hinweis=""):
        reihe.append({"titel": titel, "wert": wert, "gut": bool(gut), "hinweis": hinweis})

    if not plan:
        stufe("Raeume", "%d gezeichnet" % len(a.get("annotations") or []),
              a.get("annotations"))
        stufe("Massstab", ", ".join(daten["floor_scale"].keys()) or "fehlt",
              daten["floor_scale"])
        stufe("Dachform",
              "modern %s / classic %s" % (daten["dachform_modern"] or "fehlt",
                                          daten["dachform_classic"] or "fehlt")
              if (daten["dachform_modern"] or daten["dachform_classic"]) else "fehlt",
              daten["dachform_modern"] and daten["dachform_classic"])
        stufe("Moebel", "%d gesetzt" % moebel_datei, moebel_datei,
              "im Workbench setzen" if not moebel_datei else "")
        stufe("Gebaut", "noch nicht", False, "Knopf Bauen")
        return reihe

    ebenen = plan.get("floors") or [{}]
    w = sum(len(f.get("walls") or []) for f in ebenen)
    o = [x for f in ebenen for x in (f.get("openings") or [])]
    fenster = sum(1 for x in o if x.get("opening_type") == "window")
    tueren = len(o) - fenster
    raeume = sum(len(f.get("rooms") or []) for f in ebenen)
    moebel = sum(len(f.get("placements") or []) for f in ebenen)
    treppe = 1 if plan.get("shared_stair_core") else 0
    aussen = len(plan.get("exterior_areas") or [])
    blends = sorted(x for x in os.listdir(d) if x.endswith(".blend")) if os.path.isdir(d) else []
    innen = [x for x in renders(name) if x.startswith("interior")]
    ext = [x for x in renders(name) if x.startswith("exterior")]

    stufe("Waende", "%d" % w, w >= 4)
    stufe("Fenster", "%d" % fenster, fenster)
    stufe("Tueren", "%d" % tueren, tueren)
    stufe("Treppen", "%d Kern" % treppe, treppe or len(ebenen) == 1,
          "einstoeckig, keine noetig" if not treppe and len(ebenen) == 1 else "")
    stufe("Boeden / Raeume", "%d" % raeume, raeume)
    stufe("Umgebung", "%d Flaechen" % aussen, aussen)
    stufe("Moebel", "%d platziert" % moebel, moebel,
          "im Workbench setzen: /floorplan-workbench?reference=" + name if not moebel else "")
    stufe("Dachform", "modern %s / classic %s" % (plan.get("roof_type"),
                                                  (classic or {}).get("roof_type")),
          plan.get("roof_type") and (classic or {}).get("roof_type"))
    stufe("Blender-Modelle", "%d .blend" % len(blends), blends)
    stufe("Render innen", "%d" % len(innen), innen)
    stufe("Render aussen", "%d" % len(ext), ext)
    return reihe


def zustand(name, ledger_idx):
    """Was mit diesem Haus los ist, und was als naechstes drankommt."""
    folder = os.path.join(PROJECTS, name)
    a = read_json(os.path.join(folder, "annotations.json")) or {}
    # Dieselbe Zusammenfuehrung wie in stufen() und im Bau, nicht noch einmal
    # von Hand: scripts/hausdaten.py.
    daten = hausdaten.hausdaten(folder)
    side = daten["gebaeudemass"]
    raeume = len(a.get("annotations") or [])
    scale = daten["floor_scale"]
    d = os.path.join(DATA, "corrections", name, "renders", "go-baseline")
    blends = [x for x in os.listdir(d) if x.endswith(".blend")] if os.path.isdir(d) else []
    manifest = read_json(os.path.join(d, "delivery-manifest.json"))
    fails = []
    log = os.path.join(d, "batch-build.log")
    if os.path.exists(log):
        with open(log, encoding="utf-8", errors="replace") as h:
            fails = sorted({l.split()[1] for l in h
                            if l.startswith("FAIL ") and len(l.split()) > 1})
    entry = ledger_idx.get(name) or {}
    bild = any(x.lower().endswith(RASTER) and "room_concept" not in x.lower()
               for x in os.listdir(folder)) if os.path.isdir(folder) else False

    if not raeume:
        stand, tun = "nicht annotiert", None
    elif not scale:
        stand = "Massstab fehlt"
        tun = "messen_bild" if bild else "messen"
    elif not manifest and fails:
        stand, tun = "Verifier: " + ", ".join(fails), "bauen"
    elif not manifest:
        stand, tun = "nicht gebaut", "bauen"
    elif not entry.get("commercial_generator_eligible"):
        stand, tun = "gebaut, Rechte offen", "freigeben"
    else:
        stand, tun = "fertig", None
    return {
        "name": name, "raeume": raeume, "stand": stand, "tun": tun,
        "blends": len(blends), "bilder": renders(name),
        "breite": side.get("gebaeude_breite_m") or "",
        "tiefe": side.get("gebaeude_tiefe_m") or "",
        "stile": (manifest or {}).get("verified_styles") or [],
        "frei": bool(entry.get("commercial_generator_eligible")),
        "stufen": stufen(name),
    }


def alle():
    ledger = read_json(LEDGER) or {}
    idx = {e["project_id"]: e for e in (ledger.get("projects") or [])}
    out = []
    for name in sorted(os.listdir(PROJECTS)):
        if not os.path.exists(os.path.join(PROJECTS, name, "annotations.json")):
            continue
        out.append(zustand(name, idx))
    return out


PAGE = r"""<!doctype html><meta charset="utf-8">
<title>Werkbank</title>
<style>
 :root{--bg:#f6f4f1;--fg:#23282c;--muted:#6d7780;--card:#fff;--line:#e3ded7;
       --ok:#2e7d52;--warn:#b4622a;--accent:#8c5a2b}
 @media (prefers-color-scheme:dark){:root{--bg:#15181b;--fg:#e9e7e4;--muted:#98a1a9;
       --card:#1e2226;--line:#2e343a;--ok:#4caf7d;--warn:#d78b52;--accent:#c68b52}}
 *{box-sizing:border-box}
 body{margin:0;display:grid;grid-template-columns:290px 1fr;height:100vh;
      background:var(--bg);color:var(--fg);
      font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}
 aside{border-right:1px solid var(--line);overflow-y:auto;background:var(--card)}
 aside h2{font-size:11px;text-transform:uppercase;letter-spacing:.07em;
          color:var(--muted);margin:0;padding:14px 16px 8px}
 .item{padding:9px 16px;cursor:pointer;border-bottom:1px solid var(--line);
       font-family:ui-monospace,monospace;font-size:12px;display:flex;
       justify-content:space-between;gap:8px}
 .item:hover{background:var(--bg)}
 .item.aktiv{background:var(--accent);color:#fff}
 .item .st{font-family:ui-sans-serif,sans-serif;font-size:10px;opacity:.7;
           white-space:nowrap}
 main{overflow-y:auto;padding:24px 30px 60px}
 h1{font-size:20px;margin:0 0 2px;font-family:ui-monospace,monospace}
 .stand{color:var(--muted);font-size:14px;margin-bottom:18px}
 .stand b{color:var(--warn)}
 .stand b.ok{color:var(--ok)}
 .aktionen{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 22px;align-items:center}
 button{background:var(--accent);color:#fff;border:0;border-radius:7px;
        padding:10px 20px;font-size:14px;font-weight:600;cursor:pointer}
 button.zweit{background:transparent;color:var(--fg);border:1px solid var(--line)}
 button:disabled{opacity:.4;cursor:default}
 input{padding:8px 10px;border:1px solid var(--line);border-radius:6px;
       background:var(--bg);color:var(--fg);font-size:14px;width:110px;
       font-family:ui-monospace,monospace}
 input.breit{width:320px;font-family:inherit}
 .bilder{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px}
 figure{margin:0;background:var(--card);border:1px solid var(--line);
        border-radius:10px;overflow:hidden}
 figure img{width:100%;display:block;background:#fff}
 figcaption{padding:7px 11px;font-size:11px;color:var(--muted);
            font-family:ui-monospace,monospace}
 #stufen{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
          gap:8px;margin:0 0 22px}
 .stufe{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--warn);
        border-radius:7px;padding:8px 11px;font-size:13px}
 .stufe.gut{border-left-color:var(--ok)}
 .stufe .t{display:block;font-size:11px;text-transform:uppercase;
           letter-spacing:.05em;color:var(--muted)}
 .stufe .w{font-family:ui-monospace,monospace}
 .stufe .h{display:block;font-size:11px;color:var(--warn);margin-top:3px}
 #log{margin-top:18px;padding:11px 13px;background:var(--card);
      border:1px solid var(--line);border-radius:8px;font-size:12.5px;
      font-family:ui-monospace,monospace;white-space:pre-wrap;color:var(--muted);
      max-height:220px;overflow:auto;display:none}
</style>
<aside><h2 id="kopf">Haeuser</h2><div id="liste"></div></aside>
<main>
  <h1 id="titel">-</h1>
  <div class="stand" id="stand"></div>
  <div class="aktionen" id="aktionen"></div>
  <div id="stufen"></div>
  <div class="bilder" id="bilder"></div>
  <div id="log"></div>
</main>
<script>
let daten = [], aktiv = null;

function male(){
  const l = document.getElementById('liste');
  l.innerHTML = '';
  for (const h of daten){
    const d = document.createElement('div');
    d.className = 'item' + (h.name === aktiv ? ' aktiv' : '');
    d.innerHTML = '<span>' + h.name.slice(0,26) + '</span><span class="st">' +
                  (h.stand === 'fertig' ? 'fertig' : h.stand.slice(0,18)) + '</span>';
    d.onclick = () => { aktiv = h.name; male(); zeige(); };
    l.appendChild(d);
  }
  const offen = daten.filter(x => x.stand !== 'fertig').length;
  document.getElementById('kopf').textContent =
    daten.length + ' Haeuser, ' + offen + ' offen';
}

function zeige(){
  const h = daten.find(x => x.name === aktiv);
  if (!h) return;
  document.getElementById('titel').textContent = h.name;
  document.getElementById('stand').innerHTML =
    h.raeume + ' Raeume &middot; ' + h.blends + ' .blend &middot; ' +
    (h.stile.length ? h.stile.join('+') : 'kein Stil') + ' &middot; <b class="' +
    (h.stand === 'fertig' ? 'ok' : '') + '">' + h.stand + '</b>';

  const a = document.getElementById('aktionen');
  a.innerHTML = '';
  const knopf = (text, fn, zweit) => {
    const b = document.createElement('button');
    b.textContent = text; if (zweit) b.className = 'zweit';
    b.onclick = fn; a.appendChild(b); return b;
  };
  if (h.tun === 'messen' || h.tun === 'messen_bild'){
    const br = document.createElement('input'); br.placeholder = 'Breite m'; br.value = h.breite;
    const ti = document.createElement('input'); ti.placeholder = 'Tiefe m'; ti.value = h.tiefe;
    a.appendChild(br); a.appendChild(ti);
    knopf('Messen + Bauen', () => tu('messen', {breite: br.value, tiefe: ti.value}));
  } else if (h.tun === 'bauen'){
    knopf('Bauen', () => tu('bauen'));
  } else if (h.tun === 'freigeben'){
    const g = document.createElement('input');
    g.className = 'breit'; g.placeholder = 'Grund: warum hast du die Rechte?';
    a.appendChild(g);
    knopf('Freigeben', () => tu('freigeben', {grund: g.value}));
    knopf('Hochladen', () => tu('hochladen'), true);
  }
  if (h.blends) knopf('Neu bauen', () => tu('bauen'), true);
  knopf('Weiter', weiter, true);

  const st = document.getElementById('stufen');
  st.innerHTML = '';
  for (const s of (h.stufen || [])){
    const d = document.createElement('div');
    d.className = 'stufe' + (s.gut ? ' gut' : '');
    d.innerHTML = '<span class="t">' + s.titel + '</span><span class="w">' + s.wert +
                  '</span>' + (s.hinweis ? '<span class="h">' + s.hinweis + '</span>' : '');
    st.appendChild(d);
  }

  const b = document.getElementById('bilder');
  b.innerHTML = '';
  const riss = document.createElement('figure');
  riss.innerHTML = '<img src="/riss/' + encodeURIComponent(h.name) + '?t=' + Date.now() +
                   '"><figcaption>gezeichnete Raeume</figcaption>';
  b.appendChild(riss);
  for (const bild of h.bilder){
    const f = document.createElement('figure');
    f.innerHTML = '<img loading="lazy" src="/bild/' + encodeURIComponent(h.name) + '/' +
      encodeURIComponent(bild) + '?t=' + Date.now() + '"><figcaption>' + bild + '</figcaption>';
    b.appendChild(f);
  }
}

function weiter(){
  const i = daten.findIndex(x => x.name === aktiv);
  const rest = daten.slice(i + 1).find(x => x.stand !== 'fertig') ||
               daten.find(x => x.stand !== 'fertig');
  if (rest){ aktiv = rest.name; male(); zeige(); }
}

function tu(was, extra){
  const log = document.getElementById('log');
  log.style.display = 'block';
  log.textContent = was + ' laeuft ...';
  for (const b of document.querySelectorAll('button')) b.disabled = true;
  fetch('/tu', {method:'POST', body: JSON.stringify(
      Object.assign({haus: aktiv, was: was}, extra || {}))})
    .then(r => r.json()).then(r => {
      log.textContent = r.ausgabe || '(keine Ausgabe)';
      return laden();
    }).then(() => {
      for (const b of document.querySelectorAll('button')) b.disabled = false;
    });
}

function laden(){
  return fetch('/daten').then(r => r.json()).then(d => {
    daten = d;
    if (!aktiv || !daten.find(x => x.name === aktiv)){
      const o = daten.find(x => x.stand !== 'fertig') || daten[0];
      aktiv = o && o.name;
    }
    male(); zeige();
  });
}
laden();
</script>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, body, typ="text/html; charset=utf-8", code=200):
        raw = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except Exception:
            pass

    def _datei(self, pfad, erlaubt_in):
        voll = os.path.abspath(pfad)
        if not voll.startswith(os.path.abspath(erlaubt_in)) or not os.path.exists(voll):
            return self._send("nicht gefunden", code=404)
        typ = mimetypes.guess_type(voll)[0] or "application/octet-stream"
        with open(voll, "rb") as handle:
            self._send(handle.read(), typ)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            return self._send(PAGE)
        if path == "/daten":
            return self._send(json.dumps(alle()), "application/json")
        if path.startswith("/riss/"):
            name = urllib.parse.unquote(path[len("/riss/"):])
            folder = os.path.join(PROJECTS, name)
            for k in ("groundfloor_room_concept.svg", "room_concept.svg"):
                if os.path.exists(os.path.join(folder, k)):
                    return self._datei(os.path.join(folder, k), PROJECTS)
            return self._send("kein Riss", code=404)
        if path.startswith("/bild/"):
            teile = path[len("/bild/"):].split("/", 1)
            if len(teile) != 2:
                return self._send("nicht gefunden", code=404)
            name, datei = (urllib.parse.unquote(t) for t in teile)
            return self._datei(
                os.path.join(DATA, "corrections", name, "renders", "go-baseline", datei),
                os.path.join(DATA, "corrections"))
        self._send("nicht gefunden", code=404)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/tu":
            return self._send("nicht gefunden", code=404)
        laenge = int(self.headers.get("Content-Length") or 0)
        req = json.loads(self.rfile.read(laenge) or b"{}")
        haus, was = req.get("haus"), req.get("was")
        if haus not in {h["name"] for h in alle()}:
            return self._send(json.dumps({"ausgabe": "unbekanntes Haus"}), "application/json")

        befehle = []
        if was == "messen":
            if not req.get("breite") or not req.get("tiefe"):
                return self._send(json.dumps({"ausgabe": "Breite und Tiefe fehlen"}),
                                  "application/json")
            befehle.append([PY, os.path.join(HERE, "gebaeudemass.py"), haus,
                            "--breite", str(req["breite"]), "--tiefe", str(req["tiefe"])])
            befehle.append([PY, os.path.join(HERE, "go.py"), haus])
        elif was == "bauen":
            befehle.append([PY, os.path.join(HERE, "go.py"), haus])
        elif was == "hochladen":
            befehle.append([PY, os.path.join(HERE, "go.py"), haus, "--hochladen"])
        elif was == "freigeben":
            if not req.get("grund"):
                return self._send(json.dumps({"ausgabe": "Ohne Grund keine Freigabe."}),
                                  "application/json")
            befehle.append([PY, os.path.join(HERE, "approve-plan.py"), haus,
                            "--reason", req["grund"]])
        else:
            return self._send(json.dumps({"ausgabe": "unbekannte Aktion"}), "application/json")

        ausgabe = []
        for cmd in befehle:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               errors="replace", cwd=HERE)
            ausgabe.append((r.stdout or "") + (r.stderr or ""))
        self._send(json.dumps({"ausgabe": "\n".join(x.strip() for x in ausgabe if x.strip())}),
                   "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as srv:
        print("Werkbank:  http://localhost:%d" % PORT)
        srv.serve_forever()
