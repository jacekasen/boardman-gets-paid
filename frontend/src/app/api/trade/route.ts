import { spawn } from "node:child_process";
import path from "node:path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let payload: unknown;
  try {
    const body = await request.text();
    if (body.length > 16_384)
      return NextResponse.json(
        { error: "Trade request is too large." },
        { status: 413 },
      );
    payload = JSON.parse(body);
    if (!payload || typeof payload !== "object" || Array.isArray(payload))
      throw new Error();
  } catch {
    return NextResponse.json(
      { error: "Provide a valid trade request." },
      { status: 400 },
    );
  }
  const root = path.resolve(process.cwd(), "..");
  const python = process.env.BOARDMAN_PYTHON;
  const command = python || process.env.CONDA_EXE || "conda";
  const args = python
    ? ["-m", "boardman.web_api"]
    : [
        "run",
        "--no-capture-output",
        "-n",
        "nba",
        "python",
        "-m",
        "boardman.web_api",
      ];
  try {
    const result = await new Promise<{ body: unknown; status: number }>(
      (resolve, reject) => {
        const child = spawn(command, args, {
          cwd: root,
          stdio: ["pipe", "pipe", "pipe"],
        });
        let output = "";
        const timer = setTimeout(() => {
          child.kill();
          reject(new Error("timeout"));
        }, 20_000);
        child.stdout.on("data", (chunk) => {
          output += chunk;
        });
        child.stderr.on("data", () => {
          /* Keep process diagnostics off the public response. */
        });
        child.on("error", (error) => {
          clearTimeout(timer);
          reject(error);
        });
        child.stdin.on("error", () => {});
        child.on("close", (code) => {
          clearTimeout(timer);
          try {
            resolve({
              body: JSON.parse(output),
              status: code === 0 ? 200 : 400,
            });
          } catch {
            reject(new Error("engine unavailable"));
          }
        });
        child.stdin.end(JSON.stringify(payload));
      },
    );
    return NextResponse.json(result.body, { status: result.status });
  } catch {
    return NextResponse.json(
      {
        error:
          "The valuation engine is unavailable. Install the Python project dependencies and set BOARDMAN_PYTHON if needed.",
      },
      { status: 503 },
    );
  }
}
