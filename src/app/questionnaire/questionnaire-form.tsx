"use client";

import { useActionState, useState } from "react";
import { saveQuestionnaire, type SaveState } from "./actions";

const initialState: SaveState = {};

const steps = ["Home", "Household", "Site", "Rooms", "Living", "Priorities"];

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
        <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Brief saved</p>
        <h2 className="mt-4 text-3xl font-medium tracking-tight text-emerald-950">
          {state.projectName} is ready for the next step.
        </h2>
        <p className="mt-4 max-w-xl leading-7 text-emerald-900/70">
          The planning requirements are safely stored. Next we can turn this brief into
          room relationships, constraints, and the first floor-plan candidates.
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-8 rounded-full bg-emerald-950 px-6 py-3 text-sm font-semibold text-white"
        >
          Start another brief
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
              <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">The ambition</p>
              <h2 className="mt-3 text-3xl font-medium tracking-tight">What are we designing?</h2>
            </div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Project name" name="projectName">
                <input id="projectName" name="projectName" className={inputClass} placeholder="Haus am Garten" />
              </Field>
              <Field label="Target living area (m²)" name="targetArea">
                <input min="60" max="500" type="number" id="targetArea" name="targetArea" defaultValue="145" className={inputClass} />
              </Field>
              <Field label="Floors above ground" name="floors">
                <select id="floors" name="floors" value={floors} onChange={(event) => setFloors(Number(event.target.value))} className={inputClass}>
                  <option value="1">1 — Bungalow</option>
                  <option value="2">2 — Typical family house</option>
                  <option value="3">3 — Compact urban house</option>
                </select>
              </Field>
              <Field label="Basement" name="basement">
                <select id="basement" name="basement" className={inputClass}>
                  <option value="none">No basement</option>
                  <option value="partial">Partial basement</option>
                  <option value="full">Full basement</option>
                  <option value="undecided">Not decided</option>
                </select>
              </Field>
              <Field label="Architectural character" name="constructionStyle">
                <select id="constructionStyle" name="constructionStyle" className={inputClass}>
                  <option value="timeless-modern">Timeless modern</option>
                  <option value="regional">Regional / traditional</option>
                  <option value="minimal">Minimal contemporary</option>
                  <option value="natural">Warm and natural</option>
                </select>
              </Field>
              <Field label="Roof preference" name="roofPreference">
                <select id="roofPreference" name="roofPreference" className={inputClass}>
                  <option value="undecided">Let the site decide</option>
                  <option value="gable">Gable roof / Satteldach</option>
                  <option value="hipped">Hipped roof / Walmdach</option>
                  <option value="flat">Flat roof / Flachdach</option>
                </select>
              </Field>
            </div>
        </section>

        <section className={step === 1 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">The people</p><h2 className="mt-3 text-3xl font-medium tracking-tight">Who should the house work for?</h2></div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Adults" name="adults"><input id="adults" name="adults" type="number" min="1" max="8" defaultValue="2" className={inputClass} /></Field>
              <Field label="Children" name="children"><input id="children" name="children" type="number" min="0" max="8" defaultValue="2" className={inputClass} /></Field>
              <Field label="Plan for step-free living?" name="accessibility">
                <select id="accessibility" name="accessibility" className={inputClass} onChange={(event) => setAccessible(event.target.value === "yes")}>
                  <option value="no">Not essential</option><option value="yes">Yes, now or in the future</option>
                </select>
              </Field>
              {accessible && floors > 1 && (
                <div className="rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-900">
                  We will reserve space for a future lift or a generous stair geometry and keep essential rooms on the ground floor.
                </div>
              )}
            </div>
        </section>

        <section className={step === 2 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">The place</p><h2 className="mt-3 text-3xl font-medium tracking-tight">How does the plot meet the sun?</h2></div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Bundesland" name="bundesland"><input id="bundesland" name="bundesland" className={inputClass} placeholder="e.g. Hessen" /></Field>
              <Field label="Municipality / town" name="municipality"><input id="municipality" name="municipality" className={inputClass} placeholder="e.g. Wiesbaden" /></Field>
              <Field label="Street side faces" name="streetDirection"><select id="streetDirection" name="streetDirection" className={inputClass}><option>North</option><option>East</option><option>South</option><option>West</option><option>Unknown</option></select></Field>
              <Field label="Preferred garden side" name="gardenDirection"><select id="gardenDirection" name="gardenDirection" className={inputClass}><option>South</option><option>South-west</option><option>West</option><option>East</option><option>Let the plot decide</option></select></Field>
            </div>
            <p className="rounded-xl bg-stone-100 p-4 text-sm leading-6 text-stone-600">Later, a site-plan upload will let us check actual boundaries, setbacks, access, neighbouring buildings, and the Bebauungsplan.</p>
        </section>

        <section className={step === 3 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">The programme</p><h2 className="mt-3 text-3xl font-medium tracking-tight">Which rooms earn their place?</h2></div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Bedrooms" name="bedrooms"><input id="bedrooms" name="bedrooms" type="number" min="1" max="8" defaultValue="3" className={inputClass} /></Field>
              <Field label="Full bathrooms" name="bathrooms"><input id="bathrooms" name="bathrooms" type="number" min="1" max="5" defaultValue="2" className={inputClass} /></Field>
              <Field label="Separate guest WC" name="guestWc"><select id="guestWc" name="guestWc" className={inputClass}><option value="yes">Yes</option><option value="no">No</option></select></Field>
              <Field label="Dedicated home office" name="office"><select id="office" name="office" className={inputClass}><option value="yes">Yes</option><option value="no">No</option></select></Field>
              <Field label="Utility / technical room" name="utilityRoom"><select id="utilityRoom" name="utilityRoom" className={inputClass}><option value="yes">Yes</option><option value="no">No</option></select></Field>
              <Field label="Ground-floor sleeping option" name="groundFloorSleeping"><select id="groundFloorSleeping" name="groundFloorSleeping" className={inputClass}><option value="no">Not needed</option><option value="yes">Yes — bedroom or flexible room</option></select></Field>
            </div>
        </section>

        <section className={step === 4 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Daily life</p><h2 className="mt-3 text-3xl font-medium tracking-tight">How should the house feel to live in?</h2></div>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="Kitchen relationship" name="kitchen"><select id="kitchen" name="kitchen" className={inputClass}><option value="open">Open to living and dining</option><option value="semi-open">Semi-open / closable</option><option value="separate">Separate kitchen</option></select></Field>
              <Field label="Connection to garden" name="gardenConnection"><select id="gardenConnection" name="gardenConnection" className={inputClass}><option value="generous">Generous glazing and terrace</option><option value="balanced">Balanced light and privacy</option><option value="private">More private, framed views</option></select></Field>
              {floors > 1 && <Field label="Stair preference" name="stairPreference"><select id="stairPreference" name="stairPreference" className={inputClass}><option value="central">Central and efficient</option><option value="feature">Architectural feature stair</option><option value="separable">Can be separated later</option><option value="undecided">No preference</option></select></Field>}
            </div>
        </section>

        <section className={step === 5 ? "space-y-6" : "hidden"}>
            <div><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">The compass</p><h2 className="mt-3 text-3xl font-medium tracking-tight">What must the design protect?</h2></div>
            <div className="grid gap-3 sm:grid-cols-2">
              {["Daylight", "Garden connection", "Compact building cost", "Privacy", "Flexible rooms", "Energy efficiency"].map((priority) => (
                <label key={priority} className="flex items-center gap-3 rounded-xl border border-stone-200 bg-white p-4 text-sm font-medium"><input type="checkbox" name="priorities" value={priority} className="size-4 accent-emerald-800" />{priority}</label>
              ))}
            </div>
            <Field label="Anything else the concept should know?" name="notes"><textarea id="notes" name="notes" rows={4} className={inputClass} placeholder="Views to preserve, hobbies, furniture, future changes…" /></Field>
        </section>
      </div>

      {state.error && <p className="mt-6 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{state.error}</p>}
      <div className="mt-8 flex items-center justify-between border-t border-stone-200 pt-6">
        <button type="button" disabled={step === 0} onClick={() => setStep((value) => value - 1)} className="rounded-full px-5 py-3 text-sm font-semibold text-stone-600 disabled:opacity-30">Back</button>
        {step < steps.length - 1 ? (
          <button type="button" onClick={() => setStep((value) => value + 1)} className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white hover:bg-[#245446]">Continue</button>
        ) : (
          <button disabled={pending} type="submit" className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white disabled:opacity-50">{pending ? "Saving…" : "Save house brief"}</button>
        )}
      </div>
    </form>
  );
}
