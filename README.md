# 🌊 ReeferMadness — Ocean Edition
**v0.27.0 · Reef Aquarium Management Desktop App**

ReeferMadness is a single-file Python desktop application for managing a reef aquarium. It covers the full test-and-dose workflow across three tabs: safe dosing schedule generation, parameter trend graphs with test history, and step-by-step test kit instructions with built-in timers. All data is stored locally in a SQLite database — no account, no internet connection, and no subscription required.

---

## Requirements

| Dependency | Notes |
|---|---|
| Python 3.8+ | 3.9+ recommended |
| tkinter | Included with most Python installs; Ubuntu/Debian: `sudo apt install python3-tk` |
| pandas | `pip install pandas` |
| matplotlib | `pip install matplotlib` |
| SQLite 3 | Bundled with Python — no separate install needed |

> **One-liner install:** `pip install pandas matplotlib`

---

## Installation & Launch

No installer or build step required. The entire application is one `.py` file.

1. Download `reef_commander_improved.py` to any folder
2. Install dependencies: `pip install pandas matplotlib`
3. Run: `python reef_commander_improved.py`

> On first launch, ReeferMadness creates `~/Documents/ReeferMadness/` and initialises the database inside it. All data is written there automatically.

---

## Data Storage

All files are written to `~/Documents/ReeferMadness/`:

| File | Contents |
|---|---|
| `reef_pro_v25.db` | SQLite database — all test logs and custom optimal levels |
| `preferences.txt` | Tank volume preference (persists between sessions) |

> **Back up before clearing:** Use **Export to CSV** in the Trends & Data tab before using Clear All Data.

---

## The Three Tabs

### Tab 1 — Calculators

Houses two calculators that share a single **Tank Volume** entry at the top.

**Rapid Dosing Calculator**
Enter your current reading, your target value, and choose a dosing product. The calculator generates a day-by-day schedule that keeps each daily change within safe limits using two independent safety checks: a dKH-per-day ceiling and a mL-per-gallon-per-day ceiling. The more conservative of the two governs the schedule, and the output shows exactly which limit is binding and why.

**Consumption Rate Calculator**
Enter a start reading, an end reading, the number of days between them, and your current daily dose (if any). The calculator determines how many mL per day your tank is consuming and recommends whether to increase, decrease, or hold your current dose.

**Alkalinity unit auto-detection**
For any Alkalinity field in either calculator, you never select a unit manually. Values ≤ 20 are read as dKH; values > 20 are read as ppm. The label next to the field bolds the active unit so you always know which one is in use. If the start and end values in the Consumption Calculator appear to be in different units, the app blocks the calculation and explains the mismatch.

**Nitrate and Phosphate**
These parameters cannot be corrected by adding a dosing product. Selecting either one in the Rapid Dosing Calculator displays practical management guidance (feeding, water changes, GFO, carbon dosing) instead of generating a schedule.

---

### Tab 2 — Trends & Data

**Parameter Trends**
One chart per parameter showing your historical readings as a line graph. The green shaded band marks the safe range; the dashed line is your target. Click **Refresh Graphs** any time to reload the latest logged data.

**Custom Optimal Levels**
After your first graph load, a Custom Optimal Levels panel appears below the charts. You can set a personalised target for each parameter; the charts and the dosing calculators update immediately. Custom targets are saved to the database and persist between sessions.

**Test History**
A sortable table showing every logged reading. Double-click any row to edit the timestamp, parameter, or value. Right-click for a quick edit/delete menu. Three buttons at the bottom handle **Export to CSV**, **Refresh History**, and **Clear All Data**.

> Clear All Data permanently deletes all test logs and resets custom optimal levels to factory defaults.

---

### Tab 3 — Testing & Logging

**Test Kit Instructions**
Select a parameter and a test kit brand to see numbered, step-by-step instructions. Any step that requires waiting shows a timer button. Tap the button to start an in-line countdown; tap it again to cancel. Steps can be checked off as you complete them.

**Daily Test Log**
A row of entry fields, one per parameter. Fill in whichever readings you have and tap **Save to Log**. Only non-empty fields are saved. Alkalinity uses the same auto-detection described above — the bold unit label updates as you type.

---

## Supported Parameters

| Parameter | Target | Safe Range | Unit | Notes |
|---|---|---|---|---|
| Alkalinity | 8.5 dKH / 152 ppm | 7.5 – 9.5 dKH | dKH or ppm | Auto-detected; unit tag preserved in database |
| Calcium | 420 ppm | 400 – 440 ppm | ppm | |
| Magnesium | 1350 ppm | 1280 – 1420 ppm | ppm | |
| Nitrate | 5 ppm | 2 – 10 ppm | ppm | Tracked and graphed; dosing calculator not applicable |
| Phosphate | 0.03 ppm | 0.01 – 0.08 ppm | ppm | Tracked and graphed; dosing calculator not applicable |

---

## Supported Dosing Products

Pre-loaded with manufacturer-specified concentrations. Select **Custom** in any dropdown to enter your own.

