import random
import unittest
import random
from collections import namedtuple
from benchmark.signature_benchmark import SignatureBenchmark

SimpleInterval = namedtuple('Interval', ('idx', 'semi', 'dur'))


def pitch_seq(semitones):
    result = []
    for semitone in semitones:
        result.append(SimpleInterval(idx=0, semi=semitone, dur=0))
    return result


def random_pitches(size):
    return [random.randint(-5, 5) for i in range(0, size)]


def random_seq():
    return pitch_seq(random_pitches(random.randint(5, 15)))


class TestSimilarity(unittest.TestCase):

    def test_similar_to_self_100(self):
        intervals = random_seq()
        self.assertTrue(SignatureBenchmark(100, 100).is_similar(intervals, intervals))

    def test_not_similar_to_different_100(self):
        intervals1 = random_seq()
        intervals2 = None
        while intervals2 is None or intervals1 == intervals2:
            intervals2 = pitch_seq(random_pitches(len(intervals1)))
        self.assertFalse(SignatureBenchmark(100, 1).is_similar(intervals1, intervals2))

    def test_not_similar_to_different_len3(self):
        intervals1 = pitch_seq([1, -1, -2])
        intervals2 = pitch_seq([-1, -2, 2])
        self.assertFalse(SignatureBenchmark().is_similar(intervals1, intervals2))


if __name__ == '__main__':
    unittest.main()
