# Contributing

Thanks for your interest. Issues and pull requests are welcome: bug reports, fixes,
documentation, and new findings about the PO-33 format.

## Setting up

See the [README](README.md#quick-start-the-web-app) for both halves: the web app (Node 22,
`web/`) and the Python toolkit (Python 3.12, repository root).

Before opening a pull request, run what applies:

| Changed | Run |
| --- | --- |
| The web app | `npm run lint`, `npm test`, `npm run build` and `npm run test:visual` in `web/` |
| The Python toolkit | `ruff check src tests` and `pytest` at the root |
| Docs | Check that relative links resolve |

CI runs everything but the browser screenshot tests, whose baselines were made on macOS. If
your change alters the interface on purpose, run `npm run test:visual:update`, look at the
new screenshots, and include them.

## Claims about the device

Every statement about the PO-33 in `docs/` rests on a registered hardware experiment: the
predictions are written down before the session, the device's backup is compared byte for
byte with the target, and failed predictions are kept ([hardware sessions](docs/hardware-sessions.md)).
New findings are welcome in the same form. If you have observed something on a device but
not in that form, open an issue with what you did and saw; it can become an experiment.

## Audio

Only contribute audio you have the right to license under the MIT licence. The bundled
sounds are synthesized ([sound synthesis](docs/sound-synthesis.md)); recordings of a PO-33's
factory content or of third-party sample packs cannot be accepted.

## How changes land

Development happens in a private repository whose history holds research material that is
not published; this repository receives each update as a snapshot commit. A merged pull
request is applied there and appears here with the next update, so its commit may show up
under a different hash. You will be credited in the commit and, for format findings, in the
docs.
