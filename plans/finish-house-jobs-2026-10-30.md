# Finish requested house image jobs, 2026-10-30
Status: AUTHORIZED by repeated user instructions to finish the jobs and upload completed houses.
## Objective
Complete current saved builds and image deliveries for twostorey_xvv1, onehalfstorey_xvv2, twostorey_xvi, twostorey_xvbah and twostorey_xvv2; inspect existing onehalfstorey_xvv1 delivery.
## Current evidence and repository baseline
Workbench HEAD 5be1a4e18956b9fb2e158bee82aa159898356e89. Existing tracked and untracked user changes inspected; preserve them. twostorey_xvv1 has twelve images verified on server (1363-1374), send=false. onehalfstorey_xvv1 already has ten server images. Three remaining builds are stale; twostorey_xvbah build current but handoff absent.
## Exact scope and files
Existing go.py / make-codex-job.py / publish-renders.py workflows, project-specific generated outputs under E:/born2thrill-local-workbench-data/corrections, review catalogs and image-generation prompts. No application code edits.
## Out of scope
Original annotation changes, geometry guessing, changing rights, customer email or --send, deleting user changes.
## Contracts and acceptance
Use current plans, open actual blends, preserve architecture and furniture inventory; image-model styling; visually check whole sets. Native image resolution authorized. Full sets only, verify names and plan_id after upload. Document limitations honestly.
## Tests and verification
Existing build verifier and preflight; input hashes; mesh inventory; image review; complete delivery count; API verification. No new software tests for artifact-only work.
## Risks, rights and external effects
Image model can alter geometry; reject defects. Upload explicitly authorized, rights unchanged. No source geometry publication or customer emails. No changed executable paths bypass corrected-corpus guards; existing verification remains active.
## Rollback
Keep earlier image versions; no source deletions. Server removal requires scoped follow-up if needed.
## Approval
User: 'ok do the rest and upload to server', 'upload fertige Häuser +', 'finish these ... jobs'. Original resolution explicitly approved. No repeated confirmation needed.

