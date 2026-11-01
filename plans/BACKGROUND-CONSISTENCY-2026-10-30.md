# Dollhouse background consistency - requested rule update
Date: 2026-10-30
Status: Recorded at user request. Merge into main render rules after revised image upload and verification; main rulebook not changed yet.

## Rules to carry forward
1. Keep the exterior studio background consistent across all interior styles of the same house. Dark Modern changes the interior palette, not the background to charcoal or black.
2. Match background brightness, hue and gradient against an existing companion image from the same delivery. Include that image as a background-only reference in the edit prompt.
3. Do not replace a dark background with bright white or an excessively pale backdrop. The first correction was rejected as too light compared with the other images.
4. For this set, match the companion image's cooler grey. Reference matching takes precedence over an invented fixed colour value; do not add an arbitrary blue cast.
5. Retain natural soft contact/window shadows. Avoid excessive white halos and strong warm light spill outside the house footprint.
6. A background correction must preserve the house: camera, crop, walls, doors, windows, stairs, furniture, bathroom fixtures, materials and interior lighting. Check the output visually against the source for drift.
7. Compare the corrected image with its companion before uploading. Preserve prior versions and record the chosen original file and hash. Verify the uploaded server original against that hash; do not report a local correction as already uploaded.

## Concrete reference and pending work
House: onehalfstorey_xvv2, Dark Modern EG.
Background reference: renders/codex-onehalfstorey_xvv2-2026-10-30/03-floorplan-warm-modern-eg.png.
Latest correction: renders/codex-onehalfstorey_xvv2-2026-10-30/_work/04-floorplan-dark-modern-eg-matched-background-v2.png.
The latest correction has been shown; no separate explicit approval is claimed.
Server attachment 1378 still contains the earlier dark-background image. Replacement and hash verification remain pending. Keep the set at ten images, without adding a duplicate gallery entry or changing send/release flags.
After upload verification, reconcile these notes with docs/CODEX-REGELN-4PLUS2.md, particularly its white-background wording and background check. Do not silently treat the older white-background wording as the current visual target for this set.
- [x] 2026-10-30: Corrected background uploaded with publish-renders.py as ID1421, send=false. Server SHA256 e0010581c998b143ea102feef213a43f6371f819917f43f514271d27e3dcb2b1 matches selected original. Local final/catalog updated, previous image and catalog retained in _work. Server currently has 11 images including old ID1378; no release flags changed. Old image was initially send=true, later observed send=false. Automatic approval review rejected permanent deletion of ID1378 because upload authorization did not explicitly authorize deletion; user approval requested. Pending: remove old image only with approval, then consolidate background rules into main rulebook.
- [ ] 2026-10-30: Exterior wall brightness corrections generated with built-in image_gen: twostorey_xvi/_work/06-floorplan-dark-modern-eg-light-facade-v2.png (source local final), onehalfstorey_xvv2/_work/08-floorplan-dark-modern-og-light-facade-preview.png (source user attached image). Both stored under respective delivery folders. Neither uploaded yet. OG attachment differs from current final in bathroom sink position; reconcile before replacing server final, do not silently undo earlier fixture correction. Exterior wall light plaster requirement recorded; main rule update remains pending.
2026-10-30 binding correction: ALL wall surfaces light (interior, exterior, cut tops); entrance door ANTHRACITE in every style. User expressly confirmed both. Recorded in REGELN.md rule25. Eight affected dark-modern corrections being generated; four older xvv1 images already have light plaster walls. Front-door consistency across other styles must also be checked. No existing server image deletion authorized; earlier auto-review deletion rejection remains in force.

2026-10-30: Standing rules consolidated into REGELN.md rule25 and main CODEX-REGELN-4PLUS2.md. All wall faces light, anthracite entrance doors, background matched to set. No generator code or make-codex-job.py changed. User explicitly approved permanent removal of superseded server copies AFTER corrected uploads are verified (reply: ok).

## 2026-10-30: Regel 25 - Serveraustausch abgeschlossen
15 korrigierte Bilder mit publish-renders.py ohne --send hochgeladen (IDs 1422-1436). Alle Serveroriginale per SHA256 gegen die ausgewaehlten Dateien geprueft. Erst danach die 15 ersetzten Serverbilder nach Rainers ausdruecklichem OK entfernt. Endbestaende: onehalfstorey_xvv2 10, twostorey_xvi 12, twostorey_xvbah 12, twostorey_xvv2 12, twostorey_xvv1 12. Zehn Wandkorrekturen und fuenf Haustuerkorrekturen; helle Wandflaechen einschliesslich Wandfliesen und Schnittflaechen, anthrazitfarbene Haustuer, passendes Grau im Hintergrund. Andere Bilder und Freigaben unveraendert. Neue Uploads send=false.
Nachweis: C:\Users\Admin\.codex\visualizations\2026\10\30\01a18d6b-7d8a-7d23-9d05-89e19c6e1e26\rule25-upload-verification.json
Originalsicherungen je Haus: E:\born2thrill-local-workbench-data\corrections\<plan>\renders\codex-<plan>-2026-10-30\_work\before-rule25. Lokale Kataloge und Uploadnachweise aktualisiert. Regel 25 in REGELN.md und Hauptregelbuch dokumentiert; regeln-pruefen.py erfolgreich. Keine Generatoraenderung, kein Commit oder Push. Diese Fertigmeldung ersetzt die offenen Wand-/Tuer-/Hintergrund-Uploadpunkte. Formale Geometrie-/Markerpruefung und der bestehende Kinderzimmer-Schrankpunkt bei onehalfstorey_xvv1 bleiben separat offen; keine neue Architekturfreigabe behauptet.
