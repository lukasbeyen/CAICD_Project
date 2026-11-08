import argparse
import json
import os
import shutil
import torch
import numpy as np
from td3 import TD3, ReplayBuffer
from circuit_env import CircuitEnv
from datetime import datetime

def readParser():
    parser = argparse.ArgumentParser(description='TD3-based RL for Circuit Sizing')

    parser.add_argument('--seed', type=int, default=123456, metavar='N',
                        help='random seed (default: 123456)')

    parser.add_argument('--noise_sigma', type=float, default="0.1",
                        help='fixed noise sigma added to the deterministic action')

    parser.add_argument('--gamma', type=float, default=0.99, metavar='G',
                        help='discount factor for reward (default: 0.99)')
    
    parser.add_argument('--tau', type=float, default=0.005, metavar='G',
                        help='target smoothing coefficient(τ) (default: 0.005)')
    
    parser.add_argument('--target_update_interval', type=int, default=1, metavar='N',
                        help='Value target update per no. of updates per step (default: 1)')
    
    parser.add_argument('--actor_update_interval', type=int, default=2, metavar='N',
                        help='Actor target update per no. of updates per step (default: 2)')
    
    parser.add_argument('--hidden_size', type=int, default=256, metavar='N',
                        help='hidden size (default: 256)')
    
    parser.add_argument('--batch_size', type=int, default="64", metavar='N',
                        help='hidden size')
    
    parser.add_argument('--w', type=int, default="200", metavar='N',
                        help='number of warmup steps')
    
    parser.add_argument('--T', type=int, default=10_000, metavar='N',
                        help='total training steps (default: 10_000)')

    # CHANGED (not in the course runner): the assignment compares with the baseline within 5k SIMULATIONS and asks for
    # the Pareto solutions after 5k simulations (no hard cap is stated). One episode is 1 reset simulation + 10 step
    # simulations, so --T 10_000 steps would be 11_000 simulations. Training stops at whichever comes first, --T steps
    # or --max_sims simulations, also in the middle of an episode. To go back to the course behaviour: --max_sims 1_000_000.
    parser.add_argument('--max_sims', type=int, default=5000, metavar='N',
                        help='simulation budget: stop after this many ngspice simulations (default: 5000)')
    
    parser.add_argument('--pi_lr', type=float, default="3e-4", metavar='G',
                        help='learning rate')
    
    parser.add_argument('--q_lr', type=float, default="1e-3", metavar='G',
                        help='learning rate')

    parser.add_argument('--replay_size', type=int, default=1000000, metavar='N',
                        help='size of replay buffer (default: 10000000)')

    parser.add_argument('--cuda', default=False, action="store_true",
                        help='run on CUDA (default: True)')
    
    parser.add_argument('--run_id', type=str, default=datetime.now().strftime('%Y-%m-%d--%H-%M-%S'), metavar='N',
                        help='run identifier (default: current time)')
    
    return parser.parse_args()


def train(args, env, agent, env_pool):
    total_steps = warmup_exploration(args, env, env_pool, agent)
    while total_steps < args.T and env.counter < args.max_sims:  # CHANGED: + the simulation budget
        obs = env.reset()
        done = False
        while not done and env.counter < args.max_sims:  # CHANGED: + the simulation budget (may end mid-episode)
            action = agent.select_action(obs)
            next_state, reward, done, info = env.step(action)
            env_pool.push(obs, action, reward, next_state, done)
            obs = next_state
            train_policy(args, env_pool, agent, total_steps)
            total_steps += 1
            # clean up the no_backup folder every 100 steps
            if total_steps % 100 == 0:
                os.system('./clean.sh')
                best = max(env.reward_history, default=float("nan"))
                print(f'steps {total_steps}, simulations {env.counter}, best reward {best:.3f}')



def warmup_exploration(args, env, env_pool, agent):
    step_counter = 0
    while step_counter < args.w and env.counter < args.max_sims:  # CHANGED: + the simulation budget
        obs = env.reset()
        done = False
        while not done and env.counter < args.max_sims:  # CHANGED: + the simulation budget
            action = env.action_space.sample()
            next_state, reward, done, info = env.step(action)
            env_pool.push(obs, action, reward, next_state, done)
            obs = next_state
            step_counter += 1
    return step_counter


def train_policy(args, env_pool, agent, total_steps):
    state, action, next_state, reward, not_done = env_pool.sample(args.batch_size)
    batch = (state, action, next_state, reward, not_done)
    agent.update_parameters(memory_batch=batch, update=total_steps)


def main(args=None):
    if args is None:
        args = readParser()
    # Set random seed
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    # Initial environment
    env = CircuitEnv(run_id=args.run_id)
    # CHANGED: np.random.seed doesn't reach gymnasium's own random generators: seed the env's (random start design
    # of every reset) and the action space's (random warm-up actions)
    env.np_random = np.random.default_rng(args.seed)
    env.action_space.seed(args.seed)
    # CHANGED: keep the circuit definition and this run's hyperparameters with its results
    os.makedirs(env.run_folder, exist_ok=True)
    shutil.copy(os.path.join('ngspice_interface', 'files', 'yaml_files', f'{env.circuit_name}.yaml'), env.run_folder)
    with open(os.path.join(env.run_folder, 'hyperparameters.json'), 'w') as f:
        json.dump(vars(args), f, indent=2)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    # Intial agent
    agent = TD3(state_dim, env.action_space, args)
    # Initial pool for env
    env_pool = ReplayBuffer(state_dim, action_dim, max_size=args.replay_size)
    # Training
    train(args, env, agent, env_pool)
    # CHANGED: the last plots (Pareto front) and the trained networks
    env.finalize()
    agent.save(os.path.join(env.run_folder, 'td3'))
    best = max(env.reward_history, default=float("nan"))
    print(f'done: {env.counter} simulations, best reward {best:.3f}, run folder {env.run_folder}')


if __name__ == "__main__":
    main()