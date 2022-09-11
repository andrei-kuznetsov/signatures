from music21 import *

# Mozart signatures. David Cope, Experiments in Musical Intelligence, p. 92
moz_sig = [
    (
        converter.parse("tinyNotation: 4/4 c'16 d' e' f' f.4 a16 g f4"),
        key.KeySignature(-1),
        "a. Motive: K.330 second movement, mm. 19-20"
    ),
    (
        converter.parse("tinyNotation: 4/4 e'-16 d' c' b- c'.4 b-16 c'16 d'"),
        key.KeySignature(-2),
        "b. Inversion: K.333 third movement, mm. 154-5"
    ),
    (
        converter.parse("tinyNotation: 4/4 trip{c'8 c'# d'} f4 e.8 d32 e f4"),
        key.KeySignature(-1),
        "c. Augmentation: K.279 second movement, mm. 56-57 (57)"
    ),
    (
        converter.parse("tinyNotation: 4/4 a16 b- b c' f.8 g32 f e8"),
        key.KeySignature(-1),
        "d. Diminution: K.309 second movement, mm. 4-5"
    ),
    (
        converter.parse("tinyNotation: 4/4 a'16 g' f' e'- d'4 c'.8 b-32 c' b-4"),
        key.KeySignature(-2),
        "e. Interpolation: K.333 first movement, mm. 133-134"
    ),
    (
        converter.parse("tinyNotation: 4/4 f'32 e'- d' c' b-4 a8"),
        key.KeySignature(-3),
        "f. Fragmentation: K.281 second movement, mm. 25-26"
    ),
    (
        converter.parse("tinyNotation: 4/4 d'16 c' b c' b.8 c'32 b a8"),
        key.KeySignature(1),
        "g. Order: K.545 second movement, mm. 7-9"
    ),
]


def show_signatures(signatures):
    out = stream.Part()
    for i in range(0, len(signatures)):
        s = signatures[i][0]
        label = expressions.TextExpression(signatures[i][2])
        s.measure(1).insert(0, label)
        s.measure(1).insert(0, signatures[i][1])

        if i > 0:
            s.measure(1).insert(0, layout.SystemLayout(isNew=True))
            clef = s.recurse().getElementsByClass('Clef')[0]
            s.remove(clef, recurse=True)

        for el in s.recurse():
            out.append(el)
        out.append(stream.Measure())
        out.append(stream.Measure())
        out.append(stream.Measure())

    out.show()


if __name__ == '__main__':
    show_signatures(moz_sig)
