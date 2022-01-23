from datetime import datetime

from music21 import *
from music21.chord import Chord
from music21.note import Note
from music21.stream import Stream

from benchmark.signature_benchmark import SignatureBenchmark

score1 = converter.parse('http://kern.ccarh.org/cgi-bin/ksdata?l=users/craig/classical/bach/cello&file=bwv1007-01.krn&f=kern')
score2 = converter.parse('https://kern.humdrum.org/cgi-bin/ksdata?location=users/craig/classical/bach/371chorales&file=chor279.krn&f=kern')
# score1.show()
# score2.show()

# todo фильтровать одинаковые сигнатуры - придумать как группировать одинаковые
# todo обработать разные части
# todo перевести все в до https://stackoverflow.com/questions/37494229/music21-transpose-streams-to-a-given-key

# CONTROLLERS REGION start

# допустимый процент несовпадения
threshold = 20
# контрольный показатель совпадения, при котором тест считается пройденным
benchmark_percent = 60
# минимальное количество нот, при котором последовательность считается сигнатурой
min_note_count = 4
# максимальное количество нот, при котором последовательность считается сигнатурой
max_note_count = 10
# показывать ли дебажные логи
show_logs = True

min_duration = 0.1

# CONTROLLERS REGION end


class NoteInterval:

    def __init__(self, notes, interval_between):
        self.notes = notes
        self.interval = interval_between

    def __str__(self):
        return self.get_note_str() + " - " + self.interval.niceName

    def __repr__(self):
        return self.get_note_str() + " - " + self.interval.niceName

    def get_note_str(self):
        return ', '.join(str(n) for n in self.notes)


def find_signatures():
    intervals1 = get_notes(score1)
    intervals2 = get_notes(score2)
    result = []

    if len(intervals1) < len(intervals2):
        temp_interval = intervals1
        intervals1 = intervals2
        intervals2 = temp_interval

    for i in range(0, len(intervals1), min_note_count):
        for k in range(0, len(intervals2), min_note_count):
            j = i + max_note_count
            m = k + max_note_count
            signature = []
            notes1 = []
            notes2 = []
            while j > i + min_note_count and m > k + min_note_count:
                if 0 <= j < len(intervals1) and 0 <= m < len(intervals2):
                    benchmark = SignatureBenchmark(benchmark_percent, threshold, show_logs)
                    notes1 = intervals1[i: j]
                    notes2 = intervals2[k: m]
                    if benchmark.is_signature(notes1, notes2):
                        signature = notes2
                        break
                j -= 1
                m -= 1
            if len(signature) > 0:
                result.append(signature)
                print('Found signature with: ', notes1, ' and ', notes2)
    return result


def get_notes(score):
    notes = []
    parts = [p.flat.notesAndRests.stream() for p in score.parts]
    key = score.analyze('key')
    for note in parts[0]:
        if isinstance(note, Note):
            notes.append(note)
        elif isinstance(note, Chord):
            # trying to get leading tone from chord
            for chord_pitch in note.pitches:
                if key.chord.pitches.__contains__(chord_pitch):
                    if show_logs:
                        print('Got note from chord: ', chord_pitch)
                    notes.append(chord_pitch)
                    break
        else:
            print('Unknown type: {}'.format(note))
    return notes


def count_repeated(list):
    list_with_count, counted_elements = [], []
    for element in list:
        if not (element in counted_elements):
            counted_elements = counted_elements + [element]
            list_with_count = list_with_count + [[element, 1]]
        else:
            for index in range(len(list_with_count)):
                if list_with_count[index][0] == element:
                    list_with_count[index][1] = list_with_count[index][1] + 1
    return list_with_count


start_time = datetime.now()
signatures = find_signatures()
end_time = datetime.now()
print('Time: ', end_time - start_time)

result = count_repeated(signatures)
stream1 = Stream()
for element in result:
    stream1.append(element[0])
    stream1.append(note.Rest())
    stream1.append(note.Rest())
    stream1.show()
print(*result, sep='\n')
