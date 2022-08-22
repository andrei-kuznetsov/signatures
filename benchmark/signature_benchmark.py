import logging
from benchmark.benchmark_utils import *

logger = logging.getLogger('signature_benchmark')


class SignatureBenchmark:
    def __init__(self, benchmark_percent=80, threshold=30, use_rhythmic=False):
        self.benchmark_percent = benchmark_percent
        self.threshold = threshold
        self.use_rhythmic = use_rhythmic

    def is_similar(self, notes1, notes2):
        if len(notes1) != len(notes2):
            return False  # todo

        matching = sum(map(lambda n1, n2: 1 if n1.i == n2.i else 0, notes1, notes2))
        return matching >= self.benchmark_percent * len(notes1) / 100


def parse_ints_from_intervals(notes):
    intervals = []
    directions = []
    durations = []
    for note in notes:
        interval = note[0]
        duration = note[1]
        intervals.append(abs(interval))
        if interval > 0:
            direction = 1
        elif interval == 0:
            direction = 0
        else:
            direction = -1
        directions.append(direction)
        durations.append(duration)
    return intervals, directions, durations
