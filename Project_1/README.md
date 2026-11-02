# Lumen Run

A fast arcade game set in a moonlit garden. Guide a moth through the night, gather drifting lights, and avoid the storm wisps. Choose Easy, Normal, or Hard, then play a timed challenge or see how long you can last in Endless mode.

## Run

Requires Python 3 with Tkinter available. No third-party packages are needed.

```bash
python3 main.py
```

## Controls

- `W`, `A`, `S`, `D` or arrow keys: fly
- `Space`: dash
- `P`: pause or resume
- `Esc`: return to the title screen
- `Enter`: visit the market from the title or end screen; start the run from the market
- In the market, `1`, `2`, or `3` buys the displayed upgrade
- Move during the safe opening period, then watch for small warning rings before each storm appears
- On the title screen, `Left` / `Right` (or `A` / `D`) select difficulty
- On the title screen, `M` switches between Timed and Endless mode

## Modes and difficulty

Timed mode asks you to collect 20 lights before time runs out. Endless mode has no timer or light target; your run ends when you lose all your wings. Difficulty changes starting lives, time limit, storm speed, and how quickly more storm wisps appear.

## Market

Collected lights are saved in your light purse between runs. Visit the market before each run to buy an extra wing, a faster dash recharge, or extra time for timed mode. After leaving the market, you have four safe seconds to move away from your spawn point. Storms then arrive one at a time: a small pulsing ring marks each location shortly before the storm appears. Your wallet is stored in `.lumen_run_save.json` in your home folder.

## Libraries

Python standard library: `tkinter`, `random`, `math`, and `time`.