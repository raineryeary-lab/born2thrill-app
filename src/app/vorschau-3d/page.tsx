"use client";

/**
 * 3D-Vorschau des Hauses von aussen, vor dem Bau (vorschau-3d-v1).
 *
 * Rainer, 2026-11-03: "WOULD IT BE SUPER HARD TO DO A 3D PREVIEW OF SOME SORT
 * of the outside before we really go into the build?" Gezeigt wird die GLB,
 * die /api/floorplan-workbench/vorschau-3d aus dem echten Bau schreibt --
 * dieselben Waende, Oeffnungen und Daecher wie im Aussenbild, nur drehbar.
 *
 * fenster-3d-v1 (Rainer, 2026-11-12): "click on the 3d windows to move them
 * horizontally with a red light up whenever we got an alignment and maybe even
 * rightclick and change the size, bruestung or full height and the number of
 * glass panes". Im Modus "Fenster bearbeiten": Fenster anklicken und entlang
 * der Wand ziehen; fluchtet es mit einem Fenster darueber/darunter (Kante oder
 * Mitte), leuchtet es rot und rastet ein. Rechtsklick: Breite, Bruestung oder
 * bodentief, Glasfelder. Gespeichert wird in die Zeichnung
 * (scripts/fenster-bearbeiten.py), danach baut die Vorschau neu.
 *
 * Aufruf: /vorschau-3d?plan=<projekt-id>
 */
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const DACH_NAMEN: Record<string, string> = {
  flachdach: "Flachdach",
  walmdach: "Walmdach",
  satteldach: "Satteldach",
  "satteldach-kubus": "Satteldach (Kubus)",
  pultdach: "Pultdach",
  doppelpultdach: "Versetztes Pultdach",
};

const FANG_M = 0.06;          // so nah rastet ein Fenster auf eine Flucht
const FASSADE_QUER_M = 0.45;  // so weit duerfen die Wandlinien zweier Geschosse auseinander liegen
const BREITEN_CM = [51, 63, 76, 88, 101, 113, 126, 138, 151, 176, 201, 226, 251, 301];

type Fenster = {
  id: string;
  geschoss: number;
  mitte: THREE.Vector3;        // GLB-Meter
  u: THREE.Vector3;            // entlang der Wand, GLB
  uPlan: [number, number];     // entlang der Wand, Plan-mm-Richtung
  breite: number;              // m
  typ: string | null;
  felder: number | null;
  knoten: THREE.Object3D[];
  start: THREE.Vector3[];      // Ausgangslagen der Knoten
};

type Menue = { x: number; y: number; f: Fenster; breite: number; typ: string; felder: string };

