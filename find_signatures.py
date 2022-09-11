import random
from datetime import datetime

from music21 import *
from music21.chord import Chord
from music21.interval import Interval
from music21.note import Note
from music21.stream import Stream, Part, Measure, Score

from signature import Signature, AnalyzableInterval
from signature import SignatureEntry
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

show_debug_scores = False


class SignaturesFinder:
    logger = logging.getLogger(__name__)

    def __init__(self,
                 score=score1,
                 min_note_count=4,
                 max_note_count=10,
                 min_signature_entries=2,
                 max_signature_entries=None,
                 benchmark=SignatureBenchmark()):
        if not max_signature_entries:
            # once every ten measures 4/4
            max_signature_entries = min(10, max(min_signature_entries, score.quarterLength / 40))

        self.score = score
        self.benchmark = benchmark
        self.notes = self.__get_notes__(self.score)

        # минимальное количество нот, при котором последовательность считается сигнатурой
        self.min_interval_count = min(len(self.notes), min_note_count) - 1
        # максимальное количество нот, при котором последовательность считается сигнатурой
        self.max_interval_count = min(len(self.notes), max_note_count) - 1
        # минимальное количество раз, которое сигнатура может встречаться в произведении
        self.min_signature_entries = min_signature_entries
        # максимальное количество раз, которое сигнатура может встречаться в произведении
        self.max_signature_entries = max_signature_entries

    def __find_signatures__(self):
        # Part(self.notes).show()
        intervals = self.__map_notes__(self.notes)
        assert len(self.notes) > 0, "Empty scores"
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
        remaining_subseq = set(all_subseq_map.keys())
        groups = {}

        while remaining_subseq:
            seq1 = remaining_subseq.pop()

            group = set()
            group.add(seq1)

            similarity_queue = list()
            similarity_queue.append(seq1)

            while len(similarity_queue) > 0:
                sample = similarity_queue.pop()
                checked = set()
                for seq2 in remaining_subseq:
                    if len(sample) != len(seq2):  # todo: interpolated notes and other variations
                        continue

                    if self.benchmark.is_similar(sample, seq2):
                        self.__log__(f"merged {sample} and {seq2} \t\t //  canonical form: {seq1}")
                        similarity_queue.append(seq2)
                        checked.add(seq2)
                group.update(checked)
                remaining_subseq.difference_update(checked)
            groups[seq1] = group
            if len(group) > 1:
                self.__log__(f"Merged {len(group)} patterns. Sample: {seq1}")

        self.__log__(f"Found {len(groups)} domains")

        result = []
        for key, values in groups.items():
            indexes = []
            for value in values:
                for start_idx in all_subseq_map[value]:
                    indexes.append((start_idx, start_idx + len(value)))

            if self.min_signature_entries <= len(indexes) <= self.max_signature_entries:
                signature = Signature(key, values)
                sig_entry = SignatureEntry(signature, sorted(indexes))
                result.append(sig_entry)
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
        return self.__get_notes_v2__(score)

    # This is a skyline-like algorithm
    def __get_notes_v2__(self, score):  # TODO: for downloads/Bach/wtc1p02.krn produces 167 patterns (compare to v1)
        notes = []
        chords = score.chordify()
        # chords.show()
        for chord in chords.recurse().getElementsByClass('Chord'):
            notes.append(sorted(chord.notes)[-1])
        self.debug_show_notes(notes)

        return notes

    def __get_notes_v1__(self, score):  # TODO: for downloads/Bach/wtc1p02.krn produces 123 patterns (compare to v2)
        parts = score.getElementsByClass('Part')
        if len(parts) > 1:
            print(len(parts))
            raise AssertionError()
        elif len(parts) == 1:
            part = parts[0]
        else:
            part = score

        measures = part.getElementsByClass('Measure')

        notes = []
        for measure in measures:
            voices = measure.voices
            if voices:
                top_voice = voices[0]  # todo: check that this is really a top voice
                notes_and_chords = top_voice.notes  # todo: rests
            else:
                notes_and_chords = measure.notes

            for note in notes_and_chords:
                if isinstance(note, Note):
                    notes.append(note)
                elif isinstance(note, Chord):
                    notes.append(Note(note.root()))
                    raise AssertionError()
                else:
                    self.__log__('Unknown type: {}'.format(note))
                    raise AssertionError()

        # self.debug_show_notes(notes)
        return notes

    @staticmethod
    def debug_show_notes(notes):
        if not show_debug_scores:
            return
        # score = Score(notes) # todo: see how beautiful it looks for downloads/Bach/wtc1p02.krn
        score = Score()
        score.append(notes)
        score.show()

    @staticmethod
    def __map_notes__(notes):
        digits = []
        for i in range(0, len(notes) - 1):
            note1: Note = notes[i]
            note2: Note = notes[i + 1]
            interval = Interval(note1, note2).semitones
            # durations = note2.duration.quarterLength - note1.duration.quarterLength
            durations = 0 # ignore rhythm at the moment
            digits.append(AnalyzableInterval(interval, durations))
        return digits

    def highlight_signatures(self, sig_entries):
        notes = self.notes
        for sig_entry in sig_entries:
            color = '#' + ''.join(random.sample('0123456789ABCDEF', 6))
            for start, end in sig_entry.entries:
                overlaps = False
                note_indexes = range(start, end + 1)
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
        # print(str)
        self.logger.info(str)


if __name__ == '__main__':
    logging.getLogger(__name__).setLevel(logging.INFO)
    logging.getLogger(__name__).addHandler(logging.StreamHandler())

    # notes = converter.parse(r'downloads/Bach/bwv0312.krn')
    # notes = converter.parse(r'res/dataset/bach/The-Well-Tempered-Clavier-Book-1-Prelude-and-Fugue-No.-14-in-F-sharp-Minor-BWV-859_Fugue-BWV-859_Bach-Johann-Sebastian_file1.mid')
    show_debug_scores = False
    notes = converter.parse(r'downloads/Bach/wtc1p02.krn')
    # notes = converter.parse(r'downloads/Bach/wtc1p04.krn')  # no particular voice/part containing a melody
    # notes.show()

    finder = SignaturesFinder(notes)
    sig_entries = finder.run()
    # finder.highlight_signatures(sig_entries)
