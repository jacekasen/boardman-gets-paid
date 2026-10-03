import { execFileSync } from "node:child_process";
import { writeFileSync, renameSync } from "node:fs";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../../", import.meta.url));
const python = process.env.BOARDMAN_PYTHON;
const output = execFileSync(
  python || process.env.CONDA_EXE || "conda",
  python
    ? ["-m", "boardman.web_api", "snapshot"]
    : [
        "run",
        "--no-capture-output",
        "-n",
        "nba",
        "python",
        "-m",
        "boardman.web_api",
        "snapshot",
      ],
  { cwd: root, maxBuffer: 10 * 1024 * 1024, encoding: "utf8" },
);
JSON.parse(output);
const target = new URL("../src/data/league.json", import.meta.url);
const temporary = new URL("../src/data/league.json.tmp", import.meta.url);
writeFileSync(temporary, output);
renameSync(temporary, target);
console.log("Refreshed the league snapshot from the Python valuation engine.");
