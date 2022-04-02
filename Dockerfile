FROM liquidinvestigations/hoover-snoop2:0.16-base

RUN apt-get update && apt-get install -y s3fs cmake libfuse-dev build-essential libfuse-dev libmhash-dev libminizip-dev     build-essential pkg-config cmake g++ clang libfuse-dev libmhash-dev libminizip-dev zlib1g-dev libssl-dev libgtest-dev

RUN mkdir /x
WORKDIR /x

COPY . .

RUN bash ./build.sh
