import os
import csv
import json
import shutil
from pathlib import Path
from fnmatch import fnmatch
from typing import Iterable


def get_ascending_folder(current_file_path: str, folders_above: int = 2) -> str:
    """
    Get folder path by file path and number of folders above.
    folders_above = 1 -> current folder
    folders_above = 2 -> grand-parent folder

    Usage (i.e., in /PROJECT/src/settings.py):

    from vlad_utils.file import get_ascending_folder
    PROJECT_DIR = get_ascending_folder(__file__, folders_above=2)   # returns /PROJECT/
    """
    for i in range(folders_above):
        current_file_path = os.path.dirname(current_file_path)
    return current_file_path


def find_files_by_pattern(dir_path: str, pattern: str) -> Iterable[str]:
    """Return files in directory matching name pattern"""
    for file_name in os.listdir(dir_path):
        if fnmatch(file_name, pattern):
            yield os.path.join(dir_path, file_name)


def list_children_paths(dir_path: str, ignore_hidden=False) -> Iterable[str]:
    """List all files in directory as absolute paths"""
    for file_name in os.listdir(dir_path):
        # skip dotted files and Icon? (appears in macOS if change folder icon)
        if ignore_hidden and file_name.startswith('.'):
            continue
        yield os.path.join(dir_path, file_name)


def is_folder(path: str, treat_pseudo_folders_as_files=True) -> bool:
    """Check if path is a folder"""
    if not os.path.isdir(path):
        return False

    # apps and numbers - treat as files by default
    pseudo_folder_extensions = ['.app', '.numbers']
    if treat_pseudo_folders_as_files and any(path.lower().endswith(e) for e in pseudo_folder_extensions):
        return False

    # folders
    return True


def split_file_path(file_path: str) -> (str, str, str):
    """Split file path into dir_name, file_name and extension"""
    p = Path(file_path)
    return p.parent, p.stem, p.suffix.strip('.')


def load_file(file_path: str | Path) -> str:
    """Load string from text file"""
    with open(file_path, mode='r', encoding='utf-8') as f:
        return f.read()


def load_json(file_path: str | Path) -> dict:
    """Dump dict to json file"""
    with open(file_path, mode='r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict , file_path: str):
    """Load dict from json file"""
    with open(file_path, mode='w', encoding='utf-8') as f:
        json.dump(data, fp=f, indent=2, ensure_ascii=False)


def load_csv(file_paths: str | Path, encoding: str = 'utf-8') -> list[dict]:
    """Load list of dicts from CSV file"""
    with open(file_paths, mode='r', encoding=encoding) as f:
        csv_reader = csv.DictReader(f)
        return list(csv_reader)


def recreate_folder(folder_path: str) -> None:
    """Delete folder and create it again"""
    shutil.rmtree(folder_path, ignore_errors=True)
    os.makedirs(folder_path)
