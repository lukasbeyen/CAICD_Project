import copy
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class Actor(nn.Module):
	def __init__(self, state_dim, action_dim, max_action):
		super(Actor, self).__init__()

		self.l1 = nn.Linear(state_dim, 256)
		self.l2 = nn.Linear(256, 256)
		self.l3 = nn.Linear(256, action_dim)
		
		self.max_action = max_action
		

	def forward(self, state):
		a = F.relu(self.l1(state))
		a = F.relu(self.l2(a))
		return self.max_action * torch.tanh(self.l3(a))


class Critic(nn.Module):
	def __init__(self, state_dim, action_dim):
		super(Critic, self).__init__()

		# Q1 architecture
		self.l1 = nn.Linear(state_dim + action_dim, 256)
		self.l2 = nn.Linear(256, 256)
		self.l3 = nn.Linear(256, 1)

		# Q2 architecture
		self.l4 = nn.Linear(state_dim + action_dim, 256)
		self.l5 = nn.Linear(256, 256)
		self.l6 = nn.Linear(256, 1)


	def forward(self, state, action):
		sa = torch.cat([state, action], 1)

		q1 = F.relu(self.l1(sa))
		q1 = F.relu(self.l2(q1))
		q1 = self.l3(q1)

		q2 = F.relu(self.l4(sa))
		q2 = F.relu(self.l5(q2))
		q2 = self.l6(q2)
		return q1, q2


	def Q1(self, state, action):
		sa = torch.cat([state, action], 1)

		q1 = F.relu(self.l1(sa))
		q1 = F.relu(self.l2(q1))
		q1 = self.l3(q1)
		return q1


