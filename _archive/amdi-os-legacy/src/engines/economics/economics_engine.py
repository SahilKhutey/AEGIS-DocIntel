'''
AEGIS-MIOS — Economics Engine
================================
Tracks and evaluates processing efficiency metrics (Token, Memory, Retrieval economics).
'''
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger('amdi.engines.economics')


@dataclass
class EconomicsRatios:
    '''Efficiency ratios representing document intelligence economics.'''
    token_economics: float       # TEC = Quality / Tokens
    memory_economics: float      # MEC = UsefulData / Memory
    information_economics: float # IEC = UsefulInfo / Storage
    retrieval_economics: float   # REC = CorrectRetrieval / Operations
    agent_economics: float       # AEC = Quality / AgentCost


class EconomicsEngine:
    '''
    Economics Engine.
    Tracks resource efficiency to maximize return on token budget and storage operations.
    '''

    @staticmethod
    def calculate_ratios(
        quality: float, tokens: int, useful_data_mb: float, memory_mb: float,
        useful_info_bytes: int, storage_bytes: int, correct_retrieved: int, total_ops: int,
        agent_cost_usd: float
    ) -> EconomicsRatios:
        '''Computes efficiency economic ratios.'''
        tec = quality / max(1, tokens)
        mec = useful_data_mb / max(1.0, memory_mb)
        iec = useful_info_bytes / max(1, storage_bytes)
        rec = correct_retrieved / max(1, total_ops)
        aec = quality / max(1e-6, agent_cost_usd)
        
        return EconomicsRatios(
            token_economics=tec,
            memory_economics=mec,
            information_economics=iec,
            retrieval_economics=rec,
            agent_economics=aec
        )
