#!/usr/bin/env python3
"""Build ReadablePassiveNames: patch visible English passive-skill names in
DT_SkillNameText_Common, then package a _P.pak.

Usage:
    python scripts/build_passives.py

Pipeline: vanilla cooked asset -> binary-safe string patch -> repak pack.
"""

import csv
import hashlib
import os
import argparse
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import palmod

BASE_JSON = ROOT / "source" / "DT_SkillNameText_Common.json"
PASSIVE_JSON = ROOT / "source" / "DT_PassiveSkill_Main.json"
CSV = ROOT / "source" / "renamed-passives.csv"
PATCHED_JSON = ROOT / "build" / "patched" / "DT_SkillNameText_Common.json"
STAGING = ROOT / "build" / "staging"
DIST = ROOT / "dist"
MAPPINGS = ROOT / "mappings" / "Mappings.usmap"
DOTNET = Path.home() / ".dotnet" / "dotnet.exe"
UASSETJSON = ROOT / "tools" / "UassetJson" / "bin" / "Release" / "net10.0" / "uassetjson.dll"
REPAK = ROOT / "tools" / "repak" / "repak.exe"

GAME_PAK = Path(os.environ.get(
    "PALWORLD_PAK",
    r"C:\Program Files (x86)\Steam\steamapps\common\Palworld\Pal\Content\Paks\Pal-Windows.pak",
))
GAME_UEASSET = Path(os.environ.get(
    "PALWORLD_UEASSET",
    r"C:\Program Files (x86)\Steam\steamapps\common\Palworld\Pal\Content\Paks\~mods",
))

ENV = {**os.environ, "DOTNET_ROOT": str(Path.home() / ".dotnet")}
PAK_NAME = "ReadablePassiveNames_P.pak"
EFFECTS_ONLY_PAK_NAME = "ReadablePassiveNames_EffectsOnly_P.pak"


def run(*cmd):
    subprocess.run([str(c) for c in cmd], check=True, env=ENV)


def fresh_base():
    """Re-extract and re-decompile the current game table so rebuilds always
    start from the latest vanilla data."""
    data_dir = ROOT / "gamedata"
    if data_dir.exists():
        for p in data_dir.rglob("*"):
            if p.is_file():
                p.unlink()
        for p in data_dir.rglob("*"):
            if p.is_dir():
                p.rmdir()
    run(REPAK, "unpack",
        "--include", "Pal/Content/L10N/en/Pal/DataTable/Text/DT_SkillNameText_Common.*",
        "--output", data_dir, GAME_PAK)
    src = data_dir / "Pal/Content/L10N/en/Pal/DataTable/Text/DT_SkillNameText_Common"
    run(DOTNET, UASSETJSON, "tojson", src.with_suffix(".uasset"), BASE_JSON, MAPPINGS)


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def patch_vanilla_binary(uasset, uexp, plan, table_asset):
    """Patch the cooked text strings without reserializing the whole export."""
    data = bytearray(uexp.read_bytes())
    for entry in plan:
        internal_id = entry["internal_id"].strip()
        replacement = entry["replacement_name"].strip().encode("utf-8")
        marker = f"PASSIVE_{internal_id}_TextData".encode("ascii")
        marker_at = data.find(marker)
        if marker_at < 0:
            raise RuntimeError(f"missing text record: {internal_id}")
        length_at = marker_at + len(marker) + 1
        old_length = struct.unpack_from("<i", data, length_at)[0]
        if old_length < 0:
            encoding = "utf-16-le"
            old_bytes = -old_length * 2
            encoded = replacement.decode("utf-8").encode(encoding) + b"\0\0"
            new_length = -(len(replacement.decode("utf-8")) + 1)
        else:
            encoding = "utf-8"
            old_bytes = old_length
            encoded = replacement + b"\0"
            new_length = len(encoded)
        data[length_at:length_at + 4 + old_bytes] = struct.pack("<i", new_length) + encoded

    new_serial_size = len(data) - 4
    old_serial_size = table_asset["Exports"][0]["SerialSize"]
    asset_data = bytearray(uasset.read_bytes())
    old_bytes = struct.pack("<i", old_serial_size)
    positions = [
        i for i in range(len(asset_data) - 3)
        if asset_data[i:i + 4] == old_bytes
    ]
    if not positions:
        raise RuntimeError("could not locate export SerialSize in uasset")
    serial_at = max(positions)
    asset_data[serial_at:serial_at + 4] = struct.pack("<i", new_serial_size)
    uasset.write_bytes(asset_data)
    uexp.write_bytes(data)


