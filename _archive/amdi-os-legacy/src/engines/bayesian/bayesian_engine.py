'''
AEGIS-MIOS — Bayesian Engine
==============================
Computes Bayesian belief updates and runs inference networks.
'''
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger('amdi.engines.bayesian')


@dataclass
class BayesianBelief:
    '''Posterior belief about document importance or grounding.'''
    claim: str
    prior: float
    likelihood: float
    posterior: float
    evidence: list[str] = field(default_factory=list)


class BayesianEngine:
    '''
    Bayesian Engine.
    Computes claim updates P(A|B) = P(B|A) * P(A) / P(B) and runs simple conditional probability networks.
    '''

    def __init__(self, default_prior: float = 0.5):
        self.default_prior = default_prior
        self.beliefs: dict[str, BayesianBelief] = {}

    def update_belief(self, claim: str, likelihood: float, evidence_str: str = '') -> BayesianBelief:
        '''
        Updates the belief in a claim given a new evidence likelihood.
        P(A|B) = P(B|A)*P(A) / (P(B|A)*P(A) + P(B|~A)*P(~A))
        We assume a symmetric false positive rate of (1 - likelihood) for P(B|~A).
        '''
        prior = self.beliefs.get(claim, BayesianBelief(claim, self.default_prior, 1.0, self.default_prior)).posterior
        
        # P(B|A)
        p_b_given_a = likelihood
        # P(B|~A) - false positive probability
        p_b_given_not_a = 1.0 - likelihood
        
        p_b = p_b_given_a * prior + p_b_given_not_a * (1.0 - prior)
        if p_b == 0.0:
            posterior = 0.0
        else:
            posterior = (p_b_given_a * prior) / p_b

        belief = self.beliefs.get(claim)
        if not belief:
            belief = BayesianBelief(claim, prior, likelihood, posterior)
            self.beliefs[claim] = belief
        else:
            belief.prior = prior
            belief.likelihood = likelihood
            belief.posterior = posterior
            
        if evidence_str:
            belief.evidence.append(evidence_str)
            
        return belief

    def sequential_update(self, claim: str, likelihoods: list[float]) -> float:
        '''Updates a belief sequentially over a sequence of likelihood events.'''
        for idx, lh in enumerate(likelihoods):
            self.update_belief(claim, lh, f'seq_event_{idx}')
        return self.beliefs[claim].posterior

    def query_importance(self, size_score: float, keyword_score: float, layout_score: float) -> float:
        '''
        Computes conditional probability of relevance using a simple Bayesian network.
        Nodes: Important (Root), Size, Keywords, Layout (Leaves)
        '''
        p_imp = 0.3  # Prior probability of element importance
        
        # Likelihoods P(Signal | Important) vs P(Signal | ~Important)
        p_size_given_imp = size_score
        p_size_given_not_imp = 0.2
        
        p_key_given_imp = keyword_score
        p_key_given_not_imp = 0.1
        
        p_lay_given_imp = layout_score
        p_lay_given_not_imp = 0.3
        
        # Joint probability P(Signals | Important)
        p_signals_given_imp = p_size_given_imp * p_key_given_imp * p_lay_given_imp
        # Joint probability P(Signals | ~Important)
        p_signals_given_not_imp = p_size_given_not_imp * p_key_given_not_imp * p_lay_given_not_imp
        
        numerator = p_signals_given_imp * p_imp
        denominator = numerator + p_signals_given_not_imp * (1.0 - p_imp)
        
        if denominator == 0.0:
            return 0.0
        return numerator / denominator
