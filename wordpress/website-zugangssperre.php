<?php
/**
 * Website-Zugangssperre (website-zugangssperre-v1).
 * Rainer, 2026-11-08: ganze Website mit Benutzer + Passwort kss2026, danach alles sichtbar.
 * Nur Frontend: wp-admin, wp-login.php, wp-json, admin-ajax und cron bleiben frei,
 * eingeloggte WordPress-Nutzer kommen ohne Abfrage durch.
 * Abschalten: Snippet in Code Snippets deaktivieren.
 * Offen-Modus (Rainer, 2026-11-08): B2T_ZUGANG_OFFEN = true -> keine Sperre, und alle
 * sehen die Teamfelder (Countdown, Preistabelle). Wieder sperren: auf false setzen.
 */
if ( ! defined( 'B2T_ZUGANG_OFFEN' ) ) {
	define( 'B2T_ZUGANG_OFFEN', false );
}
function b2t_zugang_marke() {
	return hash_hmac( 'sha256', 'kss2026|kss2026', wp_salt( 'auth' ) );
}

/** Mit dem Website-Zugang angemeldet (Team)? Nutzt auch die Preistabelle (Snippet 12). */
function b2t_zugang_ok() {
	if ( B2T_ZUGANG_OFFEN ) {
		return true;
	}
	return isset( $_COOKIE['b2t_zugang'] ) && hash_equals( b2t_zugang_marke(), (string) $_COOKIE['b2t_zugang'] );
}

add_action( 'template_redirect', function () {
	if ( B2T_ZUGANG_OFFEN || is_user_logged_in() || wp_doing_ajax() || wp_doing_cron() || defined( 'REST_REQUEST' ) ) {
		return;
	}
	$benutzer = 'kss2026';
	$passwort = 'kss2026';
	$keks     = 'b2t_zugang';
	$marke    = b2t_zugang_marke();
	if ( b2t_zugang_ok() ) {
		return;
	}
	$fehler = false;
	if ( 'POST' === ( $_SERVER['REQUEST_METHOD'] ?? '' ) && isset( $_POST['b2t_zugang_benutzer'] ) ) {
		$b = (string) wp_unslash( $_POST['b2t_zugang_benutzer'] );
		$p = (string) wp_unslash( $_POST['b2t_zugang_passwort'] ?? '' );
		if ( hash_equals( $benutzer, trim( $b ) ) && hash_equals( $passwort, $p ) ) {
			setcookie( $keks, $marke, array(
				'expires'  => time() + 30 * DAY_IN_SECONDS,
				'path'     => '/',
				'secure'   => is_ssl(),
				'httponly' => true,
				'samesite' => 'Lax',
			) );
			$ziel = ( is_ssl() ? 'https://' : 'http://' ) . ( $_SERVER['HTTP_HOST'] ?? '' ) . ( $_SERVER['REQUEST_URI'] ?? '/' );
			wp_safe_redirect( $ziel, 303 );
			exit;
		}
		$fehler = true;
	}
	nocache_headers();
	status_header( 401 );
	header( 'X-Robots-Tag: noindex, nofollow' );
	header( 'Content-Type: text/html; charset=utf-8' );
	$name = esc_html( get_bloginfo( 'name' ) );
	?><!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title><?php echo $name; ?> – Anmeldung</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#ececea;font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;color:#222}
form{background:#fff;padding:32px 28px;border-radius:10px;box-shadow:0 2px 16px rgba(0,0,0,.08);width:100%;max-width:320px;margin:16px}
h1{font-size:20px;margin:0 0 18px}label{display:block;font-size:13px;color:#555;margin:12px 0 4px}
input{width:100%;box-sizing:border-box;padding:9px 10px;border:1px solid #ccc;border-radius:6px;font:inherit}
button{margin-top:18px;width:100%;padding:10px;border:0;border-radius:6px;background:#2f3437;color:#fff;font:inherit;cursor:pointer}
.f{color:#b3261e;font-size:14px;margin:0 0 8px}
</style></head><body>
<form method="post">
<h1><?php echo $name; ?></h1>
<?php if ( $fehler ) : ?><p class="f">Benutzer oder Passwort falsch.</p><?php endif; ?>
<label for="b">Benutzer</label><input id="b" name="b2t_zugang_benutzer" autocomplete="username" required autofocus>
<label for="p">Passwort</label><input id="p" name="b2t_zugang_passwort" type="password" autocomplete="current-password" required>
<button type="submit">Anmelden</button>
</form></body></html><?php
	exit;
}, 0 );
