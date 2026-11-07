"""Unit tests for the TD3 agent (td3/agent.py): select_action and update_parameters.

No ngspice: the agent only sees tensors. Run from the repo root or CAD/:  python -m pytest -q tests/test_agent.py
"""
import copy
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from gymnasium import spaces

from td3 import TD3, ReplayBuffer
from td3 import agent as agent_module

STATE_DIM, ACTION_DIM = 7, 20  # the circuit env: 7 normalized specs, 20 sizing parameters


def make_agent(noise_sigma=0.1, state_dim=STATE_DIM, action_dim=ACTION_DIM, pi_lr=3e-4, q_lr=1e-3, seed=0):
    # the same arguments td3_runner.py passes (args from argparse)
    torch.manual_seed(seed)
    np.random.seed(seed)
    args = SimpleNamespace(gamma=0.99, tau=0.005, noise_sigma=noise_sigma, actor_update_interval=2,
                           pi_lr=pi_lr, q_lr=q_lr)
    action_space = spaces.Box(low=-1.0, high=1.0, shape=(action_dim,), dtype=np.float32)
    return TD3(state_dim, action_space, args)


def random_batch(batch_size=32, state_dim=STATE_DIM, action_dim=ACTION_DIM, not_done=1.0):
    # in the order of ReplayBuffer.sample(): state, action, next_state, reward, not_done
    return (torch.rand(batch_size, state_dim) * 2 - 1,
            torch.rand(batch_size, action_dim) * 2 - 1,
            torch.rand(batch_size, state_dim) * 2 - 1,
            torch.randn(batch_size, 1),
            torch.full((batch_size, 1), not_done))


def parameters(network):
    # a frozen copy of all weights and biases of a network
    return [p.detach().clone() for p in network.parameters()]


def changed(before, network):
    return any(not torch.equal(b, p) for b, p in zip(before, network.parameters()))


# ---------- select_action ----------

def test_select_action_shape_and_bounds():
    # large noise (sigma 0.8) pushes many values past +-1: they must be clipped to the action space
    agent = make_agent(noise_sigma=0.8)
    for _ in range(200):
        action = agent.select_action(np.random.uniform(-1, 1, STATE_DIM))
        assert isinstance(action, np.ndarray)
        assert action.shape == (ACTION_DIM,)
        assert np.all(action >= -1.0) and np.all(action <= 1.0)


def test_select_action_noise_has_the_requested_spread():
    # exploration noise N(0, (max_action * sigma)^2): over many calls on the same state the spread around mu is sigma.
    # The untrained actor's mu is close to 0, far from the clip at +-1, so clipping doesn't shrink the spread.
    sigma = 0.1
    agent = make_agent(noise_sigma=sigma)
    state = np.zeros(STATE_DIM, dtype=np.float32)
    actions = np.array([agent.select_action(state) for _ in range(2000)])
    assert np.std(actions - actions.mean(axis=0)) == pytest.approx(sigma, rel=0.05)


# ---------- update_parameters: which networks change, and when ----------

def test_critic_every_update_actor_and_targets_every_second_update():
    # delayed policy updates (policy_freq = 2): update 1 only changes the critics; update 2 also changes the actor
    # and soft-updates the targets. The targets never change on update 1, so no gradient reaches them.
    agent = make_agent()
    batch = random_batch()
    critic, actor = parameters(agent.critic), parameters(agent.actor)
    critic_target, actor_target = parameters(agent.critic_target), parameters(agent.actor_target)

    agent.update_parameters(batch, update=1)
    assert agent.total_it == 1
    assert changed(critic, agent.critic)
    assert not changed(actor, agent.actor)
    assert not changed(critic_target, agent.critic_target)
    assert not changed(actor_target, agent.actor_target)

    critic = parameters(agent.critic)
    agent.update_parameters(batch, update=2)
    assert agent.total_it == 2
    assert changed(critic, agent.critic)
    assert changed(actor, agent.actor)
    assert changed(critic_target, agent.critic_target)
    assert changed(actor_target, agent.actor_target)


def test_soft_update_moves_the_targets_by_tau():
    # theta' <- tau * theta + (1 - tau) * theta', with theta the weights right after this update's optimizer steps
    agent = make_agent()
    batch = random_batch()
    agent.update_parameters(batch, update=1)  # update 1: no soft update yet
    critic_target_old, actor_target_old = parameters(agent.critic_target), parameters(agent.actor_target)
    agent.update_parameters(batch, update=2)
    tau = agent.tau
    for old, new, online in zip(critic_target_old, agent.critic_target.parameters(), agent.critic.parameters()):
        assert torch.allclose(new, tau * online + (1 - tau) * old, atol=1e-7)
    for old, new, online in zip(actor_target_old, agent.actor_target.parameters(), agent.actor.parameters()):
        assert torch.allclose(new, tau * online + (1 - tau) * old, atol=1e-7)


