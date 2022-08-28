import os
import os.path
from pathlib import Path
import urllib.request
from urllib.parse import urlparse
from urllib.parse import parse_qs


class Dataset:

    def __init__(self, path, composer=None, cache="downloads/"):
        self.__score_files = []
        self.__path = path
        if composer:
            self.__composer = composer
        else:
            self.__composer = Path(path).stem
        self.__cache = os.path.join(cache, self.__composer)

        downloaded = set()
        os.makedirs(self.__cache, exist_ok=True)

        with open(path) as f:
            lines = f.readlines()
            for line in lines:
                if self.__should_skip(line):
                    continue
                try:
                    local_or_url = line.rstrip()
                    parsed = urlparse(local_or_url)
                    if not parsed.scheme:  # local file
                        self.__score_files.append(local_or_url)
                    else:
                        fname = self.__get_file_name(parsed)
                        if fname in downloaded:
                            # Sanity: already downloaded in this session
                            raise FileExistsError(f"File already exists: {fname}, url: {line}")

                        if os.path.isfile(fname):
                            print(f"Using existing file {fname}")
                        else:
                            print(f"Downloading {local_or_url} > {fname}")
                            urllib.request.urlretrieve(local_or_url, fname)
                            downloaded.add(fname)

                        self.__score_files.append(fname)
                except Exception as ex:
                    print(f'Failed parsing line {line} due to exception: {ex}')

    def __should_skip(self, line):
        return line is None or line.startswith('#') or len(line.rstrip()) <= 0

    def __get_file_name(self, parsed):
        parsed_qs = parse_qs(parsed.query)

        if "file" in parsed_qs:
            file_name = parsed_qs["file"][0]
        else:
            raise NameError("Could not guess file name from: " + parsed)

        return os.path.join(self.__cache, file_name)

    def composer(self):
        return self.__composer

    def files(self):
        return self.__score_files


if __name__ == '__main__':
    Dataset('res/scores/n-grams/bach-control-set', 'Bach')
