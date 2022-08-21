import random
from datetime import datetime

from music21 import *
from music21.chord import Chord
from music21.interval import Interval
from music21.note import Note
from music21.stream import Stream, Part, Measure

from signature import Signature
from benchmark.signature_benchmark import SignatureBenchmark
from notes_utils import *
from profile_utils import profile
from collections import defaultdict
from collections import OrderedDict
import logging

# score1 = converter.parse('http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=kern')
# score1 = converter.parse('https://kern.humdrum.org/cgi-bin/ksdata?location=users/craig/classical/mozart/piano/sonata&file=sonata15-1.krn&format=kern')
score1 = converter.parse('tinyNotation: 4/4 C4 D E8 F C4 D E8 F C4 D E8 F C4 D E8 F')


# score1 = converter.parse('https://kern.humdrum.org/cgi-bin/ksdata?l=users/craig/classical/mozart/piano/sonata&file=sonata10-1.krn&f=kern&o=norep')
# score1 = converter.parse('https://kern.humdrum.org/cgi-bin/ksdata?location=users/craig/classical/chopin/prelude&file=prelude28-06.krn&format=kern')
# score1.show()

# todo фильтровать одинаковые сигнатуры - придумать как группировать одинаковые, привести сигнатуру к одному виду
# сделать через threshold, выбор эталона который будет наиболее похожим на все остальные, возможно > 1
# todo обработать разные части


