"use client";

import { useActionState, useState } from "react";
import { saveQuestionnaire, type SaveState } from "./actions";

const initialState: SaveState = {};

const steps = ["Haus", "Haushalt", "Grundstück", "Räume", "Wohnen", "Prioritäten"];

function Field({
  label,
  name,
  children,
}: {
  label: string;
  name: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={name} className="block text-sm font-medium text-stone-700">
      {label}
      <span className="mt-2 block">{children}</span>
    </label>
  );
}

const inputClass =
  "w-full rounded-xl border border-stone-200 bg-white px-4 py-3 text-stone-900 outline-none transition focus:border-emerald-700 focus:ring-2 focus:ring-emerald-100";

export default function QuestionnaireForm() {
  const [step, setStep] = useState(0);
  const [floors, setFloors] = useState(2);
  const [accessible, setAccessible] = useState(false);
  const [state, action, pending] = useActionState(saveQuestionnaire, initialState);

  if (state.projectId) {
    return (
      <div className="rounded-[2rem] border border-emerald-200 bg-emerald-50 p-8 sm:p-12">
        <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Hausprofil gespeichert</p>
        <h2 className="mt-4 text-3xl font-medium tracking-tight text-emerald-950">
          {state.projectName} ist bereit für den nächsten Schritt.
        </h2>
        <p className="mt-4 max-w-xl leading-7 text-emerald-900/70">
          Die Planungsanforderungen sind sicher gespeichert. Als Nächstes entwickeln wir daraus
          Raumbeziehungen, Randbedingungen und erste Grundrissvarianten.
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-8 rounded-full bg-emerald-950 px-6 py-3 text-sm font-semibold text-white"
        >
          Weiteres Hausprofil anlegen
        </button>
      </div>
    );
  }

  return (
    <form action={action}>
      <div className="mb-9 flex items-center gap-2 overflow-x-auto pb-2">
        {steps.map((label, index) => (
          <button
            key={label}
            type="button"
            onClick={() => index <= step && setStep(index)}
            className={`whitespace-nowrap rounded-full px-4 py-2 text-xs font-semibold transition ${
              index === step
                ? "bg-[#18392f] text-white"
                : index < step
                  ? "bg-emerald-100 text-emerald-900"
                  : "bg-stone-100 text-stone-400"
            }`}
          >
            {index + 1}. {label}
          </button>
        ))}
      </div>

      <div className="min-h-[430px]">
        <section className={step === 0 ? "space-y-6" : "hidden"}>
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Das Vorhaben</p>
              <h2 className="mt-3 text-3xl font-medium tracking-tight">Was möchten Sie bauen?</h2>
            </div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Projektname" name="projectName">
                <input id="projectName" name="projectName" className={inputClass} placeholder="Haus am Garten" />
              </Field>
              <Field label="Gewünschte Wohnfläche (m²)" name="targetArea">
                <input min="60" max="500" type="number" id="targetArea" name="targetArea" defaultValue="145" className={inputClass} />
              </Field>
              <Field label="Oberirdische Geschosse" name="floors">
                <select id="floors" name="floors" value={floors} onChange={(event) => setFloors(Number(event.target.value))} className={inputClass}>
                  <option value="1">1 — Bungalow</option>
                  <option value="2">2 — Klassisches Einfamilienhaus</option>
                  <option value="3">3 — Kompaktes Stadthaus</option>
                </select>
              </Field>
              <Field label="Unterkellerung" name="basement">
                <select id="basement" name="basement" className={inputClass}>
                  <option value="none">Nicht unterkellert</option>
                  <option value="partial">Teilunterkellert</option>
                  <option value="full">Voll unterkellert</option>
                  <option value="undecided">Noch offen</option>
                </select>
              </Field>
              <Field label="Architektonischer Charakter" name="constructionStyle">
                <select id="constructionStyle" name="constructionStyle" className={inputClass}>
                  <option value="timeless-modern">Zeitlos modern</option>
                  <option value="regional">Regional / traditionell</option>
                  <option value="minimal">Reduziert und zeitgenössisch</option>
                  <option value="natural">Warm und natürlich</option>
                </select>
              </Field>
              <Field label="Dachform" name="roofPreference">
                <select id="roofPreference" name="roofPreference" className={inputClass}>
                  <option value="undecided">Vom Grundstück und Baurecht abhängig</option>
                  <option value="gable">Satteldach</option>
                  <option value="hipped">Walmdach</option>
                  <option value="flat">Flachdach</option>
                </select>
              </Field>
            </div>
        </section>

        <section className={step === 1 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Die Menschen</p><h2 className="mt-3 text-3xl font-medium tracking-tight">Für wen soll das Haus funktionieren?</h2></div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Erwachsene" name="adults"><input id="adults" name="adults" type="number" min="1" max="8" defaultValue="2" className={inputClass} /></Field>
              <Field label="Kinder" name="children"><input id="children" name="children" type="number" min="0" max="8" defaultValue="2" className={inputClass} /></Field>
              <Field label="Barrierearmes Wohnen berücksichtigen?" name="accessibility">
                <select id="accessibility" name="accessibility" className={inputClass} onChange={(event) => setAccessible(event.target.value === "yes")}>
                  <option value="no">Nicht erforderlich</option><option value="yes">Ja, jetzt oder zukünftig</option>
                </select>
              </Field>
              {accessible && floors > 1 && (
                <div className="rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-900">
                  Wir berücksichtigen Platz für einen späteren Aufzug oder eine großzügige Treppengeometrie und ordnen wichtige Räume im Erdgeschoss an.
                </div>
              )}
            </div>
        </section>

        <section className={step === 2 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Der Ort</p><h2 className="mt-3 text-3xl font-medium tracking-tight">Wie liegt das Grundstück zur Sonne?</h2></div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Bundesland" name="bundesland"><input id="bundesland" name="bundesland" className={inputClass} placeholder="z. B. Hessen" /></Field>
              <Field label="Gemeinde / Ort" name="municipality"><input id="municipality" name="municipality" className={inputClass} placeholder="z. B. Wiesbaden" /></Field>
              <Field label="Straßenseite zeigt nach" name="streetDirection"><select id="streetDirection" name="streetDirection" className={inputClass}><option>Nord</option><option>Ost</option><option>Süd</option><option>West</option><option>Unbekannt</option></select></Field>
              <Field label="Bevorzugte Gartenseite" name="gardenDirection"><select id="gardenDirection" name="gardenDirection" className={inputClass}><option>Süd</option><option>Südwest</option><option>West</option><option>Ost</option><option>Vom Grundstück abhängig</option></select></Field>
            </div>
            <p className="rounded-xl bg-stone-100 p-4 text-sm leading-6 text-stone-600">Später ermöglicht ein Lageplan-Upload die Prüfung von Grundstücksgrenzen, Abstandsflächen, Zufahrt, Nachbarbebauung und Bebauungsplan.</p>
        </section>

        <section className={step === 3 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Das Raumprogramm</p><h2 className="mt-3 text-3xl font-medium tracking-tight">Welche Räume werden wirklich gebraucht?</h2></div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Schlafzimmer" name="bedrooms"><input id="bedrooms" name="bedrooms" type="number" min="1" max="8" defaultValue="3" className={inputClass} /></Field>
              <Field label="Bäder mit Dusche oder Wanne" name="bathrooms"><input id="bathrooms" name="bathrooms" type="number" min="1" max="5" defaultValue="2" className={inputClass} /></Field>
              <Field label="Separates Gäste-WC" name="guestWc"><select id="guestWc" name="guestWc" className={inputClass}><option value="yes">Ja</option><option value="no">Nein</option></select></Field>
              <Field label="Eigenes Arbeitszimmer" name="office"><select id="office" name="office" className={inputClass}><option value="yes">Ja</option><option value="no">Nein</option></select></Field>
              <Field label="Hauswirtschafts- / Technikraum" name="utilityRoom"><select id="utilityRoom" name="utilityRoom" className={inputClass}><option value="yes">Ja</option><option value="no">Nein</option></select></Field>
              <Field label="Schlafmöglichkeit im Erdgeschoss" name="groundFloorSleeping"><select id="groundFloorSleeping" name="groundFloorSleeping" className={inputClass}><option value="no">Nicht erforderlich</option><option value="yes">Ja — Schlafzimmer oder flexibel nutzbarer Raum</option></select></Field>
            </div>
        </section>

        <section className={step === 4 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Der Alltag</p><h2 className="mt-3 text-3xl font-medium tracking-tight">Wie soll sich das Wohnen anfühlen?</h2></div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Küche und Wohnbereich" name="kitchen"><select id="kitchen" name="kitchen" className={inputClass}><option value="open">Offen zu Wohnen und Essen</option><option value="semi-open">Halboffen / abtrennbar</option><option value="separate">Separate Küche</option></select></Field>
              <Field label="Bezug zum Garten" name="gardenConnection"><select id="gardenConnection" name="gardenConnection" className={inputClass}><option value="generous">Großzügige Verglasung und Terrasse</option><option value="balanced">Ausgewogenes Verhältnis von Licht und Privatsphäre</option><option value="private">Mehr Rückzug, gezielte Ausblicke</option></select></Field>
              {floors > 1 && <Field label="Treppenwunsch" name="stairPreference"><select id="stairPreference" name="stairPreference" className={inputClass}><option value="central">Zentral und flächeneffizient</option><option value="feature">Als prägendes Architekturelement</option><option value="separable">Später abtrennbar</option><option value="undecided">Keine Präferenz</option></select></Field>}
            </div>
        </section>

        <section className={step === 5 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Der Kompass</p><h2 className="mt-3 text-3xl font-medium tracking-tight">Was muss der Entwurf besonders berücksichtigen?</h2></div>
            <div className="grid gap-3 sm:grid-cols-2">
              {["Tageslicht", "Gartenbezug", "Kompakte Baukosten", "Privatsphäre", "Flexible Räume", "Energieeffizienz"].map((priority) => (
                <label key={priority} className="flex items-center gap-3 rounded-xl border border-stone-200 bg-white p-4 text-sm font-medium"><input type="checkbox" name="priorities" value={priority} className="size-4 accent-emerald-800" />{priority}</label>
              ))}
            </div>
            <Field label="Was sollte der Entwurf außerdem berücksichtigen?" name="notes"><textarea id="notes" name="notes" rows={4} className={inputClass} placeholder="Ausblicke, Hobbys, Möbel, spätere Veränderungen …" /></Field>
        </section>
      </div>

      {state.error && <p className="mt-6 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{state.error}</p>}
      <div className="mt-8 flex items-center justify-between border-t border-stone-200 pt-6">
        <button type="button" disabled={step === 0} onClick={() => setStep((value) => value - 1)} className="rounded-full px-5 py-3 text-sm font-semibold text-stone-600 disabled:opacity-30">Zurück</button>
        {step < steps.length - 1 ? (
          <button type="button" onClick={() => setStep((value) => value + 1)} className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white hover:bg-[#245446]">Weiter</button>
        ) : (
          <button disabled={pending} type="submit" className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white disabled:opacity-50">{pending ? "Wird gespeichert …" : "Hausprofil speichern"}</button>
        )}
      </div>
    </form>
  );
}
