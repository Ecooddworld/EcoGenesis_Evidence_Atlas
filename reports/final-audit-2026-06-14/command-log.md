# Final Audit Command Log

Started: 2026-06-14T15:44:13.972074+00:00

## git-status

Current commit and working tree status

```bash
git rev-parse --short HEAD && git status -sb
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:44:13.972221+00:00
Finished: 2026-06-14T15:44:13.993072+00:00

stdout:

```text
6ec3aa6
## main...origin/main
?? reports/competition-100-sequences.zip
?? reports/competition-100-sequences/
?? reports/final-audit-2026-06-14/

```

## docker-compose-status

Atlas Docker compose status

```bash
docker compose ps
```

Exit code: `124`
Status: **fail**
Started: 2026-06-14T15:44:13.993119+00:00
Finished: 2026-06-14T15:44:43.999604+00:00

## backend-health

Backend health endpoint

```bash
curl -fsS http://127.0.0.1:18100/health
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:44:43.999746+00:00
Finished: 2026-06-14T15:44:44.036266+00:00

stdout:

```text
{"status":"ok","service":"ecogenesis-barcode-gbif-compiler"}
```

## gbif-status

Live GBIF status endpoint

```bash
curl -fsS http://127.0.0.1:18100/api/evidence/gbif-status
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:44:44.036325+00:00
Finished: 2026-06-14T15:45:04.252409+00:00

stdout:

```text
{"status":"unavailable","base_url":"https://api.gbif.org/v1","message":"GBIF API is unavailable: ConnectTimeout. Live runs will use an empty no-evidence fallback."}
```

## csv-template

CSV template endpoint returns headers

```bash
curl -fsS http://127.0.0.1:18100/api/barcode/csv-template | sed -n '1,2p'
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:45:04.252468+00:00
Finished: 2026-06-14T15:45:04.270884+00:00

stdout:

```text
sequenceID,sequence,occurrenceID,eventID,materialSampleID,basisOfRecord,scientificName,eventDate,marker,assayType,referenceDatabase,methodOrSOP,target_gene,target_subfragment,pcr_primer_forward,pcr_primer_reverse,seq_meth,contaminationAssessment,topTaxon,topIdentity,topCoverage,topRank,topAlignedLength,secondTaxon,secondIdentity,secondCoverage,secondRank,secondAlignedLength,barcodeIntraMax,barcodeInterMin,diagnosticKmers
AALB-COI-good,ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCG,urn:example:AALB-COI-good,event-aedes-001,sample-aedes-001,MaterialSample,Aedes albopictus,2026-04-18,COI-5P,single_specimen_barcode,COI Animals / BOLD public clustered reference,GBIF Sequence ID-compatible BLAST workflow,cytochrome c oxidase subunit I,COI-5P barcode region,GGWACWGGWTGAACWGTWTAYCCYCC,TAIACYTCIGGRTGICCRAARAAYCA,Illumina MiSeq,no contamination detected,Aedes albopictus,99.6,96,species,658,Aedes aegypti,98.2,95,species,625,0.009,0.018,ACGTTGACCTAGGCT|TGACCTAGGCTTACG

```

## csv-import-good

Import good CSV and summarize validation

```bash
python3 - <<'INNER'
import json, urllib.request
from pathlib import Path
boundary='----auditImportBoundary'
payload=b''
payload += f'--{boundary}\r\n'.encode()
payload += b'Content-Disposition: form-data; name="file"; filename="aedes_good.csv"\r\n'
payload += b'Content-Type: text/csv\r\n\r\n'
payload += Path('examples/aedes_good.csv').read_bytes()
payload += f'\r\n--{boundary}--\r\n'.encode()
req=urllib.request.Request('http://127.0.0.1:18100/api/barcode/import-csv', data=payload, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
with urllib.request.urlopen(req, timeout=45) as resp:
    d=json.loads(resp.read().decode())
print(json.dumps({'ok': d.get('validation',{}).get('ok'), 'records': len(d.get('request',{}).get('records',[])), 'warnings': d.get('validation',{}).get('warnings', [])[:3]}, indent=2))
INNER
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:45:04.270972+00:00
Finished: 2026-06-14T15:45:04.433416+00:00

stdout:

```text
{
  "ok": true,
  "records": 1,
  "warnings": [
    "Some strongly recommended GBIF/DNA fields are missing; publication readiness may be blocked."
  ]
}

