#!/usr/bin/env python3
"""A Command-Line Interface Python script that will output a list of duplicate
files identified by their absolute path and name."""

from argparse import ArgumentParser
from hashlib import md5
from json import dumps
from os import stat, walk
from os.path import abspath, expanduser, getsize, islink, join
from stat import S_IFMT, S_IFREG

BUFSIZE = 8 * 1024


def parse_arguments():
    """Parse command line strings into arguments the program requires."""
    # Waypoint 1:
    parser = ArgumentParser(description='Duplicate Files Finder')
    parser.add_argument('-p', '--path', type=str, required=True,
                        help='the root directory to start scanning for '
                             'duplicate files')
    parser.add_argument('-c', '--compare', action='store_true',
                        help='comparing files method to find duplicate files.')
    return parser.parse_args()


# Waypoint 2:
def scan_files(path):
    """Search for all the files from the specified path.

    Returns: A flat list of files (ignore symbolic links) scanned recursively
             from this specified path.

    """
    return list(filter(lambda x: not islink(x),
                       [join(root, f) for root, _, files in
                        walk(abspath(expanduser(path))) for f in files]))


# Waypoint 3:
def group_files_by_size(file_path_names):
    """Group files by their size.

    Args:
        file_path_names: a flat list of absolute file path names.

    Returns: A list of groups of at least two files that have the same size.

    Ignore empty files, which size is of 0 bytes.

    """
    groups = {}
    # Create the same-file-size-groups:
    for filename in file_path_names:
        size = getsize(filename)
        if size:  # Ignore empty files.
            groups.setdefault(size, []).append(filename)
    return [group for group in groups.values() if
            len(group) > 1]  # groups of at least 2 files


# Waypoint 4:
def get_file_checksum(file_path):
    """ Generate the hash value of a file's content using md5."""
    try:
        with open(file_path, 'rb') as file:
            return md5(file.read()).hexdigest()
    except OSError:
        return None


# Waypoint 5:
def group_files_by_checksum(file_path_names):
    """Group files by their checksum

    Args:
        file_path_names: A flat list of the absolute path and name of files.

    Returns: A list of groups of duplicate files.

    """
    groups = {}
    for file_path in file_path_names:
        checksum = get_file_checksum(file_path)
        if checksum:  # Ignore broken link.
            groups.setdefault(checksum, []).append(file_path)
    return [group for group in groups.values() if
            len(group) > 1]  # groups of at least 2 files


# Waypoint 6:
def find_duplicate_files(file_path_names):
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
def print_output(result):
    """Write on the stdout a JSON expression corresponding to the result."""
    print(dumps(result))


# Waypoint 8:
def compare_files(f1, f2, shallow=True):
    """Compare two files.

    Args:
        f1: First file name
        f2: Second file name
        shallow: Just check stat signature (do not read the files),
                 defaults to True.

    Returns: True if the files are the same, False otherwise.

    """

    def _sig(st):
        """Generate a stat signature."""
        return S_IFMT(st.st_mode), st.st_size, st.st_mtime

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
    if shallow and s1 == s2:
        return True
    if s1[1] != s2[1]:
        return False
    return _do_compare(f1, f2)


def find_duplicate_files_by_cmp(file_path_names):
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
        file_path_names = list(
                set(file_path_names) - set(group_duplicate_files))
        if len(group_duplicate_files) > 1:
            groups.append(group_duplicate_files)
    return groups


def main():
    """Demonstration and running."""
    args = parse_arguments()
    file_path_names = scan_files(args.path)
    if args.compare:
        print_output(find_duplicate_files_by_cmp(file_path_names))
    else:
        print_output(find_duplicate_files(file_path_names))


if __name__ == '__main__':
    main()
