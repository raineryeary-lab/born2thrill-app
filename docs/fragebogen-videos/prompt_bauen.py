"""Baut den Text fuer einen Clip aus szenen.json: Stil, nur die Figuren der
Szene ("wer"), Szenentext, Ton. Rainer, 2026-11-03: Steht die ganze
Familie in der Beschreibung, steht sie auch im Bild -- deshalb nur die,
die mitspielen, und ausdruecklich niemand sonst."""

ENGLISCH = {"vater": "the father", "mutter": "the mother", "teen": "the teenage daughter",
            "tochter": "the little daughter", "sohn": "the son", "opa": "the grandfather",
            "oma": "the grandmother", "baby": "the baby", "hund": "the dog"}


def prompt(cfg, szene, stil=None):
    fig = cfg["figuren"]
    wer = szene["wer"]
    namen = [ENGLISCH[w] for w in wer]
    besetzung = (f"Only these characters appear in this clip: {', '.join(namen)}. "
                 "Nobody else from <Picture 1> is in the picture.")
    if len(wer) > 1:
        besetzung += " " + fig["_groessen"]
    teile = [stil or cfg["stil"], fig["_alle"], besetzung] + [fig[w] for w in wer] + [szene["text"], cfg["ton"]]
    return "\n\n".join(teile)