# ---------- update_parameters: the critic target y ----------

class FixedTwinCritic(torch.nn.Module):
    # a stand-in target critic: Q1' = 1 and Q2' = 3 for every (s', a'), so min(Q1', Q2') = 1.
    # It also remembers the actions it was asked about (the smoothed target actions).
    def __init__(self):
        super().__init__()
        self.seen_actions = []

    def forward(self, state, action):
        self.seen_actions.append(action.clone())
        ones = torch.ones(state.shape[0], 1)
        return ones, 3 * ones


def critic_targets(monkeypatch, agent, batch):
    # record the target y that update_parameters passes to the critic loss F.mse_loss(current_q, y)
    seen = []
    real_mse = agent_module.F.mse_loss

    def recording_mse(current, target):
        seen.append(target.clone())
        return real_mse(current, target)

    monkeypatch.setattr(agent_module.F, 'mse_loss', recording_mse)
    agent.critic_target = FixedTwinCritic()
    agent.update_parameters(batch, update=1)  # update 1: no actor step, no soft update of the stand-in
    assert len(seen) == 2 and torch.equal(seen[0], seen[1])  # both critics regress onto the same y
    return seen[0]


def test_target_uses_the_smaller_twin_critic(monkeypatch):
    # clipped double Q-learning: y = r + gamma * not_done * min(Q1', Q2') = r + 0.99 * 1 * min(1, 3) = r + 0.99
    agent = make_agent()
    batch = random_batch(not_done=1.0)
    reward = batch[3]
    assert torch.allclose(critic_targets(monkeypatch, agent, batch), reward + 0.99 * 1.0, atol=1e-6)


def test_target_at_the_end_of_an_episode_is_the_reward(monkeypatch):
    # not_done = 0 (done after the 10th step): no future value, y = r
    agent = make_agent()
    batch = random_batch(not_done=0.0)
    assert torch.allclose(critic_targets(monkeypatch, agent, batch), batch[3], atol=1e-7)


def test_target_action_smoothing_noise_is_clipped(monkeypatch):
    # target policy smoothing: next_action = clip(pi'(s') + clip(eps, -0.5, 0.5), -1, 1) with eps ~ N(0, 0.2).
    # A huge eps (randn * 0.2 = 50) must be clipped to +0.5, and the action then to the action space.
    agent = make_agent()
    agent.critic_target = FixedTwinCritic()
    monkeypatch.setattr(agent_module.torch, 'randn_like', lambda x: torch.full_like(x, 250.0))
    batch = random_batch()
    with torch.no_grad():
        expected = (agent.actor_target(batch[2]) + 0.5).clamp(-1.0, 1.0)
    agent.update_parameters(batch, update=1)
    assert torch.allclose(agent.critic_target.seen_actions[0], expected, atol=1e-7)


# ---------- the agent learns ----------

def test_agent_learns_a_simple_bandit():
    # a toy problem with a known answer: the reward is -|a - a_best|^2, whatever the state, and every transition ends
    # the episode (not_done = 0), so the best possible Q is just the reward. After training on random transitions
    # from the course's ReplayBuffer, the critic loss must have dropped and the actor must point at a_best.
    action_dim = 2
    a_best = np.array([0.5, -0.3])
    agent = make_agent(noise_sigma=0.0, action_dim=action_dim, pi_lr=1e-3, q_lr=1e-3)
    memory = ReplayBuffer(STATE_DIM, action_dim, max_size=2000)
    for _ in range(2000):
        state = np.random.uniform(-1, 1, STATE_DIM)
        action = np.random.uniform(-1, 1, action_dim)
        memory.push(state, action, -np.sum((action - a_best) ** 2), np.random.uniform(-1, 1, STATE_DIM), True)

    def critic_loss():
        state, action, _, reward, _ = memory.sample(500)
        with torch.no_grad():
            q1, q2 = agent.critic(state, action)
        return float(((q1 - reward) ** 2).mean() + ((q2 - reward) ** 2).mean())

    loss_before = critic_loss()
    for update in range(1500):
        agent.update_parameters(memory.sample(64), update)
    assert critic_loss() < 0.1 * loss_before

    actions = np.array([agent.select_action(np.random.uniform(-1, 1, STATE_DIM)) for _ in range(20)])
    assert np.all(np.abs(actions - a_best) < 0.1)
