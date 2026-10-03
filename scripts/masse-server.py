#!/usr/bin/env python3
"""Eine Seite im Browser, in die du die Masse tippst. Speichert direkt.

    python masse-server.py
    -> http://localhost:8799

Kein CSV von Hand, kein Kommandozeilen-Getippe. Die Seite listet jedes Haus,
das noch keinen Massstab hat, mit zwei Feldern. Speichern schreibt
gebaeudemass.json neben die Annotation -- annotations.json wird nie angefasst.

Was schon gesetzt ist, steht beim Laden drin und kann korrigiert werden.
"""

import http.server
import json
import os
import socketserver
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import hausdaten  # noqa: E402
SUITE = os.path.dirname(os.path.dirname(HERE))
PROJECTS = os.path.join(SUITE, "floorplan-simplifier", "projects")
PORT = 8799
PY = sys.executable
RASTER = (".png", ".jpg", ".jpeg", ".pdf")


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return default


def haeuser():
    """Every drawn house, with whatever measurement it already has."""
    out = []
    for name in sorted(os.listdir(PROJECTS)):
        folder = os.path.join(PROJECTS, name)
        # Zeichnung und Gebaeudemass kommen aus hausdaten.py -- pro Geschoss,
        # mit derselben Vorrangregel wie der Bau. Vorher sah "gemessen" nur in
        # die Zeichnung, und ein leerer Geschoss-Schluessel ({"groundfloor":
        # null}, den der Annotator anlegt, sobald das Geschoss existiert)
        # zaehlte als Messung: genau die Haeuser, die auf dieser Seite
        # auftauchen sollen, standen hier als erledigt.
        daten = hausdaten.hausdaten(folder)
        annotations = daten["annotationen"]
        if not annotations or not (annotations.get("annotations") or []):
            continue
        side = daten["gebaeudemass"]
        raeume = len(annotations["annotations"])
        bild = any(x.lower().endswith(RASTER) and "room_concept" not in x.lower()
                   for x in os.listdir(folder))
        out.append({
            "name": name,
            "raeume": raeume,
            "bild": bild,
            "breite": side.get("gebaeude_breite_m") or "",
            "tiefe": side.get("gebaeude_tiefe_m") or "",
            "fertig": bool(daten["floor_scale"]),
        })
    return out