## 2026-10-30 - Four house sets uploaded and server bytes verified
- [x] User's repeated instruction to finish all jobs and upload authorizes this delivery; prior onehalfstorey_xvv2 hold superseded by later instruction. Native image dimensions explicitly approved.
- [x] onehalfstorey_xvv2: 10 images, IDs 1375-1384. twostorey_xvi: 12 images, IDs 1385-1396. twostorey_xvbah: 12 images, IDs 1397-1408. twostorey_xvv2: 12 images, IDs 1409-1420.
- [x] All 46 server original PNG SHA256 hashes match finalized local originals; counts, names, correct plan filenames and send=false verified. Complete sets uploaded with existing publish-renders.py; no --send, rights override, customer email, commit or push.
- [x] twostorey_xvv1 previously uploaded 12 images (1363-1374), API rechecked: 12, all send=false. Includes user-requested kitchen gap correction and lowboard against wall.
- [x] Current source blends opened and inventories recorded, input hashes checked; current builds and handoffs produced; all final selected images visually reviewed. Delivery catalogs retain actual dimensions and review evidence. No application code/test changes in this task. Existing unrelated dirty files preserved.
- [ ] Formal image acceptance remains OPEN: visual review is not exact Blender geometry certification. Occluded or ambiguous furniture details are explicitly unverified in catalogs; no invented marker visibility or per-image user approval. Resolve remaining marker/orientation evidence before claiming full contractual acceptance.
- [ ] onehalfstorey_xvv1 existing 10 images remain untouched; API currently returns send=true for all 10, unlike earlier historic notes. This task did not change these flags. Existing child-wardrobe representation/formal review issue remains pending and is not cancelled by this upload.
- Evidence: each delivery folder E:/born2thrill-local-workbench-data/corrections/<plan>/renders/codex-<plan>-2026-10-30 contains catalog.json, upload-verification.json, final original PNGs and retained _work versions. Combined verification: C:/Users/Admin/.codex/visualizations/2026/10/30/01a18d6b-7d8a-7d23-9d05-89e19c6e1e26/upload-verification-all.json.
- Scoped changes: generated image artifacts/catalogs, existing build/handoff outputs, scoped task plan, this roadmap, and 46 server media attachments plus four catalog entries. No executable changes. Full repository status/diff inspected; 17 pre-existing tracked modified files plus extensive untracked work remain.
- Rollback: retain originals and previous versions; attachment IDs above identify this upload. Do not automatically remove remote images or alter existing releases; any rollback must be scoped and separately requested.
2026-10-30 background correction: onehalfstorey_xvv2 dark-modern EG revised with built-in image_gen, background only changed to light neutral grey; house layout and dark interior styling preserved visually. Saved _work/04-floorplan-dark-modern-eg-light-background.png. Prompt: Replace only exterior charcoal backdrop with light neutral grey, preserve house geometry, furniture, camera and interior lighting. Server attachment 1378 is still the prior version; replacement pending. Original retained.
2026-10-30: User found first light background too bright. Built-in image_gen revised dark-modern EG background using warm-modern EG as color reference: cooler darker blue-grey, reduced exterior glow, preserved dark interior. Saved _work/04-floorplan-dark-modern-eg-matched-background-v2.png; previous versions retained. Server replacement remains pending.
- [ ] 2026-10-30: Background consistency rules recorded at user request in born2thrill-local-workbench/plans/BACKGROUND-CONSISTENCY-2026-10-30.md. Next: replace onehalfstorey_xvv2 Dark Modern EG server image with selected corrected version and verify hash, then reconcile main rulebook background wording. No new upload or rulebook modification performed in this documentation step.
- [x] 2026-10-30: Corrected background uploaded with publish-renders.py as ID1421, send=false. Server SHA256 e0010581c998b143ea102feef213a43f6371f819917f43f514271d27e3dcb2b1 matches selected original. Local final/catalog updated, previous image and catalog retained in _work. Server currently has 11 images including old ID1378; no release flags changed. Old image was initially send=true, later observed send=false. Automatic approval review rejected permanent deletion of ID1378 because upload authorization did not explicitly authorize deletion; user approval requested. Pending: remove old image only with approval, then consolidate background rules into main rulebook.

## 2026-10-30: Regel 25 - Serveraustausch abgeschlossen
15 korrigierte Bilder mit publish-renders.py ohne --send hochgeladen (IDs 1422-1436). Alle Serveroriginale per SHA256 gegen die ausgewaehlten Dateien geprueft. Erst danach die 15 ersetzten Serverbilder nach Rainers ausdruecklichem OK entfernt. Endbestaende: onehalfstorey_xvv2 10, twostorey_xvi 12, twostorey_xvbah 12, twostorey_xvv2 12, twostorey_xvv1 12. Zehn Wandkorrekturen und fuenf Haustuerkorrekturen; helle Wandflaechen einschliesslich Wandfliesen und Schnittflaechen, anthrazitfarbene Haustuer, passendes Grau im Hintergrund. Andere Bilder und Freigaben unveraendert. Neue Uploads send=false.
Nachweis: C:\Users\Admin\.codex\visualizations\2026\10\30\01a18d6b-7d8a-7d23-9d05-89e19c6e1e26\rule25-upload-verification.json
Originalsicherungen je Haus: E:\born2thrill-local-workbench-data\corrections\<plan>\renders\codex-<plan>-2026-10-30\_work\before-rule25. Lokale Kataloge und Uploadnachweise aktualisiert. Regel 25 in REGELN.md und Hauptregelbuch dokumentiert; regeln-pruefen.py erfolgreich. Keine Generatoraenderung, kein Commit oder Push. Diese Fertigmeldung ersetzt die offenen Wand-/Tuer-/Hintergrund-Uploadpunkte. Formale Geometrie-/Markerpruefung und der bestehende Kinderzimmer-Schrankpunkt bei onehalfstorey_xvv1 bleiben separat offen; keine neue Architekturfreigabe behauptet.
