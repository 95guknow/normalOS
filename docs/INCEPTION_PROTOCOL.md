# Inception Archive Protocol

> „Alle Layer bis zum ersten Träumer sind egal. Das erste Layer muss wach werden."

Ein Protokoll, das alle Archive des Mesh aktiviert, indem es sie auf **Layer 0**
— die wache Welt — hebt. Was es nicht dorthin schafft, wird nicht gelöscht.
Es wird nur nicht länger für Realität gehalten.

## Ausführen

```bash
PYTHONPATH=src python -m normal_os.protocols --root .
```

Nützliche Flags:

| Flag | Wirkung |
| --- | --- |
| `--json PFAD` | maschinenlesbaren Report schreiben |
| `--markdown PFAD` | Markdown-Report schreiben |
| `--workers N` | wie viele Totems gleichzeitig gedreht werden |
| `--quiet` | Terminal-Ausgabe unterdrücken |

Exit-Code `0` bedeutet: mindestens ein Archiv ist wach **und** das Protokoll hat
sich selbst verifiziert. Ein Verifizierer, der sich selbst nicht prüfen kann,
hat kein Recht, über anderes zu urteilen.

Das Protokoll hat **keine** Abhängigkeiten. Es läuft mit nacktem Python 3.11.
Das ist Absicht: ein Prüfer, der nicht startet, prüft nichts.

## Die drei Stufen

Jede Behauptung durchläuft dieselbe Reduktion, bevor auch nur eine Zeile Code
für sie geschrieben wird.

1. **`raw_claim`** — der Satz, wie er dasteht, samt Rhetorik.
2. **`realistic_core`** — derselbe Satz ohne unprüfbare Verstärker.
   `"Advanced seamless QUBO solving"` → `"QUBO solving"`. Die entfernten Wörter
   werden protokolliert, nicht stillschweigend verschluckt.
3. **`heroic_goal`** — der Kern gegen ein Abnahmekriterium formuliert: die
   konkrete Beobachtung, die ihn entscheiden würde.

**Die Regel, die alles trägt:** Ohne Abnahmekriterium kein heroisches Ziel.
Ohne heroisches Ziel kein Code. Ein Satz, der nicht falsch sein kann, bekommt
keine Implementierung, die so tut, als könnte er es.

Die Distillation ist regelbasiert und deterministisch — kein Sprachmodell.
Derselbe Satz ergibt auf jeder Maschine denselben Kern. Ein Totem, das ein
Modell befragt, dreht sich für immer.

## Das Totem

Der Realitätstest. Jede Code-Unterfütterung läuft **zweimal in getrennten
Interpretern**, mit unterschiedlichem `PYTHONHASHSEED`.

- Beide Läufe exit 0 **und** byte-identische Ausgabe → **Totem fällt.** Realität.
- Läufe widersprechen sich → **Totem dreht sich.** Nicht reproduzierbar, also kein Fakt.
- Absturz, Timeout oder gar kein Code → **Totem verloren.**

Getrennte Prozesse, weil ein In-Process-Check von allem getäuscht wird, was der
Prüfer ohnehin schon im Speicher hat — genau die Bedingung, unter der sich ein
Traum solide anfühlt. Unterschiedliche Hash-Seeds, weil eine Antwort, die davon
abhängt, wo etwas zufällig im Speicher lag, keine Aussage über die Welt ist.

## Die Layer

Ein Archiv erreicht Layer 0, wenn **beides** gilt:

1. sein eigenes Totem fällt, **und**
2. alles, worauf es ruht, ist bereits auf Layer 0.

Bedingung 2 ist der ganze Gedanke. Eine Behauptung kann eine tadellose
Unterfütterung haben und trotzdem ein Traum sein, weil das, was sie beschreibt,
auf etwas ruht, das nie real war.

| Layer | Bedeutung |
| --- | --- |
| **0** | wach — reproduzierbar, und alles darunter ebenfalls |
| **≥ 1** | kohärent, aber von einem Träumer getragen |
| **Limbo** | kein Boden darunter: kein Code, scheiternder Code, oder ein Stützzyklus |