PAGE = """<!doctype html><meta charset="utf-8">
<title>Gebaeudemasse</title>
<style>
 :root{--bg:#f6f4f1;--fg:#23282c;--muted:#6d7780;--card:#fff;--line:#e3ded7;
       --ok:#2e7d52;--accent:#8c5a2b}
 @media (prefers-color-scheme:dark){:root{--bg:#16191c;--fg:#e8e6e3;--muted:#98a1a9;
       --card:#1f2327;--line:#2f353b;--ok:#4caf7d;--accent:#c68b52}}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--fg);
      font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}
 header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);
        padding:16px 22px;display:flex;gap:16px;align-items:center;flex-wrap:wrap;z-index:5}
 h1{font-size:18px;margin:0}
 .zaehler{color:var(--muted);font-size:13px}
 button{background:var(--accent);color:#fff;border:0;border-radius:7px;
         padding:9px 18px;font-size:14px;font-weight:600;cursor:pointer}
 button:disabled{opacity:.45;cursor:default}
 .wrap{padding:16px 22px 60px;max-width:1000px;margin:0 auto}
 table{width:100%;border-collapse:collapse;background:var(--card);
       border:1px solid var(--line);border-radius:9px;overflow:hidden}
 th,td{padding:8px 11px;text-align:left;border-bottom:1px solid var(--line)}
 th{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
 tr:last-child td{border-bottom:0}
 td.n{font-family:ui-monospace,monospace;font-size:13px}
 input{width:88px;padding:6px 8px;border:1px solid var(--line);border-radius:6px;
       background:var(--bg);color:var(--fg);font-size:14px;font-family:ui-monospace,monospace}
 input:focus{outline:2px solid var(--accent);outline-offset:-1px}
 .fertig td.n::after{content:" gemessen";color:var(--ok);font-size:11px;
                     font-family:ui-sans-serif,sans-serif}
 .hint{color:var(--muted);font-size:12px}
 img.riss{width:150px;height:110px;object-fit:contain;background:#fff;
          border:1px solid var(--line);border-radius:6px;cursor:zoom-in}
 img.riss:hover{position:relative;transform:scale(3.2);transform-origin:left center;
                z-index:9;box-shadow:0 8px 40px rgba(0,0,0,.35)}
 #status{font-size:13px;color:var(--ok)}
</style>
<header>
  <h1>Gebaeudemasse</h1>
  <span class="zaehler" id="z"></span>
  <button id="save">Speichern</button>
  <span id="status"></span>
</header>
<div class="wrap">
 <p class="hint">Breite und Tiefe des Gebaeudes in Metern. Nur ausgefuellte
 Zeilen werden gespeichert &mdash; du kannst in Etappen arbeiten.
 <code>annotations.json</code> wird nicht veraendert.</p>
 <table><thead><tr><th>Riss</th><th>Haus</th><th>Raeume</th><th>Vorlage</th>
 <th>Breite&nbsp;m</th><th>Tiefe&nbsp;m</th></tr></thead>
 <tbody id="b"></tbody></table>
</div>
<script>
let daten = [];
function zeichne(){
  const b = document.getElementById('b');
  b.innerHTML = '';
  let offen = 0;
  for (const h of daten){
    if (!h.fertig) offen++;
    const tr = document.createElement('tr');
    if (h.fertig) tr.className = 'fertig';
    tr.innerHTML = '<td><img class="riss" loading="lazy" src="/riss/' +
      encodeURIComponent(h.name) + '" alt=""></td>' +
      '<td class="n">' + h.name + '</td><td>' + h.raeume + '</td><td>' +
      (h.bild ? 'Bild' : '&mdash;') + '</td>' +
      '<td><input data-n="' + h.name + '" data-f="breite" value="' + h.breite + '" inputmode="decimal"></td>' +
      '<td><input data-n="' + h.name + '" data-f="tiefe" value="' + h.tiefe + '" inputmode="decimal"></td>';
    b.appendChild(tr);
  }
  document.getElementById('z').textContent = daten.length + ' Haeuser, ' + offen + ' noch ohne Mass';
}
fetch('/daten').then(r => r.json()).then(d => { daten = d; zeichne(); });
document.getElementById('save').addEventListener('click', () => {
  const werte = {};
  for (const el of document.querySelectorAll('input')){
    const n = el.dataset.n;
    werte[n] = werte[n] || {};
    werte[n][el.dataset.f] = el.value.trim().replace(',', '.');
  }
  const nutzbar = {};
  for (const [n, v] of Object.entries(werte))
    if (v.breite && v.tiefe) nutzbar[n] = v;
  const btn = document.getElementById('save');
  btn.disabled = true;
  document.getElementById('status').textContent = 'speichere ...';
  fetch('/speichern', {method:'POST', body: JSON.stringify(nutzbar)})
    .then(r => r.json()).then(r => {
      document.getElementById('status').textContent =
        r.gesetzt + ' gespeichert' + (r.fehler ? ', ' + r.fehler + ' Fehler' : '');
      btn.disabled = false;
      return fetch('/daten').then(x => x.json()).then(d => { daten = d; zeichne(); });
    });
});
</script>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, body, typ="text/html; charset=utf-8", code=200):
        raw = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            self._send(PAGE)
        elif path.startswith("/riss/"):
            # Die gezeichnete Raumaufteilung. Ohne sie ist die Liste nur eine
            # Tabelle mit Namen -- man kann kein Haus wiedererkennen, und genau
            # das Wiedererkennen ist die Arbeit.
            name = urllib.parse.unquote(path[len("/riss/"):])
            folder = os.path.join(PROJECTS, name)
            for kandidat in ("groundfloor_room_concept.svg", "room_concept.svg"):
                voll = os.path.join(folder, kandidat)
                if os.path.exists(voll) and os.path.dirname(os.path.abspath(voll)) == os.path.abspath(folder):
                    with open(voll, "rb") as handle:
                        return self._send(handle.read(), "image/svg+xml")
            self._send("kein Riss", code=404)
        elif path == "/daten":
            self._send(json.dumps(haeuser()), "application/json")
        else:
            self._send("nicht gefunden", code=404)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/speichern":
            return self._send("nicht gefunden", code=404)
        laenge = int(self.headers.get("Content-Length") or 0)
        werte = json.loads(self.rfile.read(laenge) or b"{}")
        gesetzt = fehler = 0
        for name, v in werte.items():
            if name not in {h["name"] for h in haeuser()}:
                fehler += 1
                continue
            code = subprocess.call(
                [PY, os.path.join(HERE, "gebaeudemass.py"), name,
                 "--breite", str(v["breite"]), "--tiefe", str(v["tiefe"])],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=HERE)
            if code == 0:
                gesetzt += 1
            else:
                fehler += 1
        print("[masse] %d gespeichert, %d Fehler" % (gesetzt, fehler))
        self._send(json.dumps({"gesetzt": gesetzt, "fehler": fehler}),
                   "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as srv:
        print("Gebaeudemasse eintragen:  http://localhost:%d" % PORT)
        srv.serve_forever()
