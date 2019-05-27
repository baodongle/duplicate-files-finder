#!/usr/bin/env python3
"""A Command-Line Interface Python script that will output a list of duplicate
files identified by their absolute path and name."""
from argparse import ArgumentParser, Namespace
from hashlib import md5
from json import dumps
from os import stat, walk
from os.path import abspath, expanduser, getsize, islink, join
from stat import S_IFMT, S_IFREG
from typing import Any, Callable, Dict, List, Union

BUFSIZE = 8 * 1024


# Waypoint 1:
def parse_arguments() -> Namespace:
    """Parse command line strings into arguments the program requires."""
    parser = ArgumentParser(description='Duplicate Files Finder')
    parser.add_argument('-p', '--path', type=str, required=True,
                        help='the root directory to start scanning for '
                             'duplicate files')
    parser.add_argument('-c', '--compare', action='store_true',
                        help='use comparing files method to find duplicate'
                             'files.')
    return parser.parse_args()


# Waypoint 2:
def scan_files(path: str) -> List[str]:
    """Search for all the files from the specified path.

    Args:
        path: An absolute path.

    Returns: A flat list of files (ignore symbolic links) scanned recursively
             from this specified path.

    """
    return list(filter(lambda x: not islink(x),
                       [join(root, f) for root, _, files in
                        walk(abspath(expanduser(path))) for f in files]))


def group_files(file_path_names: List[str], func: Callable) \
        -> List[List[str]]:
    """Group files according to a criterion.

    Args:
        file_path_names: A flat list of absolute file path names.
        func: The function that returns a criterion.

    Returns: A list of groups of at least 2 files that have the same criterion.

    """
    groups: Dict[Any, List[str]] = {}
    for filename in file_path_names:
        criterion = func(filename)
        if criterion:
            groups.setdefault(criterion, []).append(filename)
    return [group for group in groups.values() if
            len(group) > 1]  # groups of at least 2 files


# Waypoint 3:
def group_files_by_size(file_path_names: List[str]) -> List[List[str]]:
    """Group files by their size.

    Args:
        file_path_names: A flat list of absolute file path names.

    Returns: A list of groups of at least two files that have the same size.

    """
    return group_files(file_path_names, getsize)


# Waypoint 4:
def get_file_checksum(file_path: str) -> Union[str, None]:
    """Generate the hash value of a file's content using md5 hash algorithm.

    Args:
        file_path: An absolute path of file.

    Returns: The MD5 hash value of the content of this file.

    """
    try:
        with open(file_path, 'rb') as file:
            return md5(file.read()).hexdigest()
    except OSError:
        return None


# Waypoint 5:
def group_files_by_checksum(file_path_names: List[str]) \
        -> List[List[str]]:
    """Group files by their checksum

    Args:
        file_path_names: A flat list of the absolute path and name of files.

    Returns: A list of groups of at least 2 files that have the same checksum.

    """
    return group_files(file_path_names, get_file_checksum)


# Waypoint 6:
def find_duplicate_files(file_path_names: List[str]) -> List[List[str]]:
    """Find all duplicate files.

    Args:
        file_path_names: A flat list of the absolute path and name of files.

    Returns: A list of groups of duplicate files.

    """
    groups = []
    for group in group_files_by_size(file_path_names):
        groups.extend(group_files_by_checksum(group))
    return groups


# Waypoint 7:
def print_output(result: Any) -> None:
    """Write on the stdout a JSON expression corresponding to the result."""
    print(dumps(result, indent=4))


# Waypoint 8:
def compare_files(f1: str, f2: str) -> bool:
    """Compare two files.

    Args:
        f1: First file name
        f2: Second file name

    Returns: True if the files are the same, False otherwise.

    """

    def _sig(st):
        """Generate a stat signature."""
        return S_IFMT(st.st_mode), st.st_size

    def _do_compare(file1, file2):
        """Compare contents of two files."""
        bufsize = BUFSIZE
        try:
            with open(file1, 'rb') as fp1, open(file2, 'rb') as fp2:
                while True:
                    b1 = fp1.read(bufsize)
                    b2 = fp2.read(bufsize)
                    if b1 != b2:
                        return False
                    if not b1:
                        return True
        except OSError:
            return False

    s1 = _sig(stat(f1))
    s2 = _sig(stat(f2))
    if s1[0] != S_IFREG or s2[0] != S_IFREG:
        # If not regular files:
        return False
    if s1[1] != s2[1]:
        return False
    return _do_compare(f1, f2)


def find_duplicate_files_by_comparing(file_path_names: List[str]) \
        -> List[List[str]]:
    """Find all duplicate files by comparing.

    Args:
        file_path_names: A flat list of the absolute path and name of files.

    Returns: A list of groups of duplicate files.

    """
    groups = []
    while file_path_names:
        current = file_path_names[0]
        group_duplicate_files = [current]
        for filename in file_path_names[1:]:
            if compare_files(current, filename):
                group_duplicate_files.append(filename)
        file_path_names = [e for e in file_path_names if
                           e not in set(group_duplicate_files)]
        if len(group_duplicate_files) > 1:  # groups of at least 2 files
            groups.append(group_duplicate_files)
    return groups


def main() -> None:
    """Demonstration and running."""
    args = parse_arguments()
    if args.compare:
        print_output(find_duplicate_files_by_comparing(scan_files(args.path)))
    else:
        print_output(find_duplicate_files(scan_files(args.path)))


if __name__ == '__main__':
    main()
