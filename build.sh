#!/bin/bash

set -ex
cd "$(dirname ${BASH_SOURCE[0]})"

SOURCE_LIB7ZIP=$PWD/lib7zip
SOURCE_P7ZIP=$PWD/p7zip
SOURCE_CONCAT_FUSE=$PWD/concat-fuse
SOURCE_FUSE_7z=$PWD

BUILD=$(mktemp -d)
BUILD_LIB7ZIP=$BUILD/lib7zip
BUILD_FUSE_7z=$BUILD/fuse-7z
BUILD_CONCAT_FUSE=$BUILD/concat-fuse


# concat-fuse
# -----------
mkdir -p $BUILD_CONCAT_FUSE
cd $BUILD_CONCAT_FUSE
cmake $SOURCE_CONCAT_FUSE -DWERROR=OFF -DWARNINGS=OFF  -DBUILD_TESTS=OFF
make -j8
make install

# lib7zip
# -----------
mkdir -p $BUILD_LIB7ZIP
cd $BUILD_LIB7ZIP
cmake $SOURCE_LIB7ZIP -DCMAKE_CXX_FLAGS=-w
make -j8

# fuse-7z
# -----------
mkdir -p $BUILD_FUSE_7z
cd $BUILD_FUSE_7z
cmake $SOURCE_FUSE_7z  -Dlib7zip_binDir=$BUILD_LIB7ZIP/src -Dlib7zip_includeDir=$SOURCE_LIB7ZIP/src -DCMAKE_CXX_FLAGS=-w
make -j8
cp fuse_7z_ng /usr/local/bin


cd $SOURCE_FUSE_7z
rm -rf $BUILD


# check
( /usr/local/bin/concat-fuse -V || true ) | grep version
( /usr/local/bin/fuse_7z_ng -V || true ) | grep version
/usr/local/bin/cfconcat -v