EFFECT_LABELS = {
    "ShotAttack": "ATK",
    "Defense": "DEF",
    "CraftSpeed": "WRK",
    "MoveSpeed": "Move",
    "MaxHP": "HP",
    "SwimSpeed": "Swim",
    "Mining": "Mine",
    "Logging": "Logg",
    "PalSP_Increase": "Stamina",
    "Sanity_Decrease": "SAN",
    "FullStomatch_Decrease": "Hunger",
    "ActiveSkillCoolTime_Decrease": "Cooldown",
    "AutoHPRegeneRate": "HP Regen",
    "BreedSpeed": "Breed",
    "BreedSpeed_InBaseCamp": "Base Breed",
    "ExplosionResist": "Explosion Resist",
    "LifeSteal": "Lifesteal",
    "PlayerSP_DecreaseRate": "Stamina Drain",
    "ReloadSpeedUp": "Reload",
    "RideJumpCount_Increase": "Jumps",
    "SelfDeathAddItemDrop": "Drop",
    "ShopBuyPrice_Money_Increase": "Buy$",
    "ShopSellPrice_Money_Increase": "Sell$",
    "WorkSuitabilityAddRank_MonsterFarm": "Farm Rank",
    "PalEggHatchingSpeed": "Hatch",
    "ResistAdditionalEffect_Burn": "Burn Resist",
    "ResistAdditionalEffect_Poison": "Poison Resist",
    "Nocturnal": "Night",
    "NightOwl": "Night",
    "NonKilling": "No Kill",
    "WorldTreeDecayImmunity": "No Decay",
}

SHORT_LABELS = {
    "PAL_Sanity_Down_3": "Immovable King",
    "CraftSpeed_up3": "Master Crafter",
    "ElementBoost_Dark_2_PAL": "Underworld Lord",
    "WorldTree_DEF": "Meat Shield",
    "TrainerDEF_UP_1": "Stronghold",
    "WorldTree_ATK": "Twin-Edged Blade",
    "ElementResist_Earth_1_PAL": "Earth Resistant",
    "TrainerWorkSpeed_UP_1": "Motivator",
    "ElementBoost_Dragon_1_PAL": "Dragon Blood",
    "MutationPal_Mutant": "Idiosyncratic",
    "MutationPal_Immortal": "Immortal",
    "WorldTree_ATK_DEF": "Destruction",
    "Alien": "Otherworldly",
    "WorldTree_FullStomach": "Seedbed",
    "Nushi": "Lunker",
}

NO_VALUE_EFFECTS = {
    "LeanBackInvalid_ForPassiveSkill",
    "KnockbackInvalid_ForPassiveSkill",
}
NO_PERCENT_EFFECTS = {"RideJumpCount_Increase", "WorkSuitabilityAddRank_MonsterFarm"}


def format_value(value):
    try:
        number = float(str(value).lstrip("+"))
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return f"{int(number):+d}"
    return f"{number:+g}"


def effect_label(effect):
    if effect in EFFECT_LABELS:
        return EFFECT_LABELS[effect]
    for prefix, label in (
        ("ElementBoost_", ""),
        ("ElementResist_", "")
    ):
        if effect.startswith(prefix):
            element = effect[len(prefix):]
            element = {"Aqua": "Water", "Electricity": "Electric"}.get(element, element)
            return f"{element}{' Resist' if prefix.endswith('Resist_') else ''}"
    return None


