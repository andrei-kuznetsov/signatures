from collections import defaultdict


class Signature:
    def __init__(self, canonical, variants):
        self.canonical = canonical
        self.variants = set(variants)
        self.variants.add(canonical)

    def __eq__(self, o: object):
        if isinstance(o, Signature):
            return self.canonical == o.canonical
        else:
            return super().__eq__(o)

    def __str__(self):
        return self.get_note_str()

    def __repr__(self):
        return self.get_note_str()

    def get_note_str(self):
        return ', '.join(str(n) for n in self.canonical) + f' ({len(self.variants)} variants)'


class SignatureEntry:

    def __init__(self, signature, entries):
        self.signature = signature
        self.entries = entries

    def __str__(self):
        return self.get_note_str()

    def __repr__(self):
        return self.get_note_str()

    def __eq__(self, o: object):
        if isinstance(o, SignatureEntry):
            return self.signature.canonical == o.signature.canonical
        else:
            return super().__eq__(o)

    def get_note_str(self):
        return f'{str(self.signature)}, {sum(len(self.entries))} entries'
