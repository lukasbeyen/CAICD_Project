"""How the FoM evolves during a run, per hyperparameter: one plot column per hyperparameter, the base run plus the runs
that change only that hyperparameter.

    cd CAD && python analysis/fom_evolution.py A_base_1thread A_      # base run, then the prefix of the other runs

Top row:    the best FoM found so far, against the simulation number (what the course's max_reward.png shows)
Bottom row: the mean step reward of the last 500 simulations (is the agent still proposing good designs?)
Also prints both at 1000, 2000, ..., 5000 simulations. Saves output_figs/fom_evolution_<prefix>.png.
"""
import json
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

RUNS = 'runs'
HYPERPARAMETERS = {'noise_sigma': 'exploration noise σ', 'batch_size': 'batch size', 'w': 'warm-up steps w',
                   'pi_lr': 'actor learning rate', 'q_lr': 'critic learning rate'}
COLORS = {'base': '#2a78d6', 'lower': '#eb6834', 'higher': '#1baf7a'}  # validated palette (dataviz skill)
WINDOW = 500
CHECKPOINTS = [1000, 2000, 3000, 4000, 5000]


def load(run):
    designs = pd.read_csv(os.path.join(RUNS, run, 'designs.csv'))
    with open(os.path.join(RUNS, run, 'hyperparameters.json')) as f:
        hyperparameters = json.load(f)
    steps = designs[designs.step > 0].set_index('sim')  # the rewarded designs (reset designs have no reward)
    curves = pd.DataFrame({'best': steps.reward.cummax(),
                           'mean': steps.reward.rolling(WINDOW, min_periods=WINDOW // 2).mean()})
    return hyperparameters, curves


if __name__ == '__main__':
    base_run, prefix = sys.argv[1], sys.argv[2]
    base, base_curves = load(base_run)
    others = sorted(r for r in os.listdir(RUNS) if r.startswith(prefix) and r != base_run
                    and os.path.isfile(os.path.join(RUNS, r, 'hyperparameters.json')))
    runs = {r: load(r) for r in others}

    fig, axes = plt.subplots(2, len(HYPERPARAMETERS), figsize=(18, 7), sharex=True, sharey='row')
    rows = []
    for col, (name, title) in enumerate(HYPERPARAMETERS.items()):
        # the runs that differ from the base run in this hyperparameter only
        variants = [(r, hp, c) for r, (hp, c) in runs.items()
                    if hp[name] != base[name] and all(hp[o] == base[o] for o in HYPERPARAMETERS if o != name)]
        lines = [('base', base[name], base_run, base_curves)]
        lines += [('lower' if hp[name] < base[name] else 'higher', hp[name], r, c) for r, hp, c in variants]
        for role, value, run, curves in sorted(lines, key=lambda line: line[1]):
            label = f'{value:g}' + (' (base)' if role == 'base' else '')
            axes[0, col].plot(curves.index, curves.best, color=COLORS[role], lw=2, label=label)
            axes[1, col].plot(curves.index, curves['mean'], color=COLORS[role], lw=2, label=label)
            at = [curves.loc[:sim] for sim in CHECKPOINTS]
            rows.append({'hyperparameter': name, 'value': value, 'run': run,
                         **{f'best@{sim}': round(a.best.iloc[-1], 3) for sim, a in zip(CHECKPOINTS, at)},
                         **{f'mean@{sim}': round(a['mean'].iloc[-1], 2) for sim, a in zip(CHECKPOINTS, at)}})
        axes[0, col].set_title(title)
        axes[0, col].legend(frameon=False, fontsize=9)
        axes[1, col].set_xlabel('simulation')
    axes[0, 0].set_ylabel('best FoM so far')
    axes[0, 0].set_ylim(-0.5, 0.8)  # zoom: the first random designs start near -4
    axes[1, 0].set_ylabel(f'mean reward, last {WINDOW} sims')
    for ax in axes.flat:
        ax.grid(color='#e6e6e3', lw=0.8)
        ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    os.makedirs('output_figs', exist_ok=True)
    path = os.path.join('output_figs', f'fom_evolution_{prefix.rstrip("_")}.png')
    fig.savefig(path, dpi=120)

    with pd.option_context('display.width', 250, 'display.max_columns', 20):
        print(pd.DataFrame(rows).set_index(['hyperparameter', 'value']))
    print('saved', path)