def readable_plan(asset, effects_only=False):
    names = {r["Name"]: r for r in palmod.rows(asset)}
    passive = palmod.load(PASSIVE_JSON)
    with open(CSV, newline="", encoding="utf-8") as f:
        overrides = {r["internal_id"].strip(): r for r in csv.DictReader(f)}

    plan = []
    for row in palmod.rows(passive):
        values = {p["Name"]: p.get("Value") for p in row["Value"]}
        internal_id = row["Name"]
        if values.get("Category") != "SortDisplayable":
            continue
        name_row = names.get(f"PASSIVE_{internal_id}")
        if name_row is None:
            continue
        current = palmod.prop(name_row, "TextData").get("CultureInvariantString")
        if internal_id in overrides and not effects_only:
            replacement = overrides[internal_id]["replacement_name"].strip()
            expected = overrides[internal_id]["original_name"].strip()
        else:
            expected = current
            base = SHORT_LABELS.get(internal_id, current)
            effect_groups = []
            for index in range(1, 5):
                effect = values.get(f"EffectType{index}")
                if not effect or effect in NO_VALUE_EFFECTS:
                    continue
                label = effect_label(effect)
                if label is None:
                    continue
                value = values.get(f"EffectValue{index}")
                formatted = format_value(value)
                if formatted in {"+0", "0"} and effect not in {
                    "Nocturnal", "NightOwl", "NonKilling", "WorldTreeDecayImmunity"
                }:
                    continue
                if formatted in {"+0", "0"}:
                    effect_groups.append(([label], "", ""))
                    continue
                unit = "" if effect in NO_PERCENT_EFFECTS else "%"
                key = (formatted, unit)
                for labels, group_value, group_unit in effect_groups:
                    if (group_value, group_unit) == key:
                        labels.append(label)
                        break
                else:
                    effect_groups.append(([label], formatted, unit))
            effects = [
                f"{'/'.join(labels)} {value}{unit}" if value else labels[0]
                for labels, value, unit in effect_groups
            ]
            if effects_only:
                replacement = " | ".join(effects) if effects else base
            else:
                replacement = f"{base} [{' | '.join(effects)}]" if effects else base
        plan.append({
            "internal_id": internal_id,
            "original_name": expected,
            "replacement_name": replacement,
        })
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--effects-only",
        action="store_true",
        help="build a separate pak containing only effect annotations",
    )
    args = parser.parse_args()

    if not BASE_JSON.exists():
        fresh_base()

    asset = palmod.load(BASE_JSON)
    table = {r["Name"]: r for r in palmod.rows(asset)}

    plan = readable_plan(asset, effects_only=args.effects_only)

    changed = 0
    warnings = []
    for entry in plan:
        internal_id = entry["internal_id"].strip()
        expected = entry["original_name"].strip()
        replacement = entry["replacement_name"].strip()
        key = f"PASSIVE_{internal_id}"
        row = table.get(key)
        if row is None:
            warnings.append(f"MISSING ROW: {key}")
            continue
        text_prop = palmod.prop(row, "TextData")
        current = text_prop.get("CultureInvariantString")
        if current is None:
            warnings.append(f"NO TEXT STRING: {key}")
            continue
        if current != expected:
            warnings.append(
                f"NAME MISMATCH {key}: table has {current!r}, CSV expects {expected!r} "
                f"- patching anyway"
            )
        text_prop["CultureInvariantString"] = replacement
        changed += 1

    if not changed:
        palmod.save(asset, PATCHED_JSON)
        print("No passive names changed.")
        sys.exit(1)

    PATCHED_JSON.parent.mkdir(parents=True, exist_ok=True)
    palmod.save(asset, PATCHED_JSON)
    for w in warnings:
        print(f"WARN: {w}")
    mode = "effects-only" if args.effects_only else "name-inclusive"
    print(f"Patched {changed} visible passive names ({mode}).")

    vanilla = ROOT / "build" / "vanilla"
    if vanilla.exists():
        shutil.rmtree(vanilla)
    run(REPAK, "unpack",
        "--include", "Pal/Content/L10N/en/Pal/DataTable/Text/DT_SkillNameText_Common.*",
        "--output", vanilla, GAME_PAK)

    vanilla_table = vanilla / "Pal/Content/L10N/en/Pal/DataTable/Text/DT_SkillNameText_Common"
    staging_table = STAGING / "Pal/Content/L10N/en/Pal/DataTable/Text/DT_SkillNameText_Common"
    staging_table.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(vanilla_table.with_suffix(".uasset"), staging_table.with_suffix(".uasset"))
    shutil.copy2(vanilla_table.with_suffix(".uexp"), staging_table.with_suffix(".uexp"))
    patch_vanilla_binary(
        staging_table.with_suffix(".uasset"),
        staging_table.with_suffix(".uexp"),
        plan,
        asset,
    )

    # Sanity: the written .uexp must contain the replacement strings.
    uexp = staging_table.with_suffix(".uexp")
    blob = uexp.read_bytes()
    for entry in plan:
        replacement = entry["replacement_name"].strip()
        assert (
            replacement.encode("utf-8") in blob
            or replacement.encode("utf-16-le") in blob
        ), (
            f"replacement not found in uexp: {entry['replacement_name']}"
        )

    DIST.mkdir(exist_ok=True)
    pak = DIST / (EFFECTS_ONLY_PAK_NAME if args.effects_only else PAK_NAME)
    if pak.exists():
        pak.unlink()
    run(REPAK, "pack", "--version", "V11", STAGING, pak)
    print(f"OK -> {pak} ({pak.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
