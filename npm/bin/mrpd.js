#!/usr/bin/env node
/*
  mrpd (npm wrapper)

  Design goals:
  - frictionless for devs who reach for npm/npx
  - single source of truth stays the Python project

  Behavior:
  - If MRPD_USE_REPO=1 and we can detect the monorepo python package, run it directly:
      python -m mrpd.cli <args>
  - Otherwise, use a dedicated venv under ~/.mrpd/runtime and ensure the PyPI package is installed,
    then run: python -m mrpd.cli <args>

  Env overrides:
  - MRPD_PYPI_PACKAGE (default: "mrpd")
  - MRPD_PYPI_VERSION (optional, e.g. "0.1.0")
*/

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

function isWin() {
  return process.platform === "win32";
}

function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, {
    stdio: "inherit",
    ...opts,
  });
  if (r.error) throw r.error;
  return r.status ?? 0;
}

function whichPython() {
  // Prefer Windows launcher
  if (isWin()) {
    const status = spawnSync("py", ["-3", "-c", "import sys; print(sys.executable)"], {
      stdio: "ignore",
    }).status;
    if (status === 0) return { cmd: "py", prefixArgs: ["-3"] };
  }

  for (const cmd of ["python3", "python"]) {
    const status = spawnSync(cmd, ["-c", "import sys"], { stdio: "ignore" }).status;
    if (status === 0) return { cmd, prefixArgs: [] };
  }

  return null;
}

function repoRootFromHere() {
  // npm/bin/mrpd.js -> npm/bin -> npm -> repo root
  return path.resolve(__dirname, "..", "..");
}

function repoHasMrpd(root) {
  return fs.existsSync(path.join(root, "mrpd", "cli.py")) && fs.existsSync(path.join(root, "pyproject.toml"));
}

function ensureVenv(py, venvDir) {
  if (fs.existsSync(path.join(venvDir, isWin() ? "Scripts" : "bin"))) return;
  fs.mkdirSync(venvDir, { recursive: true });
  const status = run(py.cmd, [...py.prefixArgs, "-m", "venv", venvDir]);
  if (status !== 0) process.exit(status);
}

function venvPython(venvDir) {
  return path.join(venvDir, isWin() ? "Scripts" : "bin", isWin() ? "python.exe" : "python");
}

function ensurePipPackage(pyExe, pkg, version) {
  const spec = version ? `${pkg}==${version}` : pkg;

  // Fast check: can we import mrpd?
  const check = spawnSync(pyExe, ["-c", "import mrpd"], { stdio: "ignore" });
  if (check.status === 0) return;

  console.error(`[mrpd] Installing Python package: ${spec}`);
  const status = run(pyExe, ["-m", "pip", "install", "--upgrade", spec], { cwd: path.dirname(pyExe) });
  if (status !== 0) process.exit(status);
}

function main() {
  const py = whichPython();
  if (!py) {
    console.error("[mrpd] Python 3 is required (python/python3 or py -3). Install Python first.");
    process.exit(2);
  }

  const args = process.argv.slice(2);

  const root = repoRootFromHere();
  const inRepo = process.cwd().toLowerCase().startsWith(root.toLowerCase());
  const useRepo = process.env.MRPD_USE_REPO === "1" || (inRepo && process.env.MRPD_NO_REPO !== "1");

  if (useRepo && repoHasMrpd(root)) {
    // Run from repo (dev mode). Assumes dependencies are installed in whatever python we found.
    // Prefer repo-local venv if present so dependencies are available.
    const repoPy = isWin()
      ? path.join(root, ".venv", "Scripts", "python.exe")
      : path.join(root, ".venv", "bin", "python");

    const cmd = fs.existsSync(repoPy) ? repoPy : py.cmd;
    const prefix = fs.existsSync(repoPy) ? [] : py.prefixArgs;

    process.exit(run(cmd, [...prefix, "-m", "mrpd.cli", ...args], { cwd: root }));
  }

  // Installed/runtime mode
  const home = os.homedir();
  const runtimeDir = path.join(home, ".mrpd", "runtime");
  const venvDir = path.join(runtimeDir, "venv");

  ensureVenv(py, venvDir);

  const pyExe = venvPython(venvDir);
  const pkg = process.env.MRPD_PYPI_PACKAGE || "mrpd";
  const ver = process.env.MRPD_PYPI_VERSION || "";

  // IMPORTANT: avoid importing the local repo's ./mrpd package when running
  // the venv-installed CLI. Set cwd away from any checkout that may shadow it.
  ensurePipPackage(pyExe, pkg, ver || null);

  process.exit(run(pyExe, ["-m", "mrpd.cli", ...args], { cwd: runtimeDir }));
}

try {
  main();
} catch (e) {
  console.error("[mrpd] failed:", e && e.message ? e.message : e);
  process.exit(1);
}
