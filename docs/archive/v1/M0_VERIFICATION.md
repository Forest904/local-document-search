> Archivio v1 — fotografia documentale del 7 novembre 2026. Stati e risultati sono storici; non descrivono la v2. [Documentazione corrente](../../README.md).

# M0 — Verbale di verifica documentale

Data: 6 novembre 2026. Ambito: specifica, non implementazione.

## Esito e tracciabilità

M0 verificata: decisioni documentate, contratti allineati ed esempi di accettazione definiti.
M1–M9 restano da implementare e verificare. Nessuna dipendenza installata o API Python introdotta.

| Controllo | Evidenza | Esito |
|---|---|---|
| Decisioni v1 | [Registro OD-01…OD-23](OPEN_DECISIONS.md): ID univoci, decisione/esclusione, riferimento e milestone per tutte le 23 righe | Conforme |
| ADR e specifiche | ADR 0001–0009 confrontati con architettura, dominio, analisi, snapshot, contratti e UX | Conforme dopo rimozione delle scelte obsolete ancora aperte in ADR 0001 |
| Clausole miste | [Contratti](INTERFACE_CONTRACTS.md), [Dominio](DOMAIN_MODEL.md), [Analisi](INDEXING_AND_ANALYSIS.md), scenari M2 nel [piano test](TEST_STRATEGY.md) | AND e frasi interamente nello stesso campo; caso negativo BOTH già presente |
| Pulizia dati | Contratti, [Privacy](SECURITY_AND_PRIVACY.md), [Snapshot](SNAPSHOTS_AND_SYNC.md), scenari M6 | Rifiuto durante job esplicitato nel piano test; errore ripetibile e sorgenti preservati già previsti |
| Riuso job | Contratti, snapshot, UX e scenario M7 | Stesso job_id e reused=true, senza secondo writer |
| Paginazione | [ADR 0009](../../adr/0009-desktop-runtime.md), OD-19, contratti, UX e scenari M8 | Prima pagina alla variazione di snapshot; query/campo preservati; risposte obsolete ignorate; nessun nuovo campo nei DTO |
| Prerequisiti | [Roadmap](ROADMAP.md): catena M0 → M1 → … → M9 | Nessun ciclo; M3 richiede M2 e usa TXT/repository in memoria, senza dipendere da M4–M9 |
| Collegamenti | Controllo riproducibile sotto su 38 file Markdown del repository, 168 collegamenti locali, esclusi blocchi di codice | Nessun collegamento locale o ancora non risolto |
| Perimetro modifiche | git diff --check, elenco modifiche e file nuovi | Solo documentazione; nessun errore di whitespace |

Gli scenari sono specifiche di test futuri, non test funzionali eseguiti. I moduli applicativi sono ancora segnaposto; non è stata eseguita pytest né dichiarata una suite verde.

## Ripetere i controlli

Dalla radice del repository, con Python già disponibile e senza installazioni, eseguire il seguente script. Verifica link inline e reference-style, ancore dei titoli Markdown, copertura OD e prerequisiti dichiarati. Le directory sono destinazioni valide; URL esterni e blocchi di codice non vengono verificati. Le ancore seguono i titoli GitHub Markdown usati nel repository.

```python
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import subprocess

root = Path.cwd()
paths = subprocess.check_output(
    ['git', 'ls-files', '--cached', '--others', '--exclude-standard'], text=True
).splitlines()
files = sorted({root / p for p in paths if p.endswith('.md')})
def prose(path):
    return re.sub(r'^```[^\n]*\n.*?^```[^\n]*$', '',
                  path.read_text(encoding='utf-8'), flags=re.M | re.S)
def anchors(path):
    seen, result = {}, set()
    for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', prose(path), re.M):
        slug = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(slug if count == 0 else f'{slug}-{count}')
    return result
checked = 0
for source in files:
    body = prose(source)
    links = re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', body)
    links += re.findall(r'^\s*\[[^\]\n]+\]:\s*(\S+)', body, re.M)
    for raw in links:
        target = raw.strip().split(' "', 1)[0].strip('<>')
        parts = urlsplit(target)
        if parts.scheme or parts.netloc:
            continue
        dest = (source.parent / unquote(parts.path)).resolve() if parts.path else source
        assert dest.exists(), (source.relative_to(root), target)
        if parts.fragment:
            assert dest.is_file() and dest.suffix == '.md', target
            assert unquote(parts.fragment) in anchors(dest), (source, target)
        checked += 1
registry = (root / 'docs/OPEN_DECISIONS.md').read_text(encoding='utf-8')
rows = [line.split('|')[1:-1] for line in registry.splitlines()
        if re.match(r'^\| OD-\d{2} \|', line)]
assert [row[0].strip() for row in rows] == [f'OD-{n:02}' for n in range(1, 24)]
for row in rows:
    assert len(row) == 4 and all(cell.strip() for cell in row)
    assert re.search(r'\[[^\]]+\]\([^)]+\)', row[2])
    assert re.search(r'\bM[0-9]\b', row[3])
roadmap = (root / 'docs/ROADMAP.md').read_text(encoding='utf-8')
sections = re.split(r'^## M(\d) ', roadmap, flags=re.M)
assert sections[1::2] == list('0123456789')
for number, section in zip(sections[1::2], sections[2::2]):
    if int(number):
        entry = re.search(r'^\*\*Ingresso:\*\* (.+)$', section, re.M).group(1)
        assert re.findall(r'\bM\d\b', entry) == [f'M{int(number)-1}']
print(f'Markdown: {len(files)}; link locali: {checked}; OD: 23/23; catena M0-M9: OK')
```

Completare con `git diff --check`, `git diff --name-only` e `git ls-files --others --exclude-standard`: tutte le modifiche di questa consegna devono essere Markdown. Il controllo dei prerequisiti dichiarati va accompagnato dalla lettura delle attività: i rinvii a test futuri non sono dipendenze di ingresso.

Per cercare decisioni residue usare `rg -n -i 'TBD|TODO|FIXME|da definire|da decidere|Open implementation details|non.*scelta' docs README.md`. Classificare i risultati, non considerarli automaticamente errori.

## Limiti e dettagli espliciti rinviati

- Il template ADR contiene segnaposto intenzionali; il template della relazione e il piano query attendono corpus, risultati e misure reali in M3. Non sono decisioni v1 mancanti.
- La licenza del repository è esplicitamente non scelta nel [layout](REPOSITORY_LAYOUT.md); questa verifica non assegna una licenza né autorizza la distribuzione. Gli avvisi delle dipendenze e la verifica del pacchetto restano in M9.
- Versioni delle dipendenze e configurazione di packaging saranno fissate in M9, come già deciso nell'ADR 0009. Composizione e tipi Python concreti appartengono alle milestone implementative.
- Sono stati verificati riferimenti locali e coerenza interna, non raggiungibilità degli URL esterni, materiale originale del corso o fattibilità operativa dei parser e del pacchetto desktop.
- Nessun benchmark, recovery, test UI o comportamento applicativo è dimostrato dalla chiusura di M0.
