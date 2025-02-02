import os
import os.path
from definitions import ROOT_DIR
from pathlib import Path
import urllib.request
from urllib.parse import urlparse
from urllib.parse import parse_qs


class Dataset:

    def __init__(self, path: str or None, composer: str = None, cache: str = os.path.join(ROOT_DIR, "downloads/"),
                 immediate=None):

        if immediate:
            lines = list(immediate)
        else:
            lines = []

        if path:
            path = self.resolve_relative_path(path)
            with open(path) as f:
                lines = lines + f.readlines()

        self.__score_files = []

        if composer:
            self.__composer = composer
        else:
            if path:
                self.__composer = Path(path).stem
            else:
                self.__composer = "unknown"

        self.__cache = os.path.join(cache, self.__composer)

        downloaded = set()
        os.makedirs(self.__cache, exist_ok=True)

        for line in lines:
            if self.__should_skip(line):
                continue
            try:
                local_or_url = line.rstrip()
                parsed = urlparse(local_or_url)
                if not parsed.scheme:  # local file
                    self.__score_files.append(self.resolve_relative_path(local_or_url))
                else:
                    fname = self.__get_file_name(parsed)
                    if fname in downloaded:
                        # Sanity: already downloaded in this session
                        raise FileExistsError(f"File already exists: {fname}, url: {line}")

                    furlname = fname + ".url"
                    if os.path.isfile(fname) \
                            and os.path.isfile(furlname) \
                            and local_or_url == Path(furlname).read_text():
                        print(f"Using existing file {fname}")
                    else:
                        print(f"Downloading {local_or_url} > {fname}")
                        urllib.request.urlretrieve(local_or_url, fname)
                        downloaded.add(fname)
                        Path(furlname).write_text(local_or_url)

                    self.__score_files.append(fname)
            except Exception as ex:
                print(f'Failed parsing line {line} due to exception: {ex}')

    @staticmethod
    def resolve_relative_path(path):
        if os.path.isfile(path):
            return path
        else:
            another_path = os.path.join(ROOT_DIR, path)
            if os.path.isfile(another_path):
                return another_path
            else:
                raise FileNotFoundError(f"Not a file: {path}")

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
