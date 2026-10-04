'''
AMDI-OS Benchmarks Statistics Module
'''
from .significance import paired_t_test, wilcoxon_signed_rank, cohens_d, confidence_interval, calibration_error

__all__ = [
    'paired_t_test',
    'wilcoxon_signed_rank',
    'cohens_d',
    'confidence_interval',
    'calibration_error',
]
