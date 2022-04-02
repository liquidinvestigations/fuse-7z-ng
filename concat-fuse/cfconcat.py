#!/usr/bin/env python3

# concat-fuse
# Copyright (C) 2015 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse
import hashlib
import os
import subprocess
import sys
import tempfile


from typing import List


class ConcatFuse:

    @staticmethod
    def unmount(basedir=None):
        if basedir is None:
            basedir = ConcatFuse.find_basedir()

        if os.path.ismount(basedir):
            subprocess.check_call(["fusermount", "-u", basedir])

    @staticmethod
    def find_basedir():
        runtime_base_dir = os.environ.get("XDG_RUNTIME_DIR")
        if runtime_base_dir:
            basedir = os.path.join(runtime_base_dir, "concat-fuse")
        else:
            basedir = os.path.join(os.environ["HOME"], ".concat-fuse")
        return basedir

    def __init__(self, basedir=None, concat_fuse_exe=None):
        """Mounts concat-fuse to basedir when needed"""

        if basedir is None:
            self.basedir = ConcatFuse.find_basedir()
        else:
            self.basedir = basedir

        if concat_fuse_exe is None:
            self.concat_fuse_exe = "concat-fuse"
        else:
            self.concat_fuse_exe = concat_fuse_exe

        if not os.path.exists(self.basedir):
            os.mkdir(self.basedir)

        if not os.path.ismount(self.basedir):
            subprocess.check_call([self.concat_fuse_exe, self.basedir])

        self.check_version()

    def check_version(self):
        expected_version = "3"
        with open(os.path.join(self.basedir, "VERSION")) as fin:
            version = fin.read().rstrip()
        if version != expected_version:
            raise Exception("incorrect concat-fuse version, expected {} got {}".format(expected_version, version))

    def concat(self, files: List[str]):
        """Send the file list to concat-fuse and return the filename of the virtual file"""

        # write the file list to concat-fuse
        files_serialized: bytes = b"\0".join([os.fsencode(f) for f in files])
        with open(os.path.join(self.basedir, "from-file0/control"), "wb") as fout:
            fout.write(files_serialized)

        # return the virtual file name
        multifile_id = hashlib.sha1(files_serialized).hexdigest()
        virtual_file = os.path.join(self.basedir, "from-file0", multifile_id)
        return virtual_file

    def glob(self, globs):
        """Send the glob list to concat-fuse and return the filename of the virtual file"""

        # write the file list to concat-fuse
        globs_serialized = "\0".join(globs)
        with open(os.path.join(self.basedir, "from-glob0/control"), "wb") as fout:
            fout.write(globs_serialized)

        # return the virtual file name
        multifile_id = hashlib.sha1(globs_serialized).hexdigest()
        virtual_file = os.path.join(self.basedir, "from-glob0", multifile_id)
        return virtual_file

    def zip(self, zip):
        """Send the zip to concat-fuse and return the filename of the virtual file"""

        # write the zip filename list to concat-fuse
        with open(os.path.join(self.basedir, "from-zip/control"), "wb") as fout:
            fout.write(zip)

        # return the virtual file name
        multifile_id = hashlib.sha1(zip).hexdigest()
        virtual_file = os.path.join(self.basedir, "from-zip", multifile_id)
        return virtual_file


def splitlines0(data):
    lst = data.split("\0")
    if lst and lst[-1] == "":
        del lst[-1]
    return lst


