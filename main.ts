// Token Launch Radar — a make.fun token-radar-01 entry (Node 22, standard library only).
//
// Reads the sealed snapshot (--input <file|dir>, default /input/snapshot.json), scores every
// eligible pre-token protocol with the model in lib/model.ts, and writes to the output dir
// (MAKEFUN_OUTPUT_DIR, or /output in the grader's container):
//   board.json            the ranked board
//   dashboard/            a copy of this repo's dashboard, plus zdata.js, the data it renders
//   screenshots/          a copy of this repo's three screenshots
//   dossier.json          the judge's summary, built with vendor/makefun-board.ts
//
// The run is deterministic: the same snapshot always writes the same bytes.

import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { boardIssue, buildBoard, dataScript, parseSnapshot } from './lib/model.ts';
import { buildDossier } from './vendor/makefun-board.ts';

const here = fileURLToPath(new URL('.', import.meta.url));

/** The gate's caps, passed to buildDossier so an over-limit output fails here, not at the scorer. */
const DOSSIER_CAPS = {
  text_max_bytes: 65_536,
  screenshots: { max: 4, max_bytes: 524_288 },
  dashboard: { max_files: 400, max_bytes: 4_194_304 },
};
const IMAGE_NAME = /^[A-Za-z0-9_][A-Za-z0-9._-]{0,127}$/;

/** --name <value> or --name=<value> out of the arguments, or the fallback. */
function arg(name: string, fallback: string): string {
  const at = process.argv.indexOf(`--${name}`);
  if (at >= 0 && at + 1 < process.argv.length) return process.argv[at + 1]!;
  const eq = process.argv.find((a) => a.startsWith(`--${name}=`));
  return eq === undefined ? fallback : eq.slice(name.length + 3);
}

const inputArg = arg('input', '/input');
const inputFile = inputArg.endsWith('.json') ? inputArg : join(inputArg, 'snapshot.json');
if (!existsSync(inputFile)) {
  process.stderr.write(`radar: no snapshot at ${inputFile}: pass --input <snapshot.json|directory>\n`);
  process.exit(2);
}
const out = arg('output', process.env.MAKEFUN_OUTPUT_DIR ?? '/output');

const snapshot = parseSnapshot(readFileSync(inputFile, 'utf8'));
const { rows, meta } = buildBoard(snapshot);
const issue = boardIssue(rows, snapshot);
if (issue !== null) {
  process.stderr.write(`radar: the model wrote a board the gate refuses: ${issue}\n`);
  process.exit(1);
}

mkdirSync(out, { recursive: true });
writeFileSync(join(out, 'board.json'), `${JSON.stringify({ rows, meta })}\n`);

/** Copy one flat directory's regular files into `to`, skipping dot-names. */
function copyFlat(from: string, to: string): string[] {
  if (!existsSync(from)) return [];
  mkdirSync(to, { recursive: true });
  const copied: string[] = [];
  for (const name of readdirSync(from).sort()) {
    if (name.startsWith('.')) continue;
    const path = join(from, name);
    if (!statSync(path).isFile()) continue;
    copyFileSync(path, join(to, name));
    copied.push(name);
  }
  return copied;
}

const dashFiles = copyFlat(join(here, 'dashboard'), join(out, 'dashboard'));
// The data file lives beside the page it feeds, inside the output dashboard copy.
writeFileSync(join(out, 'dashboard', 'zdata.js'), dataScript(rows, meta));

const shots = copyFlat(join(here, 'screenshots'), join(out, 'screenshots'));
if (shots.length < 3) {
  process.stderr.write(`radar: screenshots/ holds ${shots.length} images: hand in 3 (board, detail, filtered)\n`);
  process.exit(1);
}
for (const name of shots) {
  if (!IMAGE_NAME.test(name)) {
    process.stderr.write(`radar: screenshots/${name}: a name is letters, digits and . _ -, 1 to 128 characters\n`);
    process.exit(1);
  }
}

// The dossier is written last: the scorer rebuilds it from this output and compares bytes.
writeFileSync(join(out, 'dossier.json'), buildDossier(out, DOSSIER_CAPS));

process.stdout.write(
  `radar: ${meta.protocol_count} protocols, ${meta.watchlist_size} on the watchlist, ${rows.length} rows ranked\n` +
  `radar: wrote board.json, dashboard/ (${dashFiles.length + 1} files incl. zdata.js), screenshots/ (${shots.length}) and dossier.json under ${out}\n`,
);
