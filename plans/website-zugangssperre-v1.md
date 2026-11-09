# website-zugangssperre-v1

Rainer, 2026-11-08: "can we make the whole born2thrill password protected but then
everything visible? kss2026 for user and password frontend only" -> "do it please".

## Umfang
- Neues Code-Snippet "Website-Zugangssperre (kss2026)" auf born2thrill.de, Quelle
  `wordpress/website-zugangssperre.php`.
- Jede Frontend-Seite (template_redirect) zeigt ohne Zugang eine Anmeldeseite
  (Benutzer + Passwort kss2026). Richtig -> Cookie 30 Tage, dann alles sichtbar.
- Frei bleiben: eingeloggte WordPress-Nutzer, wp-admin, wp-login.php, wp-json
  (REST, unsere Skripte mit App-Passwort), admin-ajax, cron.
- Kein HTTP-Basic-Auth (kollidiert mit dem App-Passwort-Header der REST-Skripte).

## Nicht im Umfang
Medien-Dateien und REST-Daten bleiben direkt abrufbar. Keine Freigabe, keine E-Mail,
kein `approved`.

## Test
Ohne Cookie -> Anmeldeseite (401, noindex). Falsches Passwort -> Fehlertext.
Richtig -> Weiterleitung + Cookie -> Seite normal. wp-json/b2t/v1/grundrisse ohne
Cookie 200. Code-Snippets-API mit App-Passwort weiter 200.

## Rueckweg
Snippet in Code Snippets deaktivieren (sofort wirksam).

## Sicherheitsfrage
Kann ein geaenderter Pfad Geometrie ohne freigegebene Referenz erzeugen,
veroeffentlichen oder mailen? Nein: das Snippet gibt nur eine Anmeldeseite aus.
