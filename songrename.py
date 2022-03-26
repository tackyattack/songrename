#!/usr/bin/env python3
import csv
import logging
import os
import re
import argparse

ALLOWED_FILE_TYPES = [".mp3", ".wav", ".aiff",
                      ".aac", ".mp4", ".flac", ".m4a", ".ogg"]


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
        self.songs = {}
        self.albums = {}
        with open(path, newline='') as csvfile:
            self.logger.debug("opened catalog: " + path)
            reader = csv.DictReader(csvfile)
            for row in reader:
                song = SongItem(isrc_code=row['isrc_code'],
                                sequence_number=row['sequence_number'], track_name=row['track_name'])
                if song.isrc_code in self.songs:
                    old_name = self.songs[song.isrc_code].track_name
                    new_name = song.track_name
                    self.logger.info(
                        "duplicate ISRC: " + song.isrc_code + ":" + old_name + "->" + new_name)
                    if new_name != old_name:
                        self.logger.warning(
                            "duplicate ISRC overwrite!: " + song.isrc_code + ":" + old_name + "->" + new_name)
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
                try:
                    song = self.songs[isrc_code]
                except KeyError:
                    self.logger.warning("song mapping not found: " + file_path)
                    continue
                path_only, _ = os.path.split(file_path)
                new_filename = "{sequence_number}-{track_name}".format(
                    sequence_number=song.sequence_number, track_name=song.track_name)
                new_path_name = os.path.join(
                    path_only, new_filename + file_extension)
                self.logger.info("renaming file: " +
                                 file_path + " -> " + new_path_name)
                if not dry_run:
                    os.rename(file_path, new_path_name)
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
                os.rename(dir_path, new_path_name)

    def run_renamer(self, root_dir, catalog_path, dry_run):
        self.parse_catalog(catalog_path)
        self.rename_files(root_dir, dry_run)
        self.rename_directories(root_dir, dry_run)


def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(
            f"readable_dir:{path} is not a valid path")


def file_path(path):
    if os.path.isfile(path):
        return path
    else:
        raise argparse.ArgumentTypeError(
            f"readable_file:{path} is not a valid file")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='song renamer')
    parser.add_argument(
        "--warn", help="only log at warning level and above", action="store_true")
    parser.add_argument("--dry_run", help="do a dry run", action="store_true")
    parser.add_argument(
        'root_dir', help="root directory of files to rename", type=dir_path)
    parser.add_argument('catalog', help="catalog csv", type=file_path)
    args = parser.parse_args()
    if args.warn:
        log_level = logging.WARNING
    else:
        log_level = logging.DEBUG
    logging.basicConfig(
        filename='renamer.log', format='%(asctime)s:%(levelname)s:%(message)s', level=log_level)
    logger = logging.getLogger()
    sr = SongRenamer(logger)
    sr.run_renamer(args.root_dir, args.catalog, args.dry_run)
