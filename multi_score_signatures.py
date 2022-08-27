import itertools

import numpy as np

from find_signatures import SignaturesFinder
from signature import SignatureIndex


class MultiScoreSignatures:

    def __init__(self):
        self.b = 1
        self.buckets = []
        for i in range(self.b):
            self.buckets.append({})

    @staticmethod
    def __signatures_in_single_work(score):
        print(f'Trying to find signatures in: {score.piece_name}')
        sf = SignaturesFinder(score)
        signature_entries = sf.run()
        print(f"Found {len(signature_entries)} signatures")
        # signature_entries.piece_name = score.piece_name
        return score.piece_name, signature_entries

    def run(self, scores):
        # with ThreadPoolExecutor(8) as executor:
        #     signatures = executor.map(self.__signatures_in_single_work, scores)
        works_and_signature_entries = map(self.__signatures_in_single_work, scores)

        index = SignatureIndex()
        for work_name, sig_entries in works_and_signature_entries:
            print(work_name)
            print("\n".join([e.get_variants_str() for e in sig_entries]))
            print(f"Merging signatures from {work_name}")
            for sig_entry in sig_entries:
                index.add(work_name, sig_entry.signature)
        # sig_entries = [item for sublist in works_and_signature_entries for item in sublist]
        # sig_candidates = [i.signature for i in sig_entries]
        return index.find_true_signatures()
