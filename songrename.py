import csv
import logging
import os
import re

from sympy import false

ALLOWED_FILE_TYPES = [".mp3", ".wav", ".aiff", ".aac", ".mp4", ".flac"]


class SongItem:
    def __init__(self, isrc_code, sequence_number, track_name):
        self.isrc_code = isrc_code
        self.sequence_number = sequence_number
        self.track_name = track_name


class AlbumItem:
    def __init__(self, upc_code, album_name):
        self.upc_code = upc_code
        self.album_name = album_name


class SongRenamer:
    def __init__(self, logger):
        self.songs = {}
        self.albums = {}
        self.logger = logger
        self.logger.debug("starting song renamer")

    def parse_catalog(self, path):
        with open(path, newline='') as csvfile:
            self.logger.debug("opened catalog: " + path)
            reader = csv.DictReader(csvfile)
            for row in reader:
                song = SongItem(isrc_code=row['isrc_code'],
                                sequence_number=row['sequence_number'], track_name=row['track_name'])
                if song.isrc_code in self.songs:
                    self.logger.warning("duplicate ISRC: " + song.isrc_code)
                self.songs[song.isrc_code] = song
                upc_code = re.sub("[^0-9]", "", row['upc_code'])
                album = AlbumItem(
                    upc_code=upc_code, album_name=row['album_name'])
                if album.upc_code in self.albums:
                    existing_album = self.albums[album.upc_code]
                    if existing_album.upc_code != album.upc_code:
                        self.logger.warning(
                            "upc code differs: " + album.upc_code)
                    if existing_album.album_name != album.album_name:
                        self.logger.warning(
                            "album name differs: " + album.album_name)
                self.albums[album.upc_code] = album

    def rename_files(self, root_dir, dry_run):
        file_list = []
        for root, dirs, files in os.walk(root_dir):
            for name in files:
                file_list.append(os.path.join(root, name))
        for file_path in file_list:
            filename, file_extension = os.path.splitext(file_path)
            if file_extension.lower() in ALLOWED_FILE_TYPES:
                isrc_code = filename.split("-")[-1]
                song = self.songs[isrc_code]
                path_only, _ = os.path.split(file_path)
                new_filename = "{sequence_number}-{track_name}".format(
                    sequence_number=song.sequence_number, track_name=song.track_name)
                new_path_name = os.path.join(
                    path_only, new_filename + file_extension)
                self.logger.info("renaming file: " +
                                 file_path + " -> " + new_path_name)
                if not dry_run:
                    pass
            else:
                self.logger.warning("skipping: " + file_path)

    def rename_directories(self, root_dir, dry_run):
        dir_list = []
        for root, dirs, files in os.walk(root_dir):
            for name in dirs:
                dir_list.append(os.path.join(root, name))
        for dir_path in dir_list:
            dir_name = os.path.basename(dir_path)
            try:
                album = self.albums[dir_name]
            except KeyError:
                self.logger.warning(
                    "album folder mapping not found: " + dir_path)
                continue
            path_only, _ = os.path.split(dir_path)
            new_dir_name = album.album_name
            new_path_name = os.path.join(path_only, new_dir_name)
            self.logger.info("renaming directory: " +
                             dir_path + " -> " + new_path_name)
            if not dry_run:
                pass


logging.basicConfig(
    filename='renamer.log', format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger()
sr = SongRenamer(logger)
sr.parse_catalog("catalog.csv")
sr.rename_files("sample/", False)
sr.rename_directories("sample/", False)
