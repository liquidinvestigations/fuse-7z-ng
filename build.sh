#!/bin/bash -ex

cd "$(dirname ${BASH_SOURCE[0]})"

SOURCE_LIB7ZIP=$PWD/lib7zip
SOURCE_P7ZIP=$PWD/p7zip
SOURCE_FUSE_7z=$PWD

BUILD=$(mktemp -d)
BUILD_LIB7ZIP=$BUILD/lib7zip
BUILD_FUSE_7z=$BUILD/fuse-7z
mkdir -p $BUILD_LIB7ZIP
mkdir -p $BUILD_FUSE_7z

(
cd $BUILD_LIB7ZIP
cmake $SOURCE_LIB7ZIP -DCMAKE_CXX_FLAGS=-w
make -j8
)

(
cd $BUILD_FUSE_7z
cmake $SOURCE_FUSE_7z  -Dlib7zip_binDir=$BUILD_LIB7ZIP/src -Dlib7zip_includeDir=$SOURCE_LIB7ZIP/src -DCMAKE_CXX_FLAGS=-w
make -j8
cp fuse_7z_ng /usr/local/bin
)

rm -rf $BUILD