class SignaturesFinder:
    logger = logging.getLogger(__name__)

    def __init__(self,
                 score=score1,
                 min_note_count=4,
                 max_note_count=10,
                 min_signature_entries=2,
                 max_signature_entries=10,
                 benchmark=SignatureBenchmark()):
        self.score = score
        # минимальное количество нот, при котором последовательность считается сигнатурой
        self.min_interval_count = min_note_count - 1
        # максимальное количество нот, при котором последовательность считается сигнатурой
        self.max_interval_count = max_note_count - 1
        # минимальное количество раз, которое сигнатура может встречаться в произведении
        self.min_signature_entries = min_signature_entries
        # максимальное количество раз, которое сигнатура может встречаться в произведении
        self.max_signature_entries = max_signature_entries

        self.benchmark = benchmark
        self.notes = self.__get_notes__(self.score)

    def __find_signatures__(self):
        # self.transposed_notes.show()
        intervals = self.__map_notes__(self.notes)
        assert len(intervals) + 1 == len(self.notes)
        assert Interval(self.notes[0], self.notes[1]).semitones == intervals[0][0]

        all_subseq_map = defaultdict(list)
        for siglen in range(self.min_interval_count, self.max_interval_count + 1):
            for i in range(0, len(intervals) - siglen + 1):
                key = tuple(intervals[i: i + siglen])
                all_subseq_map[key].append(i)

        # arithmetic progression: num_of_windows(max_interval_count)+..+num_of_windows(max_interval_count)
        all_possible_windows = (self.max_interval_count - self.min_interval_count + 1) * (
                2 * len(intervals) - self.max_interval_count - self.min_interval_count + 2) / 2
        assert sum(map(len, all_subseq_map.values())) == all_possible_windows

        self.log_stats(all_subseq_map, intervals)

        # create domains by similarity
        checked_seq = set()
        groups = {}

        for seq1 in all_subseq_map:
            if seq1 in checked_seq:
                continue

            group = set()
            group.add(seq1)

            similarity_queue = list()
            similarity_queue.append(seq1)

            while len(similarity_queue) > 0:
                sample = similarity_queue.pop()
                for seq2 in all_subseq_map:
                    if seq2 in checked_seq:
                        continue

                    if len(sample) != len(seq2):  # todo: interpolated notes and other variations
                        continue

                    if sample == seq2:
                        continue

                    if self.benchmark.is_similar(sample, seq2):
                        self.__log__(f"merged {sample} and {seq2} \t\t //  canonical form: {seq1}")
                        similarity_queue.append(seq2)
                        checked_seq.add(seq2)
                        group.add(seq2)

            groups[seq1] = group
            self.__log__(f"Merged {len(group)} patterns. Sample: {seq1}")

        self.__log__(f"Found {len(groups)} domains")

        result = []
        for key, values in groups.items():
            indexes = []
            for value in values:
                indexes += all_subseq_map[value]

            if self.min_signature_entries <= len(indexes) <= self.max_signature_entries:
                signature = Signature(key, sorted(indexes))
                result.append(signature)
                self.__log__(str(signature))

        self.__log__(f"Found {len(result)} signatures")

        return result

    def log_stats(self, all_subseq_map, intervals):
        self.__log__(f"Total input length: {len(intervals)}")
        self.__log__(f"Input: {intervals}")
        self.__log__(f"Total unique subsequences "
              f"(length [{self.min_interval_count}..{self.max_interval_count}]): {len(all_subseq_map)}, "
              f"max possible: {sum(map(len, all_subseq_map.values()))}")
        sizes = OrderedDict()
        for i in range(self.min_interval_count, self.max_interval_count + 1):
            sizes[i] = 0
        for key in all_subseq_map:
            sizes[len(key)] += 1
        self.__log__(f"Stats:")
        self.__log__(f"  min = {min(sizes.values())}")
        self.__log__(f"  max = {max(sizes.values())}")
        self.__log__(f"  avg = {sum(sizes.values()) / len(sizes)}")
        for size, count in sizes.items():
            self.__log__(f"    len({size}) = {count} (max: {len(intervals) - size + 1})")

    def __get_notes__(self, score):
        notes = []
        parts = self.__pick_notes_from_score__(score)
        for note in parts[0]:
            if isinstance(note, Note):
                notes.append(note)
            elif isinstance(note, Chord):
                notes.append(Note(note.root()))
            else:
                self.__log__('Unknown type: {}'.format(note))
        return notes

    @staticmethod
    def __pick_notes_from_score__(score):
        if isinstance(score, Part):
            parts = [score.flat.notes.stream()]
        elif isinstance(score, Measure):
            parts = [score.flat.notes.stream()]
        else:
            parts = [p.flat.notes.stream() for p in score.parts]
        return parts

    @staticmethod
    def __map_notes__(notes):
        digits = []
        for i in range(0, len(notes) - 1):
            note1: Note = notes[i]
            note2: Note = notes[i + 1]
            interval = Interval(note1, note2).semitones
            durations = note2.duration.ordinal - note1.duration.ordinal
            digits.append((interval, durations))
        return digits

    def highlight_signatures(self, signatures):
        notes = self.notes
        for signature in signatures:
            color = '#' + ''.join(random.sample('0123456789ABCDEF', 6))
            for offset in signature.index:
                overlaps = False
                note_indexes = range(offset, offset + signature.len() + 1)
                for i in note_indexes:
                    if notes[i].style.color:
                        self.__log__(f"Overlapping signatures at index {i}")
                        overlaps = True
                        break

                if not overlaps:
                    for i in note_indexes:
                        notes[i].style.color = color

        part = Part(self.notes)
        part.show()

    # @profile
    def run(self):
        self.__log__('Started signature search for ' + str(self.score))
        start_time = datetime.now()
        signatures = self.__find_signatures__()
        end_time = datetime.now()

        self.__log__('Time: ' + str(end_time - start_time))
        self.__log__('Found signatures: ' + str(len(signatures)))

        return signatures

    def __log__(self, str):
        print(str)
        # TODO: self.logger.info(str)


if __name__ == '__main__':
    notes = converter.parse(r'downloads/Bach/bwv0312.krn')
    # notes.show()

    # logging.basicConfig(filename='logs-' + datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    # logging.getLogger('signature_benchmark').setLevel(logging.DEBUG)

    finder = SignaturesFinder(notes)
    signatures = finder.run()
    finder.highlight_signatures(signatures)
