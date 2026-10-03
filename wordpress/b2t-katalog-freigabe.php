<?php
/**
 * Plugin Name: B2T Katalog-Freigabe
 * Description: Die eine fehlende Route: einen Grundriss im Katalog sichtbar machen.
 * Version:     1.0.0
 *
 * WARUM ES DAS GIBT
 *
 * Das Katalog-Plugin kann Bilder hochladen (wp/v2/media), sie pro Bild
 * anhaken (b2t/v1/freigabe) und Blender-Pfade speichern (b2t/v1/pfade).
 * Was es NICHT kann: am Grundriss selbst `bilder` und `approved` setzen.
 * Genau diese zwei Spalten entscheiden aber, ob ein Haus im Katalog erscheint.
 *
 * Gemessen am 2026-08-20: bungalow_039 hatte 9 Bilder in der Mediathek, alle
 * neun angehakt, Blender-Pfade eingetragen -- und stand trotzdem auf `im: 0,
 * ok: offen`. Von 310 Grundrissen war genau EINER freigegeben, und der war es
 * von Hand. Deshalb blieb der Ablauf auf dem letzten Schritt stehen, egal wie
 * viel davor stimmte.
 *
 * EINBAUEN
 *
 *   Diese Datei nach wp-content/mu-plugins/ hochladen. Fertig -- mu-plugins
 *   werden ohne Aktivierung geladen. (Gibt es den Ordner nicht: anlegen.)
 *
 * DANACH
 *
 *   python freigeben.py bungalow_039
 *
 * SICHERHEIT
 *
 *   Verlangt `edit_posts` -- dieselbe Anmeldung wie der Upload
 *   (Application Password). Ohne Anmeldung passiert nichts.
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('rest_api_init', function () {
    register_rest_route('b2t/v1', '/katalog', [
        'methods'             => 'POST',
        'permission_callback' => function () {
            return current_user_can('edit_posts');
        },
        'args' => [
            'plan'     => ['required' => true,  'type' => 'string'],
            'bilder'   => ['required' => false, 'type' => 'integer'],
            'approved' => ['required' => false, 'type' => 'string'],
        ],
        'callback' => 'b2t_katalog_freigeben',
    ]);
});

function b2t_katalog_freigeben($request)
{
    global $wpdb;

    $plan = sanitize_text_field((string) $request->get_param('plan'));
    if ($plan === '' || !preg_match('/^[A-Za-z0-9_.\-]+$/', $plan)) {
        return new WP_Error('b2t_plan', 'Plan fehlt oder enthaelt unerlaubte Zeichen.',
                            ['status' => 400]);
    }

    // Auf born2thrill.de ist $wpdb->prefix bereits 'kon_' -- ein fest
    // angehaengtes 'kon_grundrisse' ergab dort 'kon_kon_grundrisse'
    // (gemessen 2026-08-22, Katalog-Route 500). Deshalb: Kandidaten
    // durchprobieren, ersten existierenden nehmen.
    $tabelle = null;
    foreach ([$wpdb->prefix . 'grundrisse',
              $wpdb->prefix . 'kon_grundrisse',
              'kon_grundrisse'] as $kandidat) {
        if ($wpdb->get_var($wpdb->prepare('SHOW TABLES LIKE %s', $kandidat)) === $kandidat) {
            $tabelle = $kandidat;
            break;
        }
    }
    if ($tabelle === null) {
        return new WP_Error('b2t_tabelle', 'Keine Grundriss-Tabelle gefunden '
                            . '(gesucht: *grundrisse mit Prefix ' . $wpdb->prefix . ').',
                            ['status' => 500]);
    }

    $zeile = $wpdb->get_row($wpdb->prepare(
        "SELECT id, bilder, approved FROM {$tabelle} WHERE plan_id = %s", $plan));
    if (!$zeile) {
        return new WP_Error('b2t_unbekannt', 'Kein Grundriss mit plan_id ' . $plan,
                            ['status' => 404]);
    }

    // Die Anzahl kommt vom Aufrufer, weil er die Mediathek ohnehin gerade
    // gezaehlt hat. Fehlt sie, bleibt der bisherige Wert stehen -- diese Route
    // setzt nur, was ihr ausdruecklich gesagt wurde.
    $daten  = [];
    $format = [];

    $bilder = $request->get_param('bilder');
    if ($bilder !== null) {
        $daten['bilder'] = max(0, (int) $bilder);
        $format[]        = '%d';
    }

    $approved = $request->get_param('approved');
    if ($approved !== null) {
        $approved = strtolower(trim((string) $approved));
        if (!in_array($approved, ['ja', 'offen'], true)) {
            return new WP_Error('b2t_approved', 'approved muss "ja" oder "offen" sein.',
                                ['status' => 400]);
        }
        $daten['approved'] = $approved;
        $format[]          = '%s';
    }

    if (!$daten) {
        return new WP_Error('b2t_leer', 'Weder bilder noch approved angegeben.',
                            ['status' => 400]);
    }

    $wpdb->update($tabelle, $daten, ['plan_id' => $plan], $format, ['%s']);
    if ($wpdb->last_error) {
        return new WP_Error('b2t_db', $wpdb->last_error, ['status' => 500]);
    }

    // Zurueckgemeldet wird, was danach WIRKLICH in der Zeile steht, nicht was
    // geschickt wurde.
    $danach = $wpdb->get_row($wpdb->prepare(
        "SELECT bilder, approved FROM {$tabelle} WHERE plan_id = %s", $plan));

    return [
        'ok'       => true,
        'plan'     => $plan,
        'vorher'   => ['bilder' => (int) $zeile->bilder,  'approved' => $zeile->approved],
        'jetzt'    => ['bilder' => (int) $danach->bilder, 'approved' => $danach->approved],
    ];
}
