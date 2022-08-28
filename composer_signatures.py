import pickle
import json
from datetime import datetime
import multiprocessing
from find_signatures import SignaturesFinder
from signature import SignatureIndex
from music21 import converter

from json_utils import NoteEncoder, note_decoder
from dataset import Dataset
import os
import os.path

# default_cache_path=None
default_cache_path = "out/cache"


def signatures_in_single_work(file):
    try:
        return CachingSingleWorkSignaturesFinder(file).find()
    except Exception as ex:
        print(f'Failed to process {file} due to exception: {ex}')
        return file, "error"


class CachingSingleWorkSignaturesFinder:
    def __init__(self, file, cache=default_cache_path):
        if os.path.getsize(file) <= 0:
            raise Exception(f"Empty file: {file}")

        self.src_file = file
        self.cache = cache

    def cache_file(self):
        if self.cache:
            return os.path.join(self.cache, self.src_file + ".sig")
        else:
            return None

    def is_cache_valid(self):
        # TODO: consider signature extraction parameters
        cache_file = self.cache_file()
        if not cache_file or not os.path.exists(cache_file):
            return False

        cache_modified = os.path.getmtime(cache_file)
        src_modified = os.path.getmtime(self.src_file)
        return cache_modified > src_modified

    def get_cached_result(self):
        cache_file = self.cache_file()

        with open(cache_file, 'rb') as cache_file:
            return pickle.load(cache_file)

    def save_cache_result(self, result):
        cache_file = self.cache_file()
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'wb') as cache_file:
            return pickle.dump(result, cache_file)

    def find(self):
        if self.is_cache_valid():
            print(f"Using existing signatures cache for {self.src_file}")
            return self.get_cached_result()

        try:
            score = converter.parse(self.src_file)
            print('Parsed ', self.src_file)
        except Exception as ex:
            raise Exception(f'Failed to parse {self.src_file}') from ex

        print(f'Trying to find signatures in: {self.src_file}')
        sf = SignaturesFinder(score)
        signature_entries = sf.run()
        print(f"Found {len(signature_entries)} signature candidates")
        result = self.src_file, signature_entries
        self.save_cache_result(result)
        return result


class ComposerSignatures:

    def __init__(self, dataset, out_path):
        os.makedirs(out_path, exist_ok=True)

        with multiprocessing.Pool(8) as pool:
            works_and_signature_entries = pool.map(signatures_in_single_work, dataset.files())

        index = SignatureIndex()
        for work_name, sig_entries in works_and_signature_entries:
            if sig_entries == "error":
                print(f"error while processing {work_name}")
                continue

            print(work_name)
            # print("\n".join([e.get_variants_str() for e in sig_entries]))
            print(f"Merging signatures from {work_name}")
            for sig_entry in sig_entries:
                index.add(work_name, sig_entry.signature)

        multi_score_signatures = index.find_true_signatures()

        with open(f"{out_path}/{dataset.composer()}.json", "w") as outfile:
            sig_and_works = map(lambda e: {"signature": e[0].to_dict(), "works": sorted(list(e[1]))},
                                multi_score_signatures)
            json.dump(list(sig_and_works), outfile)


if __name__ == '__main__':
    start_time = datetime.now()

    # dataset_name = "nextech-22"
    dataset_name = "test"
    dataset_path = f"res/scores/{dataset_name}"
    for f in os.listdir(dataset_path):
        dataset = Dataset(os.path.join(dataset_path, f))
        ComposerSignatures(dataset, f"out/{dataset_name}")

    end_time = datetime.now()
    print('Time: ' + str(end_time - start_time))
