#!/bin/bash -ex

# docker build . --tag x
# --user $(id -u):$(id -n)
docker run  \
    --rm -it \
    --security-opt apparmor=unconfined \
    --cap-add MKNOD --cap-add SYS_ADMIN \
    --device /dev/fuse \
    -v $PWD:/x \
    x bash
