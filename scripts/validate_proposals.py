#!/usr/bin/env python3
import json, sys, pathlib
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "proposal.schema.json"
if not SCHEMA_PATH.exists():
    print(f"[ERROR] Schema not found: {SCHEMA_PATH}", file=sys.stderr)
    sys.exit(1)
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

def is_candidate(p: pathlib.Path) -> bool:
    n = p.name.lower()
    return p.suffix == ".json" and ("proposal" in n or "提案" in n)

def main():
    candidates = [p for p in ROOT.rglob("*.json") if is_candidate(p)]
    if not candidates:
        print("No proposal-like JSON found. OK")
        return
    errs = 0
    for p in candidates:
        try:
            Draft202012Validator(SCHEMA).validate(json.loads(p.read_text(encoding="utf-8")))
            print(f"[OK] {p}")
        except Exception as e:
            errs += 1
            print(f"[FAIL] {p}: {e}")
    if errs:
        sys.exit(1)

if __name__ == "__main__":
    main()
