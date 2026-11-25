#!/usr/bin/env python3
"""Pre-launch i18n key parity and release hygiene auditor (Python 3 stdlib only)."""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "build", "dist", ".gradle", "__pycache__", ".venv", "venv"}


def parse_android_strings(xml_path: Path) -> dict[str, str]:
    try:
        root = ET.parse(xml_path).getroot()
        out = {}
        for el in root.findall("string"):
            name = el.attrib.get("name")
            if name and el.attrib.get("translatable", "true").lower() != "false":
                out[name] = (el.text or "").strip()
        return out
    except ET.ParseError:
        return {}


def flatten_json(obj, prefix: str = "") -> dict[str, str]:
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(flatten_json(v, key))
    else:
        out[prefix] = str(obj)
    return out


def cmd_i18n(root: Path, output: Path) -> None:
    if not root.exists():
        print(f"Error: root not found: {root}", file=sys.stderr)
        sys.exit(1)

    android_files = []
    json_locales = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        dp = Path(dirpath)
        for f in filenames:
            fp = dp / f
            if f == "strings.xml" and dp.name.startswith("values"):
                android_files.append(fp)
            elif f.endswith(".json") and dp.name in {"locales", "i18n", "translations"}:
                json_locales.append(fp)

    android_report = {}
    base_xml = next((p for p in android_files if p.parent.name == "values"), None)
    if base_xml:
        base_keys = parse_android_strings(base_xml)
        android_report["base_file"] = str(base_xml)
        android_report["base_key_count"] = len(base_keys)
        android_report["locales"] = {}
        for p in sorted(android_files):
            if p == base_xml:
                continue
            loc_keys = parse_android_strings(p)
            missing = sorted(set(base_keys) - set(loc_keys))
            extra = sorted(set(loc_keys) - set(base_keys))
            android_report["locales"][p.parent.name] = {
                "file": str(p),
                "total_keys": len(loc_keys),
                "missing_count": len(missing),
                "extra_count": len(extra),
                "missing_keys": missing[:100],
                "extra_keys": extra[:100],
            }

    json_report = {}
    if json_locales:
        base_json = next((p for p in json_locales if p.stem.lower() in {"en", "en-us", "en_us"}), json_locales[0])
        try:
            base_map = flatten_json(json.loads(base_json.read_text()))
        except Exception:
            base_map = {}
        json_report["base_file"] = str(base_json)
        json_report["base_key_count"] = len(base_map)
        json_report["locales"] = {}
        for p in sorted(json_locales):
            if p == base_json:
                continue
            try:
                loc_map = flatten_json(json.loads(p.read_text()))
            except Exception:
                loc_map = {}
            missing = sorted(set(base_map) - set(loc_map))
            extra = sorted(set(loc_map) - set(base_map))
            json_report["locales"][p.stem] = {
                "file": str(p),
                "total_keys": len(loc_map),
                "missing_count": len(missing),
                "extra_count": len(extra),
                "missing_keys": missing[:100],
                "extra_keys": extra[:100],
            }

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "android_i18n": android_report,
        "json_i18n": json_report,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(f"Success! i18n parity audit written to: {output}")


def cmd_hygiene(root: Path, output: Path) -> None:
    if not root.exists():
        print(f"Error: root not found: {root}", file=sys.stderr)
        sys.exit(1)

    manifests = []
    findings = {"debug_flags": [], "localhost_urls": [], "placeholder_ids": [], "todo_count": 0}
    code_exts = {".kt", ".java", ".swift", ".ts", ".tsx", ".js", ".jsx", ".py", ".xml", ".json", ".gradle", ".kts"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            fp = Path(dirpath) / f
            if f == "AndroidManifest.xml":
                txt = fp.read_text(errors="ignore")
                perms = re.findall(r'android:name="(android\.permission\.[^"]+)"', txt)
                manifests.append({
                    "file": str(fp),
                    "permissions": sorted(set(perms)),
                    "debuggable_true": 'android:debuggable="true"' in txt,
                    "cleartext_true": 'android:usesCleartextTraffic="true"' in txt,
                })
            if fp.suffix.lower() in code_exts and fp.stat().st_size < 512_000:
                txt = fp.read_text(errors="ignore")
                findings["todo_count"] += len(re.findall(r"\b(?:TODO|FIXME)\b", txt))
                if "http://localhost" in txt or "http://127.0.0.1" in txt:
                    findings["localhost_urls"].append(str(fp))
                if "com.example." in txt:
                    findings["placeholder_ids"].append(str(fp))
                if 'android:debuggable="true"' in txt:
                    findings["debug_flags"].append(str(fp))

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "android_manifests": manifests,
        "hygiene_findings": {
            "debug_flags": findings["debug_flags"][:30],
            "localhost_urls": findings["localhost_urls"][:30],
            "placeholder_ids": findings["placeholder_ids"][:30],
            "todo_count": findings["todo_count"],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(f"Success! Pre-release hygiene audit written to: {output} (manifests={len(manifests)}, todos={findings['todo_count']})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Adversarial Launch & Pre-Release Audit CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_i = sub.add_parser("i18n", help="Check localization key parity across locales")
    p_i.add_argument("--root", required=True, type=Path)
    p_i.add_argument("--output", required=True, type=Path)

    p_h = sub.add_parser("hygiene", help="Check permissions, debug flags, and pre-release hygiene")
    p_h.add_argument("--root", required=True, type=Path)
    p_h.add_argument("--output", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "i18n":
        cmd_i18n(args.root, args.output)
    elif args.command == "hygiene":
        cmd_hygiene(args.root, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
