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
        print(works_and_signature_entries)

        score_index_const = 100000
        for i in range(0, len(signatures)):
            mapped_scope_signatures = signatures[i]
            for j in range(0, len(mapped_scope_signatures)):
                for notes in mapped_scope_signatures[j]:
                    key = i * score_index_const + j
                    self.add_hash(notes, key)
        candidates = self.check_candidates()
        print(candidates)
        multi_score_signatures = []
        for entry in candidates:
            for el in entry:
                index = int(el / score_index_const)
                signature_index = int(el - index * score_index_const)
                for notes in signatures[index][signature_index]:
                    if notes not in multi_score_signatures:
                        multi_score_signatures.append(notes)
        return multi_score_signatures

    def make_subvecs(self, signature):
        l = len(signature)
        assert l % self.b == 0
        r = int(l / self.b)
        # break signature into subvectors
        subvecs = []
        for i in range(0, l, r):
            subvecs.append(signature[i:i + r])
        return np.stack(subvecs)

    def add_hash(self, signature, index):
        subvecs = self.make_subvecs(signature).astype(str)
        for i, subvec in enumerate(subvecs):
            subvec = ','.join(subvec)
            if subvec not in self.buckets[i].keys():
                self.buckets[i][subvec] = []
            self.buckets[i][subvec].append(index)

    def check_candidates(self):
        candidates = []
        for bucket_band in self.buckets:
            keys = bucket_band.keys()
            for bucket in keys:
                hits = bucket_band[bucket]
                if len(hits) > 1:
                    candidates.extend(itertools.combinations(hits, len(hits)))
        return set(candidates)