class TD3(object):
    def __init__(self, state_dim, action_space, args):
        self.max_action = float(action_space.high[0])
        self.discount = args.gamma
        self.tau = args.tau
        self.policy_noise = 0.2
        self.noise_clip = 0.5
        self.expl_noise = args.noise_sigma
        self.policy_freq = args.actor_update_interval

        self.action_dim = action_space.shape[0]
        self.actor = Actor(state_dim, self.action_dim, self.max_action).to(device)
        self.actor_target = copy.deepcopy(self.actor)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=args.pi_lr)

        self.critic = Critic(state_dim, self.action_dim).to(device)
        self.critic_target = copy.deepcopy(self.critic)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(), lr=args.q_lr)

        self.total_it = 0


    def select_action(self, state):
        """
        TODO: Implement the action selection mechanism for the TD3 agent
        
        Steps to implement:
        1. Convert the state to a tensor if it's a numpy array or CPU tensor
        2. Get the deterministic action from the actor network (mu)
        3. Add "exploration noise" using np.random.normal with:
           - mean = 0
           - std = self.max_action * self.expl_noise
           - size = self.action_dim
        4. Clip the final action to be between -self.max_action and self.max_action
        5. Return the action as a numpy array
        
        Args:
            state: The current state observation (numpy array or tensor)
            
        Returns:
            action: The selected action as a numpy array
        """
        # 1. the actor expects a float tensor with a batch dimension: shape (1, state_dim)
        if not torch.is_tensor(state):
            state = torch.as_tensor(np.asarray(state), dtype=torch.float32)
        state = state.float().reshape(1, -1).to(device)
        # 2. the deterministic action mu(s); no_grad: acting is not training, no gradients needed
        with torch.no_grad():
            mu = self.actor(state).cpu().numpy().flatten()
        # 3. Gaussian exploration noise, one value per action dimension (TD3 paper, Algorithm 1: a = pi(s) + eps)
        noise = np.random.normal(0, self.max_action * self.expl_noise, size=self.action_dim)
        # 4. keep the action inside the action space [-max_action, max_action]
        return np.clip(mu + noise, -self.max_action, self.max_action)


    def update_parameters(self, memory_batch, update):
        """
        TODO: Implement the TD3 learning algorithm
        
        Steps to implement:
        1. Increment total_it counter
        2. Unpack the memory_batch tuple into state, action, next_state, reward, not_done
        
        3. Compute target actions (with torch.no_grad()):
           - Add clipped "policy noise" to target policy
           - Get next actions from target actor network
           - Clip target actions to valid range
        
        4. Compute target Q-values (with torch.no_grad()):
           - Get Q-values from both target critics
           - Take the minimum of both Q-values
           - Compute TD target using reward + discount * min Q-value * not_done
        
        5. Compute current Q-values and critic loss:
           - Get current Q-values from both critics
           - Compute MSE loss between current and target Q-values for both critics
        
        6. Update critics:
           - Zero gradients
           - Backpropagate critic loss
           - Optimize critic
        
        7. Delayed policy update (if total_it % policy_freq == 0):
           - Compute actor loss using first critic's Q-values
           - Update actor
           - Update target networks using soft update (τ)
        
        Args:
            memory_batch: Tuple of (state, action, next_state, reward, not_done) tensors
            update: Update step (not used in this implementation)
        """
        # 1. count the updates (for the delayed policy update below)
        self.total_it += 1
        # 2. a mini-batch of transitions, in the order of ReplayBuffer.sample(); every tensor has batch_size rows
        state, action, next_state, reward, not_done = memory_batch

        with torch.no_grad():  # the target y is a fixed label: no gradients through the target networks
            # 3. target policy smoothing (paper §5.3): the target actor's action plus clipped Gaussian noise
            noise = (torch.randn_like(action) * self.policy_noise).clamp(-self.noise_clip, self.noise_clip)
            next_action = (self.actor_target(next_state) + noise).clamp(-self.max_action, self.max_action)
            # 4. clipped double Q-learning (paper §4.2): the smaller of the two target critics,
            #    y = r + gamma * min(Q1', Q2'); not_done = 0 at the end of an episode, so there y = r
            target_q1, target_q2 = self.critic_target(next_state, next_action)
            target_q = reward + not_done * self.discount * torch.min(target_q1, target_q2)

        # 5. both critics regress onto the same target y
        current_q1, current_q2 = self.critic(state, action)
        critic_loss = F.mse_loss(current_q1, target_q) + F.mse_loss(current_q2, target_q)

        # 6. one gradient step on the critics
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

        # 7. delayed policy update (paper §5.2): the actor and the target networks only every policy_freq updates
        if self.total_it % self.policy_freq == 0:
            # the actor maximises the first critic's value of its own action: minimise -Q1(s, pi(s)).
            # Only the actor's optimizer steps; the critic's gradients from this backward are cleared by the
            # critic_optimizer.zero_grad() of the next update.
            actor_loss = -self.critic.Q1(state, self.actor(state)).mean()
            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            self.actor_optimizer.step()

            # soft update of the target networks: theta' <- tau * theta + (1 - tau) * theta'
            for param, target_param in zip(self.critic.parameters(), self.critic_target.parameters()):
                target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
            for param, target_param in zip(self.actor.parameters(), self.actor_target.parameters()):
                target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)


    def save(self, filename):
        torch.save(self.critic.state_dict(), filename + "_critic")
        torch.save(self.critic_optimizer.state_dict(), filename + "_critic_optimizer")
        
        torch.save(self.actor.state_dict(), filename + "_actor")
        torch.save(self.actor_optimizer.state_dict(), filename + "_actor_optimizer")


    def load(self, filename):
        self.critic.load_state_dict(torch.load(filename + "_critic"))
        self.critic_optimizer.load_state_dict(torch.load(filename + "_critic_optimizer"))
        self.critic_target = copy.deepcopy(self.critic)

        self.actor.load_state_dict(torch.load(filename + "_actor"))
        self.actor_optimizer.load_state_dict(torch.load(filename + "_actor_optimizer"))
        self.actor_target = copy.deepcopy(self.actor)
        