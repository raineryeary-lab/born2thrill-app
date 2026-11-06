"use client";

/**
 * 3D-Vorschau des Hauses von aussen, vor dem Bau (vorschau-3d-v1).
 *
 * Rainer, 2026-11-03: "WOULD IT BE SUPER HARD TO DO A 3D PREVIEW OF SOME SORT
 * of the outside before we really go into the build?" Gezeigt wird die GLB,
 * die /api/floorplan-workbench/vorschau-3d aus dem echten Bau schreibt --
 * dieselben Waende, Oeffnungen und Daecher wie im Aussenbild, nur drehbar.
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

export default function Vorschau3d() {
  const buehne = useRef<HTMLDivElement | null>(null);
  const welt = useRef<{ scene: THREE.Scene; camera: THREE.PerspectiveCamera; controls: OrbitControls; haus: THREE.Object3D | null } | null>(null);
  const [plan, setPlan] = useState("");
  const [daecher, setDaecher] = useState<string[]>([]);
  const [dach, setDach] = useState("");
  const [status, setStatus] = useState("Lädt …");
  const [laeuft, setLaeuft] = useState(false);

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
    welt.current = { scene, camera, controls, haus: null };
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
    return () => {
      cancelAnimationFrame(bild);
      window.removeEventListener("resize", groesse);
      controls.dispose();
      renderer.dispose();
      el.removeChild(renderer.domElement);
    };
  }, []);

  async function laden(p: string, d: string) {
    const w = welt.current;
    if (!w) return;
    setStatus(`${DACH_NAMEN[d] || d} wird geladen …`);
    const gltf = await new GLTFLoader().loadAsync(
      `/api/floorplan-workbench/vorschau-3d?plan=${encodeURIComponent(p)}&dach=${encodeURIComponent(d)}&t=${Date.now()}`);
    if (w.haus) w.scene.remove(w.haus);
    w.haus = gltf.scene;
    w.scene.add(gltf.scene);
    // Kamera auf das Haus: 3/4-Ansicht, ganzes Gebaeude.
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const mitte = box.getCenter(new THREE.Vector3());
    const groesse = box.getSize(new THREE.Vector3()).length();
    w.controls.target.copy(mitte);
    w.camera.position.copy(mitte).add(new THREE.Vector3(0.7, 0.45, 0.7).multiplyScalar(groesse * 0.9));
    w.camera.near = groesse / 200;
    w.camera.far = groesse * 20;
    w.camera.updateProjectionMatrix();
    setStatus("");
  }

  async function bauen(p: string, d: string) {
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
      await laden(p, ergebnis.dach);
    } finally {
      setLaeuft(false);
    }
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
      <button type="button" disabled={laeuft || !plan} onClick={() => bauen(plan, dach)}
        className="ml-auto rounded bg-stone-800 px-3 py-1 text-white disabled:opacity-50">↻ Neu bauen</button>
    </div>
    <div className="relative flex-1">
      <div ref={buehne} className="absolute inset-0" />
      {status && <div className="absolute left-4 top-4 rounded bg-white/90 px-3 py-2 text-sm shadow">{status}</div>}
      <div className="absolute bottom-3 left-4 text-xs text-stone-600">
        Ziehen: drehen · Rechts ziehen: verschieben · Rad: zoomen. Gleiche Geometrie wie der Bau, ohne Render.
      </div>
    </div>
  </main>;
}
