# Readable Passive Names

A Palworld client mod that annotates the 115 player-visible passive-skill names
with their important effects. Long names use compact aliases where needed so
they remain usable in Palworld's passive-skill UI.

## Install

1. Download `ReadablePassiveNames_P.pak` from the repository's Releases page.
2. Create the `~mods` directory if it does not exist:

   ```text
   Palworld/Pal/Content/Paks/~mods/
   ```

3. Copy `ReadablePassiveNames_P.pak` into that directory.
4. Start Palworld.

The mod changes English passive-name text only. Remove the pak from `~mods` to
uninstall it.

## Build

Building requires:

- Windows
- Python 3.10 or newer
- .NET 10 SDK
- A Steam installation of Palworld

The repository includes the current source data snapshot, UAssetAPI source, and
the repak executable used by the build. From the repository root, run:

```powershell
python scripts/build_passives.py
```

The generated pak is written to `dist/ReadablePassiveNames_P.pak`.

An alternate effects-only build is available for users who prefer to hide the
original passive names. It removes the name and square brackets, leaving labels
such as `ATK/DEF +15% | WRK +20%`:

```powershell
python scripts/build_passives.py --effects-only
```

That variant is written to `dist/ReadablePassiveNames_EffectsOnly_P.pak`. Only
install one variant at a time because both paks replace the same game asset.

If Palworld is installed somewhere other than the default Steam path, set the
pak path before building:

```powershell
$env:PALWORLD_PAK = 'D:\Games\Palworld\Pal\Content\Paks\Pal-Windows.pak'
python scripts/build_passives.py
```

The build starts from the vanilla asset and patches only the targeted cooked
strings. It deliberately avoids full UAssetAPI export reserialization because
that can produce assets Palworld cannot load.

## Compatibility

This release was tested with the Steam Windows build of Palworld using Unreal
Engine 5.1 data. Game updates can change the asset layout or passive list. If
the game crashes after an update, remove the pak first and rebuild against the
updated game data.

## Credits and Legal

Palworld and its game assets are property of Pocketpair. This is an unofficial
community mod and is not affiliated with Pocketpair.

The build tooling uses [UAssetAPI](https://github.com/atenfyr/UAssetAPI) and
[repak](https://github.com/trumank/repak). Their license and notice files are
included with the vendored tools.

## Future Work: Passive Info Overlay

The current mod only changes passive-name text. It cannot add passive details
to screens that show a passive badge but do not expose the existing detail
tooltip, such as Pal condensation.

A future improved version could use one of these approaches:

- Modify or reuse the existing Unreal UMG passive-detail widget and add it to
  other screens. This is difficult because cooked Blueprint changes are fragile
  and must preserve the original asset layout.
- Create a runtime overlay with UE4SS, Lua, or a native plugin. This is the most
  flexible option: hook UI creation and focus/selection events, identify the
  passive ID, then display its effects beside the badge. It will require
  maintenance after game updates and may need multiplayer or anti-cheat review.
- Build an external OCR-based overlay. This is easier to prototype but less
  reliable and less integrated than an in-game widget.

The recommended prototype is a runtime overlay for the condensation screen:
identify the passive badge widget and its underlying passive ID, display a
small effect panel beside it, and then reuse that logic for storage, party,
breeding, and other screens.

## Effect Label Mappings

The generated annotations use these compact labels:

| Label | Source effect | Meaning |
| --- | --- | --- |
| `ATK` | `ShotAttack` | Attack |
| `DEF` | `Defense` | Defense |
| `WRK` | `CraftSpeed` | Work speed |
| `Move` | `MoveSpeed` | Movement speed |
| `HP` | `MaxHP` | Maximum HP |
| `Swim` | `SwimSpeed` | Swimming speed |
| `Mine` | `Mining` | Mining speed |
| `Logg` | `Logging` | Logging speed |
| `Stamina` | `PalSP_Increase` | Stamina |
| `SAN` | `Sanity_Decrease` | Sanity drain/recovery |
| `Hunger` | `FullStomatch_Decrease` | Hunger drain |
| `Cooldown` | `ActiveSkillCoolTime_Decrease` | Active skill cooldown |
| `HP Regen` | `AutoHPRegeneRate` | HP regeneration |
| `Explosion Resist` | `ExplosionResist` | Explosion resistance |
| `Burn Resist` | `ResistAdditionalEffect_Burn` | Burn resistance |
| `Poison Resist` | `ResistAdditionalEffect_Poison` | Poison resistance |
| `Lifesteal` | `LifeSteal` | Life steal |
| `Reload` | `ReloadSpeedUp` | Reload speed |
| `Jumps` | `RideJumpCount_Increase` | Ride jump count |
| `Drop` | `SelfDeathAddItemDrop` | Death-drop increase |
| `Hatch` | `PalEggHatchingSpeed` | Egg hatching speed |
| `Breed` | `BreedSpeed` | Breeding speed |
| `Base Breed` | `BreedSpeed_InBaseCamp` | Base breeding speed |
| `Farm Rank` | `WorkSuitabilityAddRank_MonsterFarm` | Farm work rank |
| `Buy$` | `ShopBuyPrice_Money_Increase` | Shop buy price |
| `Sell$` | `ShopSellPrice_Money_Increase` | Shop sell price |

Element boosts use the element name directly, for example `Fire +30%` or
`Dragon +30%`. Element resistances append `Resist`, for example `Fire Resist
 +10%` and `Electric Resist +10%`.

Current element-name mappings are:

| Source element | Display name |
| --- | --- |
| `Normal` | `Neutral` |
| `Fire` | `Fire` |
| `Aqua` / `Water` | `Water` |
| `Thunder` / `Electricity` | `Electric` |
| `Leaf` | `Grass` |
| `Ice` | `Ice` |
| `Earth` | `Ground` |
| `Dark` | `Dark` |
| `Dragon` | `Dragon` |

## Support

If you find this mod helpful, consider supporting its development:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/R6R01DV0JD)
