'''
AEGIS-MIOS — Reinforcement Learning Engine
============================================
Selects optimal retrieval actions using a Q-learning value function.
'''
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

logger = logging.getLogger('amdi.engines.rl')


class RLEngine:
    '''
    Reinforcement Learning Engine.
    Q-learning agent for choosing context packaging actions based on document state features.
    '''

    def __init__(self, alpha: float = 0.1, gamma: float = 0.9, epsilon: float = 0.15):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        # Q-table: key is state representation string, value is dict of action -> Q-value
        self.q_table: dict[str, dict[str, float]] = {}
        # Pre-defined actions (different weights profiles)
        self.actions = ['semantic_heavy', 'matrix_heavy', 'geometric_heavy', 'hybrid_balanced']

    def get_state(self, table_count: int, is_repetitive: bool, complexity: str) -> str:
        '''Discretizes system features into a state string key.'''
        tbl_bucket = 'no_tables' if table_count == 0 else ('few_tables' if table_count < 3 else 'many_tables')
        rep_bucket = 'periodic' if is_repetitive else 'non_periodic'
        return f'{tbl_bucket}:{rep_bucket}:{complexity}'

    def select_action(self, state: str) -> str:
        '''Selects action using an epsilon-greedy policy.'''
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}

        if random.random() < self.epsilon:
            return random.choice(self.actions)
            
        # Exploit: find action with max Q-value
        q_vals = self.q_table[state]
        max_val = max(q_vals.values())
        best_actions = [a for a, q in q_vals.items() if q == max_val]
        return random.choice(best_actions)

    def learn(self, state: str, action: str, reward: float, next_state: str) -> None:
        '''Updates the Q-value using Bellman equation.'''
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in self.actions}

        old_q = self.q_table[state][action]
        next_max_q = max(self.q_table[next_state].values())
        
        # Q(s, a) = Q(s, a) + alpha * (reward + gamma * max Q(s', a') - Q(s, a))
        new_q = old_q + self.alpha * (reward + self.gamma * next_max_q - old_q)
        self.q_table[state][action] = new_q