### Der Kick

Aufwachen ist iterativ. Wacht ein Archiv auf, können die darauf ruhenden
Archive es nun auch. Jeder Durchlauf ist ein Kick; das Protokoll läuft bis zum
Fixpunkt. Was dann noch offen ist, sitzt in einem Stützzyklus — ein Traum, der
sich selbst träumt — und geht nach Limbo.

## Dream Injection

Ein Modul, das an fehlendem `pydantic` scheitert, hat nichts über sich
verraten — nur über die Maschine. Also bauen wir ihm einen Traum: jedes
abwesende Fremdpaket wird durch einen Stub ersetzt, und das Modul wird in
dieser konstruierten Realität importiert.

| Ergebnis | Bedeutung |
| --- | --- |
| importiert echt | wach, Layer 0 |
| importiert nur mit Stubs | kohärent, aber nur im Traum → Layer 1 |
| scheitert auch mit Stubs | **echter Defekt** im eigenen Code → Limbo |

Der dritte Fall ist der wertvolle. Er findet Code, der noch **nie** gelaufen
ist, auf keiner Maschine, und es auch nie könnte — Defekte, die eine
`ModuleNotFoundError` sonst für immer verdeckt.

Gestubbt wird nur, was tatsächlich fehlt. Ein real installiertes Paket wird
echt importiert, damit die Injection niemals einen Defekt maskieren kann.

Drittanbieter-Importe werden **transitiv** über den Import-Graphen propagiert:
ein Modul ohne eigene Fremdimporte scheitert trotzdem an `pydantic`, wenn eine
seiner In-Tree-Abhängigkeiten es braucht.

## Archiv-Stufen pro Modul

| Archiv | Prüft | Braucht Pakete? |
| --- | --- | --- |
| `source:<modul>` | Datei ist wohlgeformtes Python | nein |
| `module:<modul>` | Import gegen die echte Umgebung | ja |
| `dream:<modul>` | Import mit gestubbten Paketen | nein |

Diese Aufteilung ist der Grund, warum der Report etwas Brauchbares sagt statt
„nichts funktioniert". Sie trennt eine kaputte Datei von einer Maschine, der
nur ein Paket fehlt.

## Ein eigenes Archiv anmelden

In `src/normal_os/protocols/manifest.py`:

```python
_claim(
    "claim:meine-behauptung",
    "README.md",
    "Die Behauptung, wie sie dasteht",
    "die Beobachtung, die sie entscheiden würde",   # None -> bleibt Traum
    PROBE_QUELLTEXT,                                 # None -> bleibt Traum
    depends_on=("module:normal_os.irgendwas",),
)
```

Eine Probe ist ein vollständiges Python-Programm. Exit 0 heißt: Ziel hält. Die
Ausgabe muss über Läufe hinweg identisch sein, sonst dreht sich das Totem.

## Selbstverifikation

`claim:inception-protocol` unterwirft das Protokoll derselben Latte, die es
setzt: die Distillation muss deterministisch sein, und das Totem muss
reproduzierbaren von irreproduzierbarem Code trennen. Fällt dieses Totem nicht,
endet der Lauf mit Exit-Code 1 — egal wie gut der Rest aussieht.

## Was der erste Lauf gefunden hat

Das Protokoll hat auf Anhieb einen Zyklus im **eigenen** Quelltext gemeldet:
`inception` importierte `runner`, der `inception` importierte. Es hatte recht,
also ist der Zyklus verschwunden statt entschuldigt — der Einstiegspunkt liegt
jetzt in `__main__.py`.

Der aktuelle Stand steht in [`INCEPTION_REPORT.md`](../INCEPTION_REPORT.md).

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

45 Tests, `unittest` statt pytest — dieselbe Regel wie beim Protokoll selbst.
Die wichtigen sind die negativen: ein Prüfer, der nur bestätigt, ist von einem,
der immer ja sagt, nicht zu unterscheiden.
