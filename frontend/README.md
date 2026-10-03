# Board Man frontend

A responsive Next.js App Router dashboard for the existing Board Man valuation engine. Includes the league surplus board, salary/production scatter plot, team payrolls, individual contract profiles, CSV export, a two-team trade lab, and methodology.

## Run locally

From the repository root:

```sh
conda activate nba
npm install --prefix frontend
npm run dev
```

Open http://localhost:3000. Node 20.9+ is required (an active Node LTS release is recommended).

The trade API runs `conda run --no-capture-output -n nba python -m boardman.web_api`. The `nba` environment needs the existing project's Python dependencies. If necessary, install them with `conda run -n nba python -m pip install -e '.[dev]'`.

You can use a particular interpreter by setting `BOARDMAN_PYTHON` in `frontend/.env.local`, for example:

```sh
BOARDMAN_PYTHON=/opt/anaconda3/envs/nba/bin/python
```

If Conda is not on the server's PATH, set `CONDA_EXE` to its executable path. This application requires a Node server with access to the repository and Python environment for trade evaluation; it is not a static-only deployment.

## Data and calculations

The committed `src/data/league.json` snapshot is generated from the repository's processed parquet files using the existing Python valuation functions. Browsing the board does not need a Python request. Refresh it after ingesting or changing the data or model:

```sh
npm run data:refresh
```

Snapshot refresh uses the `nba` Conda environment by default, validates JSON, and replaces the old snapshot only on success. Restart or rebuild Next.js after refreshing the snapshot. The interactive trade lab calls `/api/trade`, which delegates to the same Python engine with the multi-season WAR baseline. It supports multi-player selections, salary dumps, legality violations, and before/after valuation for both teams. Dead-money contracts are excluded from selectable players, while the engine retains them in roster calculations.

All screens are explicitly scoped to the 2025–26 dataset. They do not represent live rosters. Friction multipliers are model assumptions; see the in-app methodology and the repository research documentation.

## Verify

```sh
npm run lint
npm run typecheck
npm run build
conda run -n nba python -m pytest -q
npm run start
```

The frontend uses local SVG graphics and Lucide icons, with no emoji. DM Sans and Manrope load from Google Fonts with system sans-serif fallbacks. Layout adapts to mobile, tables scroll on narrow screens, and player dialogs use native modal focus management and Escape dismissal.

`npm audit` at implementation time reported a `braces` advisory propagated through five development-only lint packages. No compatible patched version was available; forcing npm's suggested fix would downgrade the Next lint config to version 14. Production dependencies were unaffected.
