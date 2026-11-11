# Releasing the web app

The first release is local only: no account, no server, no payment. Everything a user
makes lives in their browser's IndexedDB, under the site's origin. This page is the
checklist for shipping that version and the audit of what remains open.

## What a build is

`cd web && npm run build` writes a static site to `web/dist/`: one HTML page, the bundled
scripts and styles, the favicon, the web app manifest, and the seven kits and ten
projects as hashed assets (about 3.5 MB). Nothing runs on a server; any static host
serves it.

Before a release:

1. `npm run presets` if a pack spec or the drum synthesizer changed, so `web/src/presets`
   is current (the zips and manifest are committed).
2. `npm test`, `npm run lint`, `npm run test:visual`, `npm run build`.
3. Deploy `web/dist/` to the host.

## Hosting on Netlify

The repo carries the Netlify configuration: `netlify.toml` at the root (base `web`,
command `npm ci && npm run build`, publish `dist`, Node 22) and `web/public/_headers`,
which caches the hashed assets, the bundled projects among them, for a year and the web
app manifest not at all.

To set it up once:

1. Netlify, Add new site, Import an existing project, pick the GitHub repo. The settings
   are read from `netlify.toml`; nothing to type.
2. Domain management, add the registered domain (the apex, the `app.` subdomain, or both).
   Either point the registrar at Netlify's nameservers, or add the CNAME and A/ALIAS records
   Netlify shows. Netlify issues the certificate itself; HTTPS is forced.
3. Push to `master`. Every push deploys; pull requests get preview URLs on their own
   subdomain, with their own empty IndexedDB, so previews never touch anyone's library.

Or, without connecting the repo, publish a local build: `cd web && npm run build && npx
netlify-cli deploy --prod --dir=dist`.

What the host must provide, which Netlify does:

- **HTTPS.** Recording a backup from the device uses the microphone, which browsers allow
  only on secure origins.
- **The site root.** The build assumes it. For a sub-path host set `base` in
  `vite.config.ts`; the preset loader and the manifest follow `BASE_URL`.
- **One origin, kept.** The data lives under the origin. Moving the app to another domain
  later means users' projects do not follow; choose the release hostname now and keep it.
  Use the `app.` subdomain if the apex may later serve a marketing page.

## How the bundled projects reach every user

The seven kits and ten projects are assets of the build. On every load the app adds any
the library lacks, judged by the bundled identity each record keeps, so a first launch
gets all of them, kits first, with every drum hit one shared library sample in its
machine's folder, and opens Rainy Rhodes ([presets](presets.md)). From then on they are the user's own local projects: edits,
renames and copies are theirs and stay on the device. A deleted one returns on the next
load; a copy does not carry the identity and is never touched.

A release with a changed pack does not alter a user's existing copy of it: presence is
judged by identity, not content. Offering updated versions to existing users would be a
deliberate action, not an automatic overwrite.

## Keeping the data local, and safe

- IndexedDB survives reloads, updates of the app and browser restarts. The app asks the
  browser for persistent storage on launch, which Chrome grants to sites the user engages
  with and Safari grants to installed web apps; without it, Safari may evict a site's data
  after seven days without a visit. The Export project action is the user's backup; the
  release notes should say so plainly.
- Private windows and "clear site data" remove everything, as for any local app.
- A browser crash mid-save can lose at most the last 300 ms of edits (the save debounce).
- When accounts arrive, the local library is the seed for the user's cloud library; the
  `ProjectRecord`, `SampleRecord` and `KitRecord` shapes are the sync unit, and the
  `presetsVersion`, `lastProject` and preference settings stay local.

## Audit: resolved for this release

- A first launch under React's strict mode mounted twice and added the bundled projects
  twice; initialisation now runs once and a second call joins it.
- Adding the bundled projects shows progress on the loading screen, reports the outcome in
  the status slot, and falls back to an empty project when a zip cannot be fetched.
- A render error no longer leaves a blank page: an error boundary shows the message and a
  reload button and says the data is unaffected.
