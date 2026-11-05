"""Milestone 4 report: the LLM harness vs. the pure RL sizer, on runtime (PDF "Finalize and Report").

    cd CAD && python analysis/harness_vs_rl.py --harness mcp_20261106_101500_123456 --rl B_pilr_w_s123456

- Harness: runs/<run>/harness_history.csv (one row per simulation; elapsed_s counts from the MCP server start, so it
  includes the LLM's thinking time between tool calls).
- RL: runs/<run>/designs.csv of a td3_runner run; its time comes from the netlist names (TwoStage_<unix time>_...).
1) output_figs/harness_vs_rl.png   maximum FoM reached against wall-clock runtime, one line per run
2) a table: runtime and simulations to reach the first design meeting all specs and FoM 0.5 / 0.6 / best
3) the explainability trace: every simulation that raised the harness's best FoM, with its reason
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

RUNS = 'runs'
COLORS = ['#2a78d6', '#eb6834', '#1baf7a']  # validated palette (dataviz skill)
LEVELS = [0.5, 0.6]


def harness_curve(run):
    rows = pd.read_csv(os.path.join(RUNS, run, 'harness_history.csv'))
    rows = rows[~rows.failed].copy()
    return pd.DataFrame({'minutes': rows.elapsed_s / 60, 'sim': rows.call, 'reward': rows.reward.astype(float),
                         'feasible': rows.hard_satisfied.astype(str) == 'True', 'source': rows.source,
                         'reason': rows.reason.fillna('')})


def rl_curve(run):
    rows = pd.read_csv(os.path.join(RUNS, run, 'designs.csv'))
    seconds = rows.netlist.str.extract(r'TwoStage_(\d+)_')[0].astype(int)
    rows['minutes'] = (seconds - seconds.iloc[0]) / 60
    rows = rows[rows.step > 0]  # the rewarded designs (reset designs have no reward)
    return pd.DataFrame({'minutes': rows.minutes, 'sim': rows.sim, 'reward': rows.reward,
                         'feasible': rows.hard_satisfied == True})


def milestones(curve, best_harness):
    # runtime and simulation count at which a run first reaches each level (None if never)
    reached = {}
    targets = {'first design meeting all specs': curve.feasible}
    for level in LEVELS:
        targets[f'FoM >= {level}'] = curve.reward >= level
    # the exact value (a rounded one could lie above it), only the label is rounded
    targets[f"the harness's best FoM ({best_harness:.3f})"] = curve.reward >= best_harness - 1e-12
    for name, hit in targets.items():
        first = curve[hit].head(1)
        reached[name] = (f'{first.minutes.item():.1f} min / {int(first.sim.item())} sims' if len(first) else 'never')
    return reached


def improvements(curve):
    # the simulations that raised the best FoM: the trace of the decisions that mattered
    best = curve.reward.cummax()
    return curve[curve.reward >= best.shift(fill_value=-float('inf')) + 1e-12]


def plot(curves):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for (label, curve), color in zip(curves.items(), COLORS * 3):
        ax.step(curve.minutes, curve.reward.cummax(), where='post', color=color, lw=2,
                ls='-' if label.startswith('harness') else '--', label=f'{label} (best {curve.reward.max():.3f})')
    ax.set_xlabel('runtime [min]')
    ax.set_ylabel('maximum FoM reached')
    ax.set_ylim(-0.5, 0.8)  # zoom: the first random designs start near -4
    ax.set_title('LLM harness vs. pure RL (TD3): maximum FoM against runtime')
    ax.legend(frameon=False, loc='lower right')
    ax.grid(color='#e6e6e3', lw=0.8)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    os.makedirs('output_figs', exist_ok=True)
    fig.savefig(os.path.join('output_figs', 'harness_vs_rl.png'), dpi=150)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--harness', nargs='+', required=True, help='run folders with a harness_history.csv')
    parser.add_argument('--rl', nargs='+', required=True, help='td3_runner run folders')
    args = parser.parse_args()
    curves = {f'harness {run}': harness_curve(run) for run in args.harness}
    curves.update({f'TD3 {run}': rl_curve(run) for run in args.rl})
    plot(curves)
    best_harness = max(curve.reward.max() for label, curve in curves.items() if label.startswith('harness'))
    table = pd.DataFrame({label: milestones(curve, best_harness) for label, curve in curves.items()})
    with pd.option_context('display.width', 250, 'display.max_colwidth', 120):
        print(table.to_string())
        for run in args.harness:
            print(f'\nDecisions that raised the best FoM ({run}):')
            print(improvements(curves[f'harness {run}'])[['sim', 'minutes', 'source', 'reward', 'feasible', 'reason']]
                  .round(3).to_string(index=False))
    print('saved output_figs/harness_vs_rl.png')