### Alkalinity
| Product | Concentration |
|---|---|
| Fritz RPM Liquid | 1.4 dKH/mL |
| ESV B-Ionic Pt 1 | 1.4 dKH/mL |
| BRS 2-Part | 1.4 dKH/mL |
| Aquaforest Component 1+ | 1.0 dKH/mL |
| Red Sea Foundation B (KH/Alkalinity) | 0.36 dKH/mL |
| Seachem Reef Builder | 0.6 dKH/mL |
| Brightwell Alkalin8.3 | 0.5 dKH/mL |
| Tropic Marin Bio-Calcium | 0.8 dKH/mL |
| Fauna Marin Balling Method Part A | 1.2 dKH/mL |
| Red Sea Reef Foundation ABC+ | 0.4 dKH/mL |
| Triton Core7 Base Elements 1 | 0.9 dKH/mL |
| Aquaforest Reef Mineral Salt | 0.7 dKH/mL |

### Calcium
| Product | Concentration |
|---|---|
| Fritz RPM Liquid | 20 ppm/mL |
| ESV B-Ionic Pt 2 | 20 ppm/mL |
| BRS 2-Part | 20 ppm/mL |
| Aquaforest Component 2+ | 15 ppm/mL |
| Red Sea Foundation C (Ca/Calcium) | 5.5 ppm/mL |
| Seachem Reef Complete | 10 ppm/mL |
| Brightwell Calcion | 12 ppm/mL |
| Tropic Marin Bio-Calcium | 18 ppm/mL |
| Fauna Marin Balling Method Part B | 25 ppm/mL |
| CaribSea ARM Media | 8 ppm/mL |
| Bulk Reef Supply Calcium Hydroxide | 30 ppm/mL |
| Red Sea Reef Foundation ABC+ | 6 ppm/mL |
| Triton Core7 Base Elements 2 | 22 ppm/mL |

### Magnesium
| Product | Concentration |
|---|---|
| Fritz RPM Liquid | 100 ppm/mL |
| ESV B-Ionic Magnesium | 30 ppm/mL |
| BRS Magnesium | 75 ppm/mL |
| Aquaforest Component Mg | 50 ppm/mL |
| Red Sea Foundation A (Mg/Magnesium) | 15 ppm/mL |
| Seachem Reef Magnesium | 25 ppm/mL |
| Brightwell MagnesIon | 40 ppm/mL |
| Tropic Marin Bio-Magnesium | 60 ppm/mL |
| Fauna Marin Balling Method Part C | 80 ppm/mL |
| Triton Core7 Base Elements 3 | 45 ppm/mL |
| Kent Marine Liquid Magnesium | 20 ppm/mL |

---

## Supported Test Kits

Step-by-step instructions and timers are included for all 13 kits below.

### Alkalinity
- Hanna HI772 dKH Checker
- Salifert KH/Alkalinity Kit
- Red Sea Reef Foundation Test Kit
- API KH Test Kit

### Calcium
- Red Sea Pro Calcium Kit
- Salifert Calcium Kit

### Magnesium
- Salifert Magnesium Kit
- Red Sea Magnesium Kit

### Nitrate
- Salifert Nitrate Kit
- API Nitrate Test Kit

### Phosphate
- Hanna HI713 Low Range
- Hanna HI736 Ultra Low Range
- Salifert Phosphate Kit

---

## Dosing Safety Model

The Rapid Dosing Calculator applies two independent safety checks for Alkalinity, and one check for all other parameters. The most conservative result always governs.

| Limit | Value | Logic |
|---|---|---|
| Alk — mL ceiling | 0.5 mL / gallon / day | Equivalent to 5 mL per 10 gallons per day |
| Alk — dKH ceiling | 1.4 dKH / day | Maximum single-day alkalinity change for coral safety |
| Calcium ceiling | 25 ppm / day | `ceil(total change ÷ 25)` determines minimum days |
| Magnesium ceiling | 100 ppm / day | Same formula as calcium |

> The math output in the results box always shows which limit is binding, both candidate day counts, and the full derivation of the daily dose.

---

## Developer Notes

### Debug Output
All verbose console output is gated behind a class-level flag near the top of the file:
```python
DEBUG = False  # set to True to restore verbose console output
```

### Adding a Parameter
Edit only `param_config` in Region 1. Every other part of the app reads it dynamically — no other changes needed.

### Adding a Dosing Product
Add an entry to the `dosing` dict inside the relevant parameter in `param_config`. The value is the product's concentration in the parameter's native unit per mL per gallon.

### Adding a Test Kit
Add a key/list entry to the `kits` dict inside the relevant parameter. Each list item is one step. Include time keywords such as `"3 mins"` or `"exactly 5 minutes"` and the app will automatically attach a countdown timer button to that step.

### Porting to Web / Mobile
The source file opens with a detailed migration guide. In brief: the calculation engine (Region 4) and data layer (Region 6) have no UI dependencies and can be extracted directly into a FastAPI backend. The three tabs map cleanly to React components, and `param_config` can be served as a `/api/config` JSON endpoint unchanged.

---

## Known Limitations

- Single-tank only — one SQLite database per installation
- No cloud sync or multi-device access; data lives in `~/Documents/ReeferMadness/`
- Alkalinity auto-detection uses a fixed threshold of 20: values ≤ 20 are treated as dKH, values > 20 as ppm. Entering a dKH reading above 20 would be misidentified as ppm, though this would represent a dangerously over-dosed tank
- Custom optimal levels for Alkalinity are stored internally in dKH regardless of which unit you type; the display panel converts back to your entered unit for readability

---

*ReeferMadness v0.27.0 · Ocean Edition · Single-file Python desktop app*
