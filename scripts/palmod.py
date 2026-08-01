"""Helpers for editing Palworld DataTables represented as UAssetAPI JSON."""

import json
import re


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(asset, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asset, f, indent=2, ensure_ascii=False)


def rows(asset):
    return asset["Exports"][0]["Table"]["Data"]


def prop(row, name):
    for p in row["Value"]:
        if p["Name"] == name:
            return p
    raise KeyError(f"prop {name} absent from row {row['Name']}")


def get(row, name):
    return prop(row, name).get("Value")


def set_(asset, row, name, value):
    p = prop(row, name)
    p["Value"] = value
    if isinstance(value, str):
        ensure_name(asset, value)


def _fname_key(name):
    m = re.match(r"^(.*)_(0|[1-9][0-9]*)$", name)
    return m.group(1) if m else name


def ensure_name(asset, name):
    nm = asset.get("NameMap")
    if nm is None:
        return
    key = _fname_key(name)
    if key not in nm and name not in nm:
        nm.append(key)
