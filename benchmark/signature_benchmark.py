import logging
from benchmark.benchmark_utils import *

logger = logging.getLogger('signature_benchmark')

class SignatureBenchmark:
    def __init__(self, benchmark_percent=80, threshold=30, use_rhythmic=False):
        self.benchmark_percent = benchmark_percent
        self.threshold = threshold
        self.use_rhythmic = use_rhythmic

    def is_similar(self, notes1, notes2):
        intervals1, directions1, durations1 = parse_ints_from_intervals(notes1)
        intervals2, directions2, durations2 = parse_ints_from_intervals(notes2)
        intervals_percent = test_correctness(intervals1, intervals2)
        direction_percent = test_correctness(directions1, directions2)

        if self.use_rhythmic:
            rhythmic_percent = test_correctness(durations1, durations2)
        else:
            rhythmic_percent = 0
        values = [intervals_percent, direction_percent, rhythmic_percent]
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(str(values) + '\n')
        return serial_matching(values, self.benchmark_percent) \
               or parallel_matching(values, self.benchmark_percent) \
               or summational_matching(values, self.benchmark_percent, self.threshold) \
               or differential_matching(values, self.benchmark_percent, self.threshold)


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
