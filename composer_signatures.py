import collections
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
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        scores = collections.defaultdict(list)

        for file in dataset.files():
            try:
                note_score = converter.parse(file)
                note_score.piece_name = file
                scores[dataset.composer()].append(note_score)
                print('Parsed ', file)
            except Exception as ex:
                print(f'Failed to parse {file} due to exception: {ex}')

        result = collections.defaultdict(list)
        for composer in scores:
            multi_score_signatures = MultiScoreSignatures().run(scores[composer])
            result[composer].append(multi_score_signatures)

        with open(out_path + ".json", "w") as outfile:
            json.dump(result, outfile, cls=NoteEncoder)
        with open(out_path + ".json") as json_file:
            data = json.load(json_file, object_hook=note_decoder)
            print(data)


if __name__ == '__main__':
    start_time = datetime.now()

    dataset = Dataset('res/scores/n-grams/bach-control-set', 'Bach')
    ComposerSignatures(dataset, "out/bach01")

    end_time = datetime.now()
    print('Time: ' + str(end_time - start_time))
