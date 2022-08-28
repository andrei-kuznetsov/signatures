import os
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


def signatures_in_single_work(file):
    try:
        return SingleWorkSignaturesFinder(file).find()
    except Exception as ex:
        print(f'Failed to process {file} due to exception: {ex}')
        return file, "error"


class SingleWorkSignaturesFinder:
    def __init__(self, file):
        if os.path.getsize(file) <= 0:
            raise Exception(f"Empty file: {file}")

        try:
            self.score = converter.parse(file)
            self.piece_name = file
            print('Parsed ', file)
        except Exception as ex:
            raise Exception(f'Failed to parse {file}') from ex

    def find(self):
        print(f'Trying to find signatures in: {self.piece_name}')
        sf = SignaturesFinder(self.score)
        signature_entries = sf.run()
        print(f"Found {len(signature_entries)} signature candidates")
        return self.piece_name, signature_entries


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

    dataset_name="nextech-22"
    # dataset_name = "test"
    dataset_path = f"res/scores/{dataset_name}"
    for f in os.listdir(dataset_path):
        dataset = Dataset(os.path.join(dataset_path, f))
        ComposerSignatures(dataset, f"out/{dataset_name}")

    end_time = datetime.now()
    print('Time: ' + str(end_time - start_time))