- The page has a description, theme colours for both schemes and a web app manifest, so
  phones can add it to the home screen as a standalone app.
- The archive importer range-checks edits, so a hand-edited project file cannot produce
  silent or exploding audio.
- `test-results/` and `.DS_Store` are ignored and should be removed from the index before
  the release commit.

## Audit: open before or soon after release

- **Sample licence: resolved.** The bundled drums are synthesized (`web/scripts/drum-synth.ts`)
  and released with the code under the MIT licence. The earlier kits, cut from a free
  third-party TR pack that states no licence, are kept out of the repository
  (`web/presets-tr/`, ignored) and can be rebuilt locally from the pack
  ([presets](presets.md)). Note that they remain in the history of the private
  repository: publish from a fresh history (see the open-source checklist below).
- **Research fixtures: resolved.** Two golden fixtures derived from the research device's
  starting state, which may have held factory audio, are local only
  (`web/src/core/__fixtures__/local/`, ignored); their tests skip without them.
- **Offline use.** There is no service worker, so the app needs the network to load; once
  loaded it works offline until the tab closes. A service worker that caches the build
  and the packs is the natural next step for a tool used away from a desk.
- **Silent switch on iPhones and iPads: handled.** Web Audio is muted while the ring/silent
  switch is on silent unless the page is playing an HTML media element, so the first tap
  starts a looped silent clip through one, and the preview sounds with the switch in either
  position. Verify on a device after each iOS release; Apple changes this behaviour.
- **Microphone import on iOS.** Safari on iOS delivers a mono microphone stream, and the
  backup decoder needs the stereo signal; importing from the device is a desktop feature
  for now and the dialog should say so on phones.
- **Storage headroom.** The bundled kits and projects take about 150 samples and a few megabytes; a user
  importing long samples can reach tens of megabytes, far under browser quotas (hundreds
  of megabytes at least). The memory meter counts device pages, not browser storage; a
  storage estimate in the Library header would help heavy users.
- **No telemetry, no crash reports.** By design for a local release; the error boundary
  prints the error for the user to copy into a report.
- **Browser support.** Chrome, Edge, Firefox and Safari 16 or later (container queries and
  `:has()` are used). Older Safari gets a broken layout; a one-line notice for unsupported
  browsers would be kind.

## Open-source checklist

The repository is released under the MIT licence ([LICENSE](../LICENSE)). Before the first
public push:

1. Commit the working tree.
2. Publish from a fresh history. The private history contains the earlier TR-pack presets
   (`web/src/presets/`, `web/public/packs/`) and the two local fixtures, so pushing it would
   publish them. The public repository is a separate one with its own history (below).
3. Check that the ignored local material is absent from the new repository: `sample_packs/`,
   `web/presets-tr/`, `web/src/core/__fixtures__/local/`, and the research captures under
   `experiments/` (`*.wav`, `*.npz`, `derived/`).
4. Known and accepted: 22 experiment records under `experiments/` contain absolute Windows
   paths from the research machine (a first name and a OneDrive folder). Each is pinned by
   SHA-256 in later records, so they are left as the historical record they are.
5. In a fresh clone, run `npm ci && npm test && npm run build` in `web/` and `pytest` at the
   root: the capture-based tests skip and the rest pass.

## Publishing workflow

Two repositories share this working folder:

| Remote | Repository | Holds |
| --- | --- | --- |
| `origin` | private | `master`, the full history; all development happens here |
| `public` | public | `main`, one commit per published update, no private history |

The local branch `public` tracks the public repository. To publish, commit on `master` and
run `./publish-public.sh "Describe the update"` from the root. It copies `master`'s tracked
files onto `public` exactly (additions, changes, deletions) as one commit and pushes it to
the public `main`. It refuses to run off `master`, with uncommitted changes, or when the
`public` remote points at the private repository. Never push `master` to `public`, and
never edit the `public` branch by hand: changes made there are not carried back.

Contributions to the public repository arrive as pull requests against its `main`. Apply
them to `master` (for example `git fetch public && git cherry-pick <commit>` from `master`,
or by hand), then publish as usual.
