"""The final milestone 3 results (PDF "Finalize and Report"): the two required plots and the Solutions folder.

    cd CAD && python analysis/final_results.py B_pilr_w_s123456 B_pilr_w_s1 B_pilr_w_s2

The first run is the one whose Pareto front goes into Solutions/ (one run = the solutions after 5k simulations).
1) output_figs/final_max_fom.png    the maximum FoM reached against the simulation number, one line per run (seed)
2) output_figs/final_pareto.png     the current-area Pareto front of the first run: every design that met all specs,
                                    the Pareto designs highlighted
3) ../Solutions/                    the netlists of the Pareto designs + Solutions.csv (parameters, specs, reward).
                                    Next to CAD/, not in it: on macOS (case-insensitive) Solutions/ and the course's
                                    CAD/solutions/ would be the same folder.
"""
import os
import shutil
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

RUNS = 'runs'
SOLUTIONS = os.path.join('..', 'Solutions')
COLORS = ['#2a78d6', '#eb6834', '#1baf7a']  # validated palette (dataviz skill)
MUTED = '#b5b4ad'


def load(run):
    designs = pd.read_csv(os.path.join(RUNS, run, 'designs.csv'))
    return designs[designs.step > 0]  # the rewarded designs (reset designs have no reward)


def pareto_front(feasible):
    # a design is on the front if no other design has both a smaller (or equal) area and a smaller (or equal) current
    points = feasible[['area', 'current']].values
    on_front = [not any(a <= area and c <= current and (a < area or c < current) for a, c in points)
                for area, current in points]
    return feasible[on_front].sort_values('area')


def plot_max_fom(runs):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for run, color in zip(runs, COLORS):
        steps = load(run)
        best = steps.reward.cummax()
        ax.plot(steps.sim, best, color=color, lw=2, label=f'{run}  (best {best.iloc[-1]:.3f})')
    ax.set_xlabel('simulation')
    ax.set_ylabel('maximum FoM reached')
    ax.set_ylim(-0.5, 0.8)  # zoom: the first random designs start near -4
    ax.set_title('TD3, tuned hyperparameters: maximum FoM within 5000 simulations')
    ax.legend(frameon=False, loc='lower right')
    ax.grid(color='#e6e6e3', lw=0.8)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join('output_figs', 'final_max_fom.png'), dpi=150)


def plot_pareto(run, feasible, front):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(feasible.area * 1e12, feasible.current * 1e6, s=10, color=MUTED, label='met all specs')
    ax.step(front.area * 1e12, front.current * 1e6, where='post', color=COLORS[0], lw=2)
    ax.scatter(front.area * 1e12, front.current * 1e6, s=40, color=COLORS[0], edgecolor='white', linewidth=1.5,
               zorder=3, label=f'Pareto front ({len(front)} designs)')
    best = feasible.loc[feasible.reward.idxmax()]
    ax.scatter(best.area * 1e12, best.current * 1e6, s=90, marker='*', color=COLORS[1], edgecolor='white',
               linewidth=1, zorder=4, label=f'best FoM {best.reward:.3f}')
    ax.set_xlabel('area [µm²]')
    ax.set_ylabel('current [µA]')
    ax.set_title(f'Current-area Pareto front ({run}, 5000 simulations)')
    ax.legend(frameon=False)
    ax.grid(color='#e6e6e3', lw=0.8)
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join('output_figs', 'final_pareto.png'), dpi=150)


def write_solutions(run, front):
    if os.path.isdir(SOLUTIONS):
        shutil.rmtree(SOLUTIONS)  # always the front of this run only
    os.makedirs(SOLUTIONS)
    for netlist in front.netlist:
        shutil.copy(os.path.join(RUNS, run, 'feasible_netlists', netlist), SOLUTIONS)
    params = list(pd.read_csv(os.path.join(RUNS, run, 'designs.csv'), nrows=0).columns[5:25])  # the 20 sizes
    specs = ['area', 'current', 'gain', 'noise', 'phm', 'slewRate', 'ugbw']
    front[['sim', 'netlist'] + params + specs + ['reward']].to_csv(os.path.join(SOLUTIONS, 'Solutions.csv'),
                                                                   index=False)


if __name__ == '__main__':
    runs = sys.argv[1:]
    os.makedirs('output_figs', exist_ok=True)
    plot_max_fom(runs)
    steps = load(runs[0])
    feasible = steps[steps.hard_satisfied == True]
    front = pareto_front(feasible.drop_duplicates(subset=['area', 'current']))
    plot_pareto(runs[0], feasible, front)
    write_solutions(runs[0], front)
    with pd.option_context('display.width', 200):
        print(front[['sim', 'area', 'current', 'gain', 'phm', 'slewRate', 'ugbw', 'noise', 'reward']].to_string(index=False))
    print(f'{len(front)} Pareto designs of {len(feasible)} that met all specs -> {os.path.abspath(SOLUTIONS)}')
