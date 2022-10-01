import logging
import math

from music21 import *
from music21 import converter
from music21.chord import Chord
from music21.duration import Duration
from music21.note import Note
from music21.stream import Part
from music21.stream import Score
from music21.tree.timespanTree import TimespanTree

from dataset import Dataset

ABS_TOL = 1 / 100

show_debug_scores = False


def extract_mono(score) -> Part:
    return __extract_mono_v2__(score)


def max_note(notes_and_chords: list) -> Note:
    m: Note = None
    for i in notes_and_chords:
        if isinstance(i, Note):
            if m:
                m = max(m, i)
            else:
                m = i
        elif isinstance(i, Chord):
            if m:
                m = max(m, max(i.notes))
            else:
                m = max(i.notes)
        else:
            raise AssertionError(i)
    return m


# This is a skyline-like algorithm
def __extract_mono_v2__(score):  # TODO: for downloads/Bach/wtc1p02.krn produces 167 patterns (compare to v1)
    notes = stream.Part()

    timespan_tree: TimespanTree = score.asTimespans(classList=('Note', 'Chord'))
    all_time_points = timespan_tree.allTimePoints()

    prev_tick = 0
    prev_note = None
    tp_iter = zip(all_time_points, all_time_points[1:])
    for offset, next_offset in tp_iter:
        starting_objs = [ts.element for ts in timespan_tree.elementsStartingAt(offset) if ts.quarterLength > 0]
        ending_objs = [ts.element for ts in timespan_tree.elementsStoppingAt(offset) if ts.quarterLength > 0]

        while next_offset and math.isclose(offset, next_offset, abs_tol=ABS_TOL):
            starting_objs += [ts.element for ts in timespan_tree.elementsStartingAt(next_offset)]
            ending_objs += [ts.element for ts in timespan_tree.elementsStoppingAt(next_offset)]
            offset, next_offset = next(tp_iter)

        starting_top_note: Note = max_note(starting_objs)
        ending_top_note: Note = max_note(ending_objs)

        if prev_note is None:
            if offset > prev_tick + ABS_TOL:
                notes.append(note.Rest(duration=Duration(quarterLength=(offset - prev_tick))))
        elif ending_top_note == prev_note:
            notes.append(prev_note)
        elif starting_top_note is None or prev_note > starting_top_note:
            continue
        elif offset > prev_tick + ABS_TOL:
            notes.append(note.Rest(duration=Duration(quarterLength=(offset - prev_tick))))

        prev_note = starting_top_note
        prev_tick = offset

    if prev_note:
        notes.append(prev_note)

    debug_show_notes(notes)

    return notes


def __extract_mono_v1__(score):  # TODO: for downloads/Bach/wtc1p02.krn produces 123 patterns (compare to v2)
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
                logging.getLogger(__name__).warning('Unknown type: {}'.format(note))
                raise AssertionError()

    debug_show_notes(notes)
    return notes


def debug_show_notes(notes):
    if not show_debug_scores:
        return
    # score = Score(notes) # todo: see how beautiful it looks for downloads/Bach/wtc1p02.krn
    score = Score()
    score.append(notes)
    score.show()


if __name__ == '__main__':
    dataset = Dataset('res/scores/mozart-sig/mozartsig.txt')
    score_file = dataset.files()[1]
    scores = converter.parse(score_file)
    mono: Part = extract_mono(scores)

    for n in mono.flatten().notes:
        n.style.color = '#00FFFF'
        # for x in n.derivation.chain():
        #     x.style.color = '#00FFFF'

    dbg = Score()
    # dbg.append(mono)
    for part in scores.parts:
        dbg.append(part)
    dbg.show()