def parse_args():
    parser = argparse.ArgumentParser(description="Create virtual concatenated files.",
                                     epilog="The name of the virtual file is returned on stdout.")

    # argparser does not allow freely mixing optional and positional
    # arguments, this limits the functionality of `cfconcat` somewhat, but
    # shouldn't be to critical: http://bugs.python.org/issue14191

    parser.add_argument('-v', '--version', action='store_true', help="Print version number")

    concat_fuse_group = parser.add_argument_group("concat-fuse options")
    concat_fuse_group.add_argument('-u', '--unmount', action='store_true', help="Unmount concat-fuse")
    concat_fuse_group.add_argument('-e', '--exe', metavar="EXE", type=str, help="Use EXE instead of concat-fuse")
    concat_fuse_group.add_argument('-m', '--mountpoint', metavar="MOUNTPOINT", type=str, default=None,
                                   help="Use MOUNTPOINT instead of default")

    general_group = parser.add_argument_group("general options")
    general_group.add_argument('--ext', metavar="EXT", type=str,
                               help="Add an extension to the virtual filename")

    files_group = parser.add_argument_group("file list options", "Options for static file lists.")
    files_group.add_argument('-n', '--dry-run', action='store_true',
                             help="Don't send file list to concat-fuse, print to stdout")
    files_group.add_argument('-k', '--keep', action='store_true',
                             help="Continue even when files are missing")
    files_group.add_argument('FILES', nargs='*',
                             help="Files to virtually concatenate")
    files_group.add_argument('--from-file', metavar='FILE', action='append', default=[],
                             help="Read files from FILE, newline separated")
    files_group.add_argument('--from-file0', metavar='FILE', action='append', default=[],
                             help="Read files from FILE, '\\0' separated")
    files_group.add_argument('-', dest="stdin", action='store_true',
                             help="Read files from stdin")
    files_group.add_argument('-0', dest="stdin0", action='store_true',
                             help="Read files from stdin, '\\0' separated")

    glob_group = parser.add_argument_group("glob options",
                                           ("Glob pattern act as dynamic file lists and the underlying virtual "
                                            "file can be dynamically updated when new files arrive."))
    glob_group.add_argument('-g', '--glob', metavar='GLOB', action='append', default=[],
                            help="Use glob pattern to select files")

    zip_group = parser.add_argument_group("zip options",
                                          ("Read files from a .zip archive"))
    zip_group.add_argument('-z', '--zip', metavar='ARCHIVE', action='store',
                           help="Read files from ARCHIVE")

    return parser.parse_args()


def make_virtual_filename(args):
    # generate the file list
    files = []

    if args.stdin:
        files.extend(sys.stdin.read().splitlines())
    elif args.stdin0:
        files.extend(splitlines0(sys.stdin.read()))

    for f in args.from_file:
        with open(f, "r") as fin:
            files.extend(fin.read().splitlines())

    for f in args.from_file0:
        with open(f, "rb") as fin:
            files.extend(splitlines0(fin.read()))

    files.extend(args.FILES)

    files = [os.path.abspath(f) for f in files]

    # generate glob list
    globs = []
    globs.extend(args.glob)
    globs = [os.path.abspath(g) for g in globs]

    # check if arguments are valid
    if globs and files:
        raise Exception("Can't mix globs and regular files")
    elif globs and args.zip:
        raise Exception("Can't mix globs and zip files")
    elif files and args.zip:
        raise Exception("Can't mix files and zip files")

    errors = False
    for f in files:
        if not os.path.exists(f):
            print("{}: No such file or directory".format(f), file=sys.stderr)
            errors = True

    if errors and not args.keep:
        raise Exception("detected errors when scanning files")

    if files:
        if args.dry_run:
            for f in files:
                print(f)
        else:
            concat_fuse = ConcatFuse(args.mountpoint, args.exe)
            virtual_filename = concat_fuse.concat(files)
            return virtual_filename
    elif globs:
        if args.dry_run:
            for g in globs:
                print(g)
        else:
            concat_fuse = ConcatFuse(args.mountpoint, args.exe)
            virtual_filename = concat_fuse.glob(globs)
            return virtual_filename
    elif args.zip:
        zip_filename = os.path.abspath(args.zip)
        if not os.path.exists(zip_filename):
            raise Exception("{}: No such file or directory".format(zip_filename))
        else:
            concat_fuse = ConcatFuse(args.mountpoint, args.exe)
            virtual_filename = concat_fuse.zip(zip_filename)
            return virtual_filename
    else:
        raise Exception("{}: fatal error: no input files provided".format(sys.argv[0]))


def main():
    args = parse_args()

    if args.version:
        print("cfconcat 0.3.2")
    elif args.unmount:
        ConcatFuse.unmount(args.mountpoint)
    else:
        virtual_filename = make_virtual_filename(args)
        if args.ext is not None:
            dir = tempfile.mkdtemp()
            link_name = os.path.join(dir, os.path.basename(virtual_filename) + args.ext)
            os.symlink(virtual_filename, link_name)
            print(link_name)
        else:
            print(virtual_filename)


if __name__ == "__main__":
    main()


# EOF #
