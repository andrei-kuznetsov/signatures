import os

from music21 import *

from dataset import Dataset


def convert(dataset):
    for file in dataset.files():
        print(f"parsing {file}")
        scores = converter.parse(file)
        fname = f"out/converted/{file}.musicxml"
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        print(f"writing {fname}")
        scores.write("musicxml", fname)


if __name__ == '__main__':
    dataset = Dataset('res/scores/mozart-sig/mozartsig.txt')
    convert(dataset)
