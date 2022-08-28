import os
import json
from datetime import datetime

from music21 import converter

from json_utils import NoteEncoder, note_decoder
from multi_score_signatures import MultiScoreSignatures
from dataset import Dataset
import os
import os.path


class ComposerSignatures:

    def __init__(self, dataset, out_path):
        os.makedirs(out_path, exist_ok=True)
        scores = []

        for file in dataset.files():
            try:
                note_score = converter.parse(file)
                note_score.piece_name = file
                scores.append(note_score)
                print('Parsed ', file)
            except Exception as ex:
                print(f'Failed to parse {file} due to exception: {ex}')

        multi_score_signatures = MultiScoreSignatures().run(scores)
        print(multi_score_signatures)

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
