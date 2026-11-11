# Countdown über dem Grundriss-Katalog

Status: DONE, LIVE 2026-11-07 (Snippet 11)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "could you add this list to the grundrisskatalog? towards the top so i can countdown?"
"This list" = the build/status list (which houses are finished, which are still open, and why).

## Proposal

- New generator `scripts/katalog-countdown-snippet.py`:
  - reads the house list from the Workbench (`localhost:3020/api/floorplan-workbench/state`, the same states as /haus);
  - writes `wordpress/katalog-countdown.php`.
- The snippet shows a box above the filters on the Grundriss-Katalog:
  - "X von N fertig – noch Y", with a progress bar;
  - below it, one row per open step (count + house names, unfolds on click);
  - clicking a house name puts it into the catalogue's name filter.
- **Visible only to logged-in users with `edit_posts`** (Rainer/boss), never to customers.
- The data is a snapshot taken when the generator runs. Refresh = rerun the generator and replace the snippet.
- Snippets 9 and 10 stay untouched.

## Tests (first)

`scripts/katalog_countdown_snippet.test.py`:
- grouping and order of the steps;
- the counts;
- the admin check (`current_user_can`) is in the PHP;
- no backslash, backtick or `${` in the output (needed for the editor method).

## Rights / external effects

- Only a display for logged-in editors. Nothing is approved, nothing is uploaded, nothing is sent.
- Live goes via a new Code Snippet, only after Rainer's OK on the preview (rule 8: show an example first).

## Rollback

Deactivate or delete the snippet.

## Live

- Snippet 11 „Katalog-Countdown (nur Bearbeiter)“, SHA 886193e23de5 = local file, created and activated.
- Live, logged in: 119 von 270 fertig, noch 151 (14 ausrichten / 29 bauen / 108 Codex-Bilder).
  - Clicking a house name fills the name filter: twostorey_2_familien → 1 house.
- Logged out the page HTML has no countdown.
- Refresh: `python scripts/katalog-countdown-snippet.py`, then replace the code in Snippet 11.
- Follow-up: /haus shows 108 houses as „Bilder freigeben“ because the uploaded floor-plan image counts as a catalogue image. In truth the Codex images are missing there.
