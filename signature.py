from collections import defaultdict
from collections import namedtuple

from benchmark.signature_benchmark import SignatureBenchmark


AnalyzableInterval = namedtuple("AnalyzableInterval", ("i", "d"))
AnalyzableInterval.__str__ = lambda self: f"({self.i}, {self.d})"
AnalyzableInterval.__repr__ = AnalyzableInterval.__str__


class Signature:
    def __init__(self, canonical, variants):
        self.canonical = canonical
        self.variants = set(variants)
        self.variants.add(canonical)

    def similar_to(self, other_signature, comparator=SignatureBenchmark()):
        for variant in self.variants:
            for other_variant in other_signature.variants:
                if comparator.is_similar(variant, other_variant):
                    return True
        return False

    def to_dict(self):
        return {'canonical': self.canonical, 'variants': sorted(list(self.variants))}

    @staticmethod
    def from_dict(dct):
        sig = Signature(dct['canonical'], dct['variants'])
        return sig

    def merge(self, other_signature):
        self.variants.update(other_signature.variants)

    def __eq__(self, o: object):
        raise AssertionError("Should not be used")

    def __hash__(self):
        raise AssertionError("Should not be used")

    def __str__(self):
        return self.get_canonical_str()

    def __repr__(self):
        return self.get_canonical_str()

    def get_canonical_str(self):
        return self.__get_note_str__(self.canonical) + f' ({len(self.variants)} variants)'

    def get_variants_str(self):
        return '\n'.join([self.__get_note_str__(i) for i in self.variants])

    @staticmethod
    def __get_note_str__(notes):
        return ', '.join(str(n[0]) for n in notes)


class SignatureEntry:

    def __init__(self, signature, entries):
        self.signature = signature
        self.entries = entries

    def __str__(self):
        return self.get_note_str()

    def __repr__(self):
        return self.get_note_str()

    def __eq__(self, o: object):
        raise AssertionError("Should not be used")

    def __hash__(self):
        raise AssertionError("Should not be used")

    def get_note_str(self):
        return f'{str(self.signature)}, {len(self.entries)} entries'

    def get_variants_str(self):
        return f'=== {len(self.signature.variants)} variants\n{self.signature.get_variants_str()}\n=== {len(self.entries)} entries'


class SignatureIndex:
    canonical_to_sig_map = {}
    canonical_to_work_map = {}

    def __init__(self):
        pass

    def add(self, work, sig):
        # fast lane
        if sig.canonical in self.canonical_to_sig_map:
            self.canonical_to_work_map[sig.canonical].add(work)
            self.canonical_to_sig_map[sig.canonical].merge(sig)
            return

        # slow path
        for canonical, known_sig in self.canonical_to_sig_map.items():
            if sig.similar_to(known_sig):
                self.canonical_to_work_map[canonical].add(work)
                known_sig.merge(sig)
                assert (len(self.canonical_to_sig_map) == len(self.canonical_to_work_map))
                return

        self.canonical_to_sig_map[sig.canonical] = sig
        self.canonical_to_work_map[sig.canonical] = {work}
        assert (len(self.canonical_to_sig_map) == len(self.canonical_to_work_map))

    def find_true_signatures(self, min_work_count=8):
        true_signatures = []
        for canonical, works in self.canonical_to_work_map.items():
            if len(works) >= min_work_count:
                true_signatures.append((self.canonical_to_sig_map[canonical], works))

        return true_signatures