```

## four-csv-live-api

Run four documented CSV examples through live API

```bash
python3 - <<'INNER'
import csv, io, json, urllib.request
from pathlib import Path
base='http://127.0.0.1:18100/api/barcode'
examples=['aedes_good.csv','aedes_ambiguous.csv','aedes_missing_metadata.csv','aedes_weak_coverage.csv']
summary=[]
for name in examples:
    boundary='----auditBoundary'
    payload=b''
    payload += f'--{boundary}\r\n'.encode()
    payload += f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'.encode()
    payload += b'Content-Type: text/csv\r\n\r\n'
    payload += (Path('examples')/name).read_bytes()
    payload += f'\r\n--{boundary}--\r\n'.encode()
    req=urllib.request.Request(f'{base}/run-csv', data=payload, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
    with urllib.request.urlopen(req, timeout=45) as resp:
        data=json.loads(resp.read().decode())
    rid=data['run_id']
    with urllib.request.urlopen(f'{base}/runs/{rid}/exports/sequence_safety_table.csv', timeout=45) as resp:
        rows=list(csv.DictReader(io.StringIO(resp.read().decode())))
    summary.append({'file': name, 'run_id': rid, 'status': data.get('status'), 'decisionClass': sorted({r.get('decisionClass') for r in rows}), 'publicationBucket': sorted({r.get('publicationBucket') for r in rows}), 'exports': len(data.get('exports', []))})
print(json.dumps(summary, indent=2, sort_keys=True))
INNER
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:45:04.433484+00:00
Finished: 2026-06-14T15:45:04.696279+00:00

stdout:

```text
[
  {
    "decisionClass": [
      "species-safe"
    ],
    "exports": 39,
    "file": "aedes_good.csv",
    "publicationBucket": [
      "publishable_candidate"
    ],
    "run_id": "39b4ccc180c442eab6538da8b59413df",
    "status": "completed"
  },
  {
    "decisionClass": [
      "genus-safe"
    ],
    "exports": 39,
    "file": "aedes_ambiguous.csv",
    "publicationBucket": [
      "publishable_candidate"
    ],
    "run_id": "5813be02140c45ed9d84de2a66fefe31",
    "status": "completed"
  },
  {
    "decisionClass": [
      "not-publishable"
    ],
    "exports": 39,
    "file": "aedes_missing_metadata.csv",
    "publicationBucket": [
      "repair_required"
    ],
    "run_id": "7f9d8b9522904d31aca2c57557b9715d",
    "status": "completed"
  },
  {
    "decisionClass": [
      "weak"
    ],
    "exports": 39,
    "file": "aedes_weak_coverage.csv",
    "publicationBucket": [
      "repair_required"
    ],
    "run_id": "b7f699e078ec471fbf37a8b59759c265",
    "status": "completed"
  }
]

```

## backend-pytest

Backend regression tests from docs/testing.md

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3.12 -m pytest backend/tests -q
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:45:04.696354+00:00
Finished: 2026-06-14T15:45:07.538260+00:00

stdout:

```text
.........................................s...........                    [100%]
52 passed, 1 skipped in 2.11s

```

## frontend-tests

Frontend regression tests

```bash
npm test -- --run
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:45:07.538325+00:00
Finished: 2026-06-14T15:45:09.817728+00:00

stdout:

```text

> ecogenesis-evidence-atlas-frontend@0.1.0 test
> vitest run --run


 RUN  v4.1.5 /Users/oddworld/Documents/BIO./EcoGenesis_Evidence_Atlas/frontend


 Test Files  1 passed (1)
      Tests  13 passed (13)
   Start at  17:45:07
   Duration  1.84s (transform 221ms, setup 66ms, import 272ms, tests 873ms, environment 528ms)


```

## frontend-build

Frontend production build

```bash
npm run build
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:45:09.817790+00:00
Finished: 2026-06-14T15:45:10.264678+00:00

stdout:

```text

> ecogenesis-evidence-atlas-frontend@0.1.0 build
> vite build

vite v8.0.10 building client environment for production...
[2K
transforming...✓ 17 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.53 kB │ gzip:   0.32 kB
dist/assets/index-DjwZSseL.css   78.19 kB │ gzip:  14.57 kB
dist/assets/index-Sfi1jABk.js   400.39 kB │ gzip: 111.40 kB

✓ built in 166ms

```

## operability-report

Barcode operability verification script

```bash
backend/.venv/bin/python backend/scripts/verify_barcode_operability.py
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:45:10.264740+00:00
Finished: 2026-06-14T15:45:11.021066+00:00

stdout:

```text
{
  "status": "pass",
  "report_dir": "/Users/oddworld/Documents/BIO./EcoGenesis_Evidence_Atlas/reports/barcode-operability"
}

```

## browser-smoke

Playwright browser smoke for local production frontend

```bash
node --input-type=module - <<'INNER'
import { chromium } from '@playwright/test';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
const bad = [];
page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
page.on('pageerror', err => errors.push(err.message));
page.on('response', res => { if (res.status() >= 400) bad.push(`${res.status()} ${res.url()}`); });
await page.goto(`http://127.0.0.1:13100/?audit=${Date.now()}#analysis-picture-sequence`, { waitUntil: 'load', timeout: 60000 });
await page.getByText('The whole analysis is now visible as a picture sequence.').waitFor({ state: 'visible', timeout: 15000 });
let desktopOverflow = await page.evaluate(() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - document.documentElement.clientWidth);
const cards = await page.locator('.analysis-picture-card').count();
const poster = await page.locator('img[alt="Generated six-panel EcoGenesis analysis sequence from input sequence to evidence pack"]').evaluate(img => ({complete: img.complete, width: img.naturalWidth, height: img.naturalHeight}));
await page.goto(`http://127.0.0.1:13100/?auditStory=${Date.now()}#animation-storyboard`, { waitUntil: 'load', timeout: 60000 });
await page.getByText('Six visual moments that make the EcoGenesis workflow easy to understand.').waitFor({ state: 'visible', timeout: 15000 });
const text = await page.locator('#animation-storyboard').innerText();
await page.setViewportSize({ width: 390, height: 900 });
await page.goto(`http://127.0.0.1:13100/?auditMobile=${Date.now()}#analysis-picture-sequence`, { waitUntil: 'load', timeout: 60000 });
await page.getByText('Generated analysis pictures').waitFor({ state: 'visible', timeout: 15000 });
let mobileOverflow = await page.evaluate(() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - document.documentElement.clientWidth);
await browser.close();
const result = {cards, poster, desktopOverflow, mobileOverflow, oldStoryboardPhrasesPresent: ['Animation-ready storyboard','generated PNG scenes','No text overlay','Future motion cues','Animate:'].filter(x => text.includes(x)), errors, bad};
console.log(JSON.stringify(result, null, 2));
if (cards !== 6 || !poster.complete || poster.width < 1000 || desktopOverflow > 2 || mobileOverflow > 2 || result.oldStoryboardPhrasesPresent.length || errors.length || bad.length) process.exit(1);
INNER
```

Exit code: `1`
Status: **fail**
Started: 2026-06-14T15:45:11.021130+00:00
Finished: 2026-06-14T15:45:11.074693+00:00

stderr:

```text
node:internal/modules/esm/resolve:857
  throw new ERR_MODULE_NOT_FOUND(packageName, fileURLToPath(base), null);
        ^

Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@playwright/test' imported from /Users/oddworld/Documents/BIO./EcoGenesis_Evidence_Atlas/frontend/[eval1]
    at packageResolve (node:internal/modules/esm/resolve:857:9)
    at moduleResolve (node:internal/modules/esm/resolve:926:18)
    at defaultResolve (node:internal/modules/esm/resolve:1056:11)
    at ModuleLoader.defaultResolve (node:internal/modules/esm/loader:654:12)
    at #cachedDefaultResolve (node:internal/modules/esm/loader:603:25)
    at ModuleLoader.resolve (node:internal/modules/esm/loader:586:38)
    at ModuleLoader.getModuleJobForImport (node:internal/modules/esm/loader:242:38)
    at ModuleJob._link (node:internal/modules/esm/module_job:135:49)
    at process.processTicksAndRejections (node:internal/process/task_queues:105:5) {
  code: 'ERR_MODULE_NOT_FOUND'
}

Node.js v22.12.0

```

## docker-smoke

Documented Docker smoke test

```bash
scripts/docker_smoke.sh
```

Exit code: `124`
Status: **fail**
Started: 2026-06-14T15:45:11.074750+00:00
Finished: 2026-06-14T15:49:11.078947+00:00

## competition-100-report-check

Validate 100-sequence competition report rows/counts

```bash
python3 - <<'INNER'
import csv, json
from collections import Counter
from pathlib import Path
p=Path('reports/competition-100-sequences/competition_100_sequence_results.csv')
rows=list(csv.DictReader(p.open()))
result={'rows': len(rows), 'decisionClass': dict(Counter(r['decisionClass'] for r in rows)), 'publicationBucket': dict(Counter(r['publicationBucket'] for r in rows)), 'report_exists': Path('reports/competition-100-sequences/competition_100_sequence_report.md').exists(), 'zip_exists': Path('reports/competition-100-sequences/evidence_pack.zip').exists()}
print(json.dumps(result, indent=2, sort_keys=True))
if result['rows'] != 100 or result['decisionClass'] != {'species-safe':25,'genus-safe':25,'weak':25,'not-publishable':25}: raise SystemExit(1)
INNER
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:49:11.079052+00:00
Finished: 2026-06-14T15:49:11.135605+00:00

stdout:

```text
{
  "decisionClass": {
    "genus-safe": 25,
    "not-publishable": 25,
    "species-safe": 25,
    "weak": 25
  },
  "publicationBucket": {
    "publishable_candidate": 50,
    "repair_required": 50
  },
  "report_exists": true,
  "rows": 100,
  "zip_exists": true
}

```

## live-gbif-scientific-suite

Optional live GBIF 1000-record / 100-claim suite from docs

```bash
backend/.venv/bin/python backend/scripts/run_scientific_hypothesis_suite.py --fresh --output-dir reports/final-audit-2026-06-14/live-gbif-suite
```

Exit code: `0`
Status: **pass**
Started: 2026-06-14T15:49:11.135687+00:00
Finished: 2026-06-14T15:49:33.076836+00:00

stdout:

```text
{
  "minimum_1000_deduplicated_records": true,
  "minimum_10_successful_online_scenarios": true,
  "no_fixture_records_counted": true,
  "minimum_100_hypothesis_claims": true,
  "every_claim_has_status_evidence_and_caveat": true
}

```
