

class Signature:
    def __init__(self, notes, index):
        self.notes = notes
        self.index = index

    def __eq__(self, o: object):
        if isinstance(o, Signature):
            return self.notes == o.notes and self.index == o.index
        else:
            return super().__eq__(o)

    def __str__(self):
        return self.get_note_str()

    def __repr__(self):
        return self.get_note_str()

    def len(self):
        return len(self.notes)

    def get_note_str(self):
        return ', '.join(str(n) for n in self.notes) + ' with index [' + ', '.join(str(n) for n in self.index) + ']'


class SignatureEntry:

    def __init__(self, signatures):
        self.signatures = signatures

    def __str__(self):
        return self.get_note_str()

    def __repr__(self):
        return self.get_note_str()

    def __eq__(self, o: object):
        if isinstance(o, SignatureEntry):
            return self.signatures[0] == o.signatures[0]
        else:
            return super().__eq__(o)

    def get_note_str(self):
        return 'Found signature with: ' + ', '.join(str(n) for n in self.signatures)