export default function Vorschau3d() {
  const buehne = useRef<HTMLDivElement | null>(null);
  const welt = useRef<{ scene: THREE.Scene; camera: THREE.PerspectiveCamera; controls: OrbitControls;
    haus: THREE.Object3D | null; renderer: THREE.WebGLRenderer } | null>(null);
  const fensterRef = useRef<Fenster[]>([]);
  const modusRef = useRef(false);
  const [plan, setPlan] = useState("");
  const [daecher, setDaecher] = useState<string[]>([]);
  const [dach, setDach] = useState("");
  const [status, setStatus] = useState("Lädt …");
  const [laeuft, setLaeuft] = useState(false);
  const [modus, setModus] = useState(false);
  const [info, setInfo] = useState("");
  const [menue, setMenue] = useState<Menue | null>(null);
  const planRef = useRef("");
  const dachRef = useRef("");
  useEffect(() => { modusRef.current = modus; }, [modus]);
  useEffect(() => { planRef.current = plan; dachRef.current = dach; }, [plan, dach]);

  // Szene einmal aufbauen.
  useEffect(() => {
    const el = buehne.current;
    if (!el) return;
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    // Neutrales Grau, nie blau (REGELN 25).
    scene.background = new THREE.Color("#c9c9c7");
    scene.add(new THREE.HemisphereLight("#ffffff", "#8a8a86", 1.6));
    const sonne = new THREE.DirectionalLight("#ffffff", 2.2);
    sonne.position.set(30, 50, 20);
    scene.add(sonne);
    const camera = new THREE.PerspectiveCamera(35, el.clientWidth / el.clientHeight, 0.1, 2000);
    camera.position.set(25, 15, 25);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.maxPolarAngle = Math.PI / 2 - 0.02;   // nicht unter den Boden
    welt.current = { scene, camera, controls, haus: null, renderer };
    let bild = 0;
    const schleife = () => {
      controls.update();
      renderer.render(scene, camera);
      bild = requestAnimationFrame(schleife);
    };
    schleife();
    const groesse = () => {
      camera.aspect = el.clientWidth / el.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(el.clientWidth, el.clientHeight);
    };
    window.addEventListener("resize", groesse);

    // ---- Fenster anklicken, ziehen, Rechtsklick (fenster-3d-v1) ----
    const strahl = new THREE.Raycaster();
    const maus = new THREE.Vector2();
    const strahlAus = (e: PointerEvent | MouseEvent) => {
      const r = renderer.domElement.getBoundingClientRect();
      maus.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      strahl.setFromCamera(maus, camera);
    };
    const fensterUnter = (e: PointerEvent | MouseEvent): Fenster | null => {
      const w = welt.current;
      if (!w?.haus) return null;
      strahlAus(e);
      const treffer = strahl.intersectObject(w.haus, true);
      for (const t of treffer) {
        let o: THREE.Object3D | null = t.object;
        while (o && !o.name.includes("~")) o = o.parent;
        if (o) {
          const f = fensterRef.current.find((x) => x.knoten.includes(o!));
          if (f) return f;
        }
        // Erste getroffene Flaeche ist eine Wand oder ein Dach: kein Fenster.
        return null;
      }
      return null;
    };

    let zug: { f: Fenster; ebene: THREE.Plane; anfang: THREE.Vector3; weg: number;
               partner: Fenster | null } | null = null;
    const leuchten = (f: Fenster | null, an: boolean) => {
      if (!f) return;
      for (const k of f.knoten) {
        k.traverse((m) => {
          const mesh = m as THREE.Mesh;
          if (!mesh.isMesh) return;
          if (!mesh.userData.eigenesMaterial) {
            mesh.material = (mesh.material as THREE.Material).clone();
            mesh.userData.eigenesMaterial = true;
          }
          const mat = mesh.material as THREE.MeshStandardMaterial;
          if (mat.emissive) mat.emissive.set(an ? "#ff1a1a" : "#000000");
          if (mat.emissiveIntensity !== undefined) mat.emissiveIntensity = an ? 1.2 : 1;
        });
      }
    };
    const markieren = (f: Fenster, an: boolean) => {
      for (const k of f.knoten) {
        k.traverse((m) => {
          const mesh = m as THREE.Mesh;
          if (!mesh.isMesh) return;
          if (!mesh.userData.eigenesMaterial) {
            mesh.material = (mesh.material as THREE.Material).clone();
            mesh.userData.eigenesMaterial = true;
          }
          const mat = mesh.material as THREE.MeshStandardMaterial;
          if (mat.emissive) mat.emissive.set(an ? "#2563eb" : "#000000");
        });
      }
    };

    const runter = (e: PointerEvent) => {
      if (!modusRef.current || e.button !== 0) return;
      const f = fensterUnter(e);
      if (!f) return;
      e.preventDefault();
      controls.enabled = false;
      const normale = new THREE.Vector3().crossVectors(f.u, new THREE.Vector3(0, 1, 0)).normalize();
      const ebene = new THREE.Plane().setFromNormalAndCoplanarPoint(normale, f.mitte);
      const anfang = new THREE.Vector3();
      strahl.ray.intersectPlane(ebene, anfang);
      zug = { f, ebene, anfang, weg: 0, partner: null };
      markieren(f, true);
      setInfo(`Fenster ${Math.round(f.breite * 100)} cm · ziehen zum Verschieben`);
      renderer.domElement.setPointerCapture(e.pointerId);
    };
    const bewegen = (e: PointerEvent) => {
      if (!zug) return;
      strahlAus(e);
      const p = new THREE.Vector3();
      if (!strahl.ray.intersectPlane(zug.ebene, p)) return;
      let weg = p.sub(zug.anfang).dot(zug.f.u);
      // Fluchten auf Nachbargeschossen derselben Fassade.
      const f = zug.f;
      let bester: { d: number; partner: Fenster; art: string } | null = null;
      for (const o of fensterRef.current) {
        if (o === f || Math.abs(o.geschoss - f.geschoss) !== 1) continue;
        if (Math.abs(o.u.dot(f.u)) < 0.995) continue;
        const quer = o.mitte.clone().sub(f.mitte);
        const entlang = quer.dot(f.u);
        quer.addScaledVector(f.u, -entlang).setY(0);
        if (quer.length() > FASSADE_QUER_M) continue;
        const ziele: [number, string][] = [
          [entlang, "Mitte"],
          [entlang - o.breite / 2 + f.breite / 2, "Kante"],
          [entlang + o.breite / 2 - f.breite / 2, "Kante"],
        ];
        for (const [ziel, art] of ziele) {
          const d = Math.abs(weg - ziel);
          if (d < FANG_M && (!bester || d < bester.d)) bester = { d, partner: o, art };
        }
        void 0;
      }
      if (zug.partner && zug.partner !== bester?.partner) markieren(zug.partner, false);
      if (bester) {
        const o = bester.partner;
        const entlang = o.mitte.clone().sub(f.mitte).dot(f.u);
        const ziele = [entlang, entlang - o.breite / 2 + f.breite / 2, entlang + o.breite / 2 - f.breite / 2];
        weg = ziele.reduce((a, b) => (Math.abs(weg - b) < Math.abs(weg - a) ? b : a));
        leuchten(f, true);
        leuchten(o, true);
        zug.partner = o;
        setInfo(`Fluchtet (${bester.art}) mit dem Fenster ${o.geschoss > f.geschoss ? "darüber" : "darunter"}`
          + ` · verschoben ${Math.round(weg * 1000)} mm`);
      } else {
        leuchten(f, false);
        markieren(f, true);
        zug.partner = null;
        setInfo(`Verschoben ${Math.round(weg * 1000)} mm`);
      }
      zug.weg = weg;
      f.knoten.forEach((k, i) => k.position.copy(f.start[i]).addScaledVector(f.u, weg));
    };
    const hoch = async () => {
      if (!zug) return;
      const { f, weg, partner } = zug;
      zug = null;
      controls.enabled = true;
      if (partner) leuchten(partner, false);
      if (Math.abs(weg) < 0.005) {
        leuchten(f, false);
        markieren(f, false);
        setInfo("");
        return;
      }
      const mm = weg * 1000;
      setInfo(`Speichere Verschiebung ${Math.round(mm)} mm …`);
      await aendern({ id: f.id, verschieben: [mm * f.uPlan[0], mm * f.uPlan[1]] });
    };
    const rechts = (e: MouseEvent) => {
      if (!modusRef.current) return;
      const f = fensterUnter(e);
      if (!f) return;
      e.preventDefault();
      setMenue({ x: e.clientX, y: e.clientY, f, breite: Math.round(f.breite * 100),
                 typ: f.typ || "", felder: f.felder ? String(f.felder) : "auto" });
    };
    renderer.domElement.addEventListener("pointerdown", runter);
    renderer.domElement.addEventListener("pointermove", bewegen);
    renderer.domElement.addEventListener("pointerup", hoch);
    renderer.domElement.addEventListener("contextmenu", rechts);
    return () => {
      cancelAnimationFrame(bild);
      window.removeEventListener("resize", groesse);
      renderer.domElement.removeEventListener("pointerdown", runter);
      renderer.domElement.removeEventListener("pointermove", bewegen);
      renderer.domElement.removeEventListener("pointerup", hoch);
      renderer.domElement.removeEventListener("contextmenu", rechts);
      controls.dispose();
      renderer.dispose();
      el.removeChild(renderer.domElement);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Die Fenster der GLB den Fenstern des Plans zuordnen. */
  async function fensterLesen(p: string, szene: THREE.Object3D) {
    const planJson = await fetch(`/api/floorplan-workbench/vorschau-3d?plan=${encodeURIComponent(p)}&datei=plan`,
      { cache: "no-store" }).then((r) => r.json()).catch(() => ({}));
    const knotenJe = new Map<string, THREE.Object3D[]>();
    szene.traverse((o) => {
      const m = /~([^~]+)(~|-\d+$|$)/.exec(o.name);
      if (!m || o.parent?.name.includes("~")) return;
      const liste = knotenJe.get(m[1]) || [];
      liste.push(o);
      knotenJe.set(m[1], liste);
    });
    const liste: Fenster[] = [];
    (planJson.floors || []).forEach((fl: any, geschoss: number) => {
      const waende = new Map((fl.walls || []).map((w: any) => [w.id, w]));
      for (const o of fl.openings || []) {
        if (o.opening_type !== "window") continue;
        const w: any = waende.get(o.wall_id);
        if (!w) continue;
        const [sx, sy] = w.start_mm;
        const [ex, ey] = w.end_mm;
        const l = Math.hypot(ex - sx, ey - sy) || 1;
        const ux = (ex - sx) / l;
        const uy = (ey - sy) / l;
        const cx = sx + (ex - sx) * o.position;
        const cy = sy + (ey - sy) * o.position;
        const schluessel = [...knotenJe.keys()].find((k) => o.id === k || o.id.startsWith(k));
        if (!schluessel) continue;
        const knoten = knotenJe.get(schluessel)!;
        const hoehe = knoten.reduce((s, k) => s + k.position.y, 0) / knoten.length;
        liste.push({
          id: o.id, geschoss,
          mitte: new THREE.Vector3(cx / 1000, hoehe, -cy / 1000),
          u: new THREE.Vector3(ux, 0, -uy).normalize(),
          uPlan: [ux, uy], breite: o.width_mm / 1000,
          typ: o.window_type || null, felder: o.panes || null,
          knoten, start: knoten.map((k) => k.position.clone()),
        });
      }
    });
    fensterRef.current = liste;
    // Pruefzugang fuer automatische Tests (nur lokal, nur lesen).
    (window as any).__fenster3d = { fenster: liste, welt: welt.current };
  }

  async function laden(p: string, d: string, kameraLassen = false) {
    const w = welt.current;
    if (!w) return;
    setStatus(`${DACH_NAMEN[d] || d} wird geladen …`);
    const gltf = await new GLTFLoader().loadAsync(
      `/api/floorplan-workbench/vorschau-3d?plan=${encodeURIComponent(p)}&dach=${encodeURIComponent(d)}&t=${Date.now()}`);
    if (w.haus) w.scene.remove(w.haus);
    w.haus = gltf.scene;
    w.scene.add(gltf.scene);
    await fensterLesen(p, gltf.scene);
    if (!kameraLassen) {
      // Kamera auf das Haus: 3/4-Ansicht, ganzes Gebaeude.
      const box = new THREE.Box3().setFromObject(gltf.scene);
      const mitte = box.getCenter(new THREE.Vector3());
      const groesse = box.getSize(new THREE.Vector3()).length();
      w.controls.target.copy(mitte);
      w.camera.position.copy(mitte).add(new THREE.Vector3(0.7, 0.45, 0.7).multiplyScalar(groesse * 0.9));
      w.camera.near = groesse / 200;
      w.camera.far = groesse * 20;
      w.camera.updateProjectionMatrix();
    }
    setStatus("");
  }

  async function bauen(p: string, d: string, kameraLassen = false) {
    setLaeuft(true);
    setStatus(`${DACH_NAMEN[d] || d || "Vorschau"} wird gebaut (einige Sekunden) …`);
    try {
      const antwort = await fetch("/api/floorplan-workbench/vorschau-3d", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: p, dach: d }),
      });
      const ergebnis = await antwort.json();
      if (!antwort.ok) {
        setStatus(`Fehler: ${ergebnis.error || antwort.status}`);
        console.error(ergebnis.ausgabe);
        return;
      }
      setDaecher(ergebnis.daecher);
      setDach(ergebnis.dach);
      await laden(p, ergebnis.dach, kameraLassen);
    } finally {
      setLaeuft(false);
    }
  }

  /** Aenderung in die Zeichnung schreiben, dann neu bauen. */
  async function aendern(aenderung: Record<string, unknown>) {
    const p = planRef.current;
    const antwort = await fetch("/api/floorplan-workbench/fenster", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan: p, ...aenderung }),
    });
    const e = await antwort.json().catch(() => ({}));
    if (!e.ok) {
      setInfo(`Nicht gespeichert: ${e.ausgabe || antwort.status}`);
      await laden(p, dachRef.current, true);
      return;
    }
    setInfo("Gespeichert – Vorschau wird neu gebaut …");
    await bauen(p, dachRef.current, true);
    setInfo("Gespeichert. Für die Bilder das Haus neu bauen.");
  }

  // Beim Oeffnen: immer frisch bauen -- die Vorschau soll den Stand von
  // JETZT zeigen, nicht den vom letzten Mal.
  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get("plan") || "";
    setPlan(p);
    if (!p) { setStatus("Kein Haus angegeben (?plan=…)."); return; }
    bauen(p, "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <main className="flex h-screen flex-col bg-stone-100 text-stone-800">
    <div className="flex flex-wrap items-center gap-2 border-b border-stone-300 bg-white px-4 py-2 text-sm">
      <span className="font-semibold">3D-Vorschau</span>
      <span className="text-stone-500">{plan}</span>
      <span className="mx-2 h-4 w-px bg-stone-300" />
      {daecher.map((d) => <button key={d} type="button" disabled={laeuft}
        onClick={() => bauen(plan, d)}
        className={`rounded border px-2 py-1 ${d === dach ? "border-emerald-700 bg-emerald-700 text-white" : "border-stone-300 bg-white"} disabled:opacity-50`}
      >{DACH_NAMEN[d] || d}</button>)}
      <label className="ml-4 flex items-center gap-1">
        <input type="checkbox" checked={modus} onChange={(e) => { setModus(e.target.checked); setMenue(null); }} />
        Fenster bearbeiten
      </label>
      <button type="button" disabled={laeuft || !plan} onClick={() => bauen(plan, dach)}
        className="ml-auto rounded bg-stone-800 px-3 py-1 text-white disabled:opacity-50">↻ Neu bauen</button>
    </div>
    <div className="relative flex-1">
      <div ref={buehne} className="absolute inset-0" />
      {status && <div className="absolute left-4 top-4 rounded bg-white/90 px-3 py-2 text-sm shadow">{status}</div>}
      {modus && info && <div className="absolute right-4 top-4 rounded bg-white/95 px-3 py-2 text-sm shadow">{info}</div>}
      {menue && <div className="absolute z-10 grid gap-2 rounded border border-stone-300 bg-white p-3 text-sm shadow-lg"
        style={{ left: Math.min(menue.x, window.innerWidth - 260), top: Math.min(menue.y - 40, window.innerHeight - 260), width: 240 }}
        onContextMenu={(e) => e.preventDefault()}>
        <b>Fenster ändern</b>
        <label className="grid gap-1">Breite (cm)
          <select value={menue.breite} onChange={(e) => setMenue({ ...menue, breite: Number(e.target.value) })}
            className="rounded border px-1 py-1">
            {[...new Set([Math.round(menue.f.breite * 100), ...BREITEN_CM])].sort((a, b) => a - b)
              .map((b) => <option key={b} value={b}>{b}{b === Math.round(menue.f.breite * 100) ? " (jetzt)" : ""}</option>)}
          </select></label>
        <label className="grid gap-1">Art
          <select value={menue.typ} onChange={(e) => setMenue({ ...menue, typ: e.target.value })}
            className="rounded border px-1 py-1">
            <option value="">unverändert</option>
            <option value="bruestungsfenster">Brüstung (900 mm)</option>
            <option value="bodentief">Bodentief</option>
          </select></label>
        <label className="grid gap-1">Glasfelder
          <select value={menue.felder} onChange={(e) => setMenue({ ...menue, felder: e.target.value })}
            className="rounded border px-1 py-1">
            <option value="auto">automatisch nach Breite</option>
            {[1, 2, 3, 4].map((n) => <option key={n} value={n}>{n}</option>)}
          </select></label>
        <div className="flex gap-2">
          <button type="button" className="rounded bg-stone-800 px-3 py-1 text-white" onClick={() => {
            const m = menue;
            setMenue(null);
            const aenderung: Record<string, unknown> = { id: m.f.id };
            if (m.breite !== Math.round(m.f.breite * 100)) aenderung.breite = m.breite * 10;
            if (m.typ && m.typ !== (m.f.typ || "")) aenderung.typ = m.typ;
            if (m.felder !== (m.f.felder ? String(m.f.felder) : "auto")) aenderung.felder = m.felder;
            if (Object.keys(aenderung).length > 1) { setInfo("Speichere …"); aendern(aenderung); }
          }}>Übernehmen</button>
          <button type="button" className="rounded border px-3 py-1" onClick={() => setMenue(null)}>Abbrechen</button>
        </div>
      </div>}
      <div className="absolute bottom-3 left-4 text-xs text-stone-600">
        {modus
          ? "Fenster ziehen: entlang der Wand verschieben, rot = fluchtet mit dem Fenster darüber/darunter · Rechtsklick: Breite, Art, Glasfelder · Rad: zoomen."
          : "Ziehen: drehen · Rechts ziehen: verschieben · Rad: zoomen. Gleiche Geometrie wie der Bau, ohne Render."}
      </div>
    </div>
  </main>;
}
