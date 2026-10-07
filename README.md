# Halting Boundary Tracker — Bounded Turing Machine Simulation

Runs a Turing Machine for at most **K** steps. Reaches the halting state in time → **HALTED**; otherwise → **TIMEOUT**.
TIMEOUT does **not** prove the machine never halts — only that it did not halt within the tested boundary K.

## Run on Windows
1. Install Python 3.9+ from python.org (tick "Add Python to PATH"; Tkinter is included).
2. Open Command Prompt in this folder and run: `python main.py`

## Dependencies
The app itself needs only the standard library. `pip install -r requirements.txt` installs PyInstaller (only for building the .exe).

## Create the .exe
Double-click `build_exe.bat` (or run `python -m PyInstaller --onefile --windowed --name HaltingBoundaryTracker main.py`).
Result: `dist\HaltingBoundaryTracker.exe` — works offline.

## Using it
Rule format: `state,read -> next,write,move` (`L`/`R`, `_` = blank, `#` comments).
Buttons: Run (F5, instant), Step (F10), Start/Pause (F6, animated, speed slider), Reset (Ctrl+R), Clear, Load Example.
Edit the inputs, then press Reset to apply changes before stepping again.

## How the simulation works
The tape is a dictionary {position: symbol} (blank elsewhere), so it is unbounded both ways. Each step reads the
symbol under the head, looks up (state, symbol) in the rule table, writes the new symbol, moves the head, changes
state and increments the step counter.

## How the bounded halting mechanism works
Before every transition: if state == HALT → HALTED; else if steps >= K → TIMEOUT; else if no rule exists →
NO TRANSITION; else execute the transition and repeat. A machine that reaches HALT on exactly its K-th step is HALTED.

## Test cases
| # | Machine | Input | K | Expected |
|---|---------|-------|---|----------|
| 1 | Example 1 | 111 | 10 | HALTED, 4 steps, head 4 |
| 2 | Example 1 | 111 | 4 | HALTED (boundary inclusive) |
| 3 | Example 1 | 111 | 3 | TIMEOUT after 3 steps, state q0 |
| 4 | Example 2 | 1 | 10 | TIMEOUT, 10 steps, head 10 |
| 5 | Example 3 | 11 | 50 | HALTED, 6 steps, head moves right then left |
| 6 | `q0,1 -> q0,1,R` only | 11 | 10 | NO TRANSITION at head 2 |
| 7 | Any | any | -5 or abc | Friendly error message |
