FROM liquidinvestigations/hoover-snoop2:0.16-base

RUN apt-get update && apt-get install -y gosu s3fs cmake libfuse-dev build-essential

RUN mkdir /x
WORKDIR /x

COPY . .

RUN bash ./build.sh
