from __future__ import annotations

import re
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PIN_RE = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==([^\s\\]+)")


def canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def source_pins(path: Path) -> tuple[dict[str, str], list[str]]:
    pins: dict[str, str] = {}
    includes: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--requirement ")):
            includes.append(line.split(maxsplit=1)[1])
            continue
        match = PIN_RE.match(line)
        if not match:
            raise SystemExit(f"{path}: direct dependency must use an exact == pin: {line}")
        pins[canonical_name(match.group(1))] = match.group(2)
    return pins, includes


def lock_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    current_block: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if PIN_RE.match(raw_line):
            check_hash_block(path, current_block)
            current_block = [raw_line]
        elif current_block:
            current_block.append(raw_line)
    check_hash_block(path, current_block)

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = PIN_RE.match(raw_line)
        if match:
            pins[canonical_name(match.group(1))] = match.group(2)
    return pins


def check_hash_block(path: Path, block: list[str]) -> None:
    if not block:
        return
    requirement = block[0].split("\\", 1)[0].strip()
    if not any("--hash=sha256:" in line for line in block):
        raise SystemExit(f"{path}: missing SHA-256 hashes for {requirement}")


def require_matching(source: dict[str, str], locked: dict[str, str], label: str) -> None:
    mismatches = {
        name: {"required": version, "locked": locked.get(name)}
        for name, version in source.items()
        if locked.get(name) != version
    }
    if mismatches:
        raise SystemExit(f"{label} lock drift: {mismatches}")


def main() -> None:
    runtime_source, runtime_includes = source_pins(BACKEND_ROOT / "requirements.txt")
    dev_source, dev_includes = source_pins(BACKEND_ROOT / "requirements-dev.txt")
    audit_source, audit_includes = source_pins(BACKEND_ROOT / "requirements-audit.txt")
    runtime_lock = lock_pins(BACKEND_ROOT / "requirements.lock")
    dev_lock = lock_pins(BACKEND_ROOT / "requirements-dev.lock")
    audit_lock = lock_pins(BACKEND_ROOT / "requirements-audit.lock")

    if runtime_includes:
        raise SystemExit("requirements.txt must not include another requirements file")
    if dev_includes != ["requirements.txt"]:
        raise SystemExit("requirements-dev.txt must include exactly '-r requirements.txt'")
    if audit_includes:
        raise SystemExit("requirements-audit.txt must not include another requirements file")

    require_matching(runtime_source, runtime_lock, "runtime direct dependency")
    require_matching(runtime_source, dev_lock, "runtime dependency in dev")
    require_matching(dev_source, dev_lock, "dev direct dependency")
    require_matching(runtime_lock, dev_lock, "runtime transitive dependency in dev")
    require_matching(audit_source, audit_lock, "audit direct dependency")
    if "pip" not in audit_lock:
        raise SystemExit(
            "requirements-audit.lock must hash-pin pip because pip-audit imports pip internals"
        )
    print(
        "Dependency locks consistent: "
        f"{len(runtime_lock)} runtime packages, {len(dev_lock)} dev packages, "
        f"{len(audit_lock)} audit packages, all hash-pinned."
    )


if __name__ == "__main__":
    main()
