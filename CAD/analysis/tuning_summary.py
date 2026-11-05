"""Compare TD3 runs: one row per run folder in runs/, from its designs.csv and hyperparameters.json.

    cd CAD && python analysis/tuning_summary.py                  # all runs
    cd CAD && python analysis/tuning_summary.py A_ B_            # only runs whose name starts with A_ or B_

Columns:
    best          the highest reward (FoM) of the run; reset designs are not rewarded
    best@sim      the simulation at which it was found
    first_feas    the simulation of the first design that met all specs
    n_feas        the number of designs that met all specs
    pareto        how many of them are on the current-area Pareto front (no other one has less area AND less current)
    late_mean     the mean step reward of the last 1500 simulations (is the agent still good at the end?)
    failed        failed simulations (of which timeouts)
"""
import json
import os
import sys

import pandas as pd

RUNS = 'runs'
HYPERPARAMETERS = ['noise_sigma', 'batch_size', 'w', 'pi_lr', 'q_lr', 'seed']


def pareto_count(feasible):
    # a design is on the front if no other design has both a smaller (or equal) area and a smaller (or equal) current
    points = feasible[['area', 'current']].drop_duplicates().values
    on_front = 0
    for area, current in points:
        dominated = any(a <= area and c <= current and (a < area or c < current) for a, c in points)
        on_front += not dominated
    return on_front


def summarize(run):
    designs = pd.read_csv(os.path.join(RUNS, run, 'designs.csv'))
    with open(os.path.join(RUNS, run, 'hyperparameters.json')) as f:
        hyperparameters = json.load(f)
    row = {name: hyperparameters[name] for name in HYPERPARAMETERS}
    steps = designs[designs.step > 0]  # the rewarded designs
    feasible = steps[steps.hard_satisfied == True]
    best = steps.loc[steps.reward.idxmax()]
    row.update({
        'run': run,
        'sims': len(designs),
        'best': round(best.reward, 3),
        'best@sim': int(best.sim),
        'first_feas': int(feasible.sim.min()) if len(feasible) else None,
        'n_feas': len(feasible),
        'pareto': pareto_count(feasible) if len(feasible) else 0,
        'late_mean': round(steps[steps.sim > designs.sim.max() - 1500].reward.mean(), 3),
        'failed': f'{int(designs.failed.sum())} ({int(designs.timeout.sum())})',
    })
    return row


if __name__ == '__main__':
    prefixes = sys.argv[1:]
    runs = sorted(run for run in os.listdir(RUNS)
                  if os.path.isfile(os.path.join(RUNS, run, 'designs.csv'))
                  and os.path.isfile(os.path.join(RUNS, run, 'hyperparameters.json'))
                  and (not prefixes or run.startswith(tuple(prefixes))))
    table = pd.DataFrame([summarize(run) for run in runs]).set_index('run')
    with pd.option_context('display.width', 200, 'display.max_columns', 20):
        print(table.sort_values('best', ascending=False))
