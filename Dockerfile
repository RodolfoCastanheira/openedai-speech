FROM python:3.11-slim

RUN pip install -U pip # --mount=type=cache,target=/root/.cache/pip

ARG TARGETPLATFORM
RUN apt-get update && apt-get install --no-install-recommends -y curl ffmpeg
RUN if [ "$TARGETPLATFORM" != "linux/amd64" ]; then apt-get install --no-install-recommends -y build-essential ; fi
RUN if [ "$TARGETPLATFORM" != "linux/amd64" ]; then curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y ; fi
ENV PATH="/root/.cargo/bin:${PATH}"

ARG DEEPSPEED=false
RUN if [ "$DEEPSPEED" = "true" ]; then \
    curl -O https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    rm cuda-keyring_1.1-1_all.deb && \
    apt-get update && \
    apt-get install --no-install-recommends -y libaio-dev build-essential cuda-toolkit; \
  touch /app/deepspeed.flag; \
fi


WORKDIR /app
RUN mkdir -p voices config

ARG USE_ROCM
ENV USE_ROCM=${USE_ROCM}

COPY requirements*.txt /app/
RUN if [ "${USE_ROCM}" = "1" ]; then mv /app/requirements-rocm.txt /app/requirements.txt; fi
RUN pip install -r requirements.txt # --mount=type=cache,target=/root/.cache/pip

RUN apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /root/.cache/pip

COPY *.py *.sh *.default.yaml README.md LICENSE /app/

ARG PRELOAD_MODEL
ENV PRELOAD_MODEL=${PRELOAD_MODEL}
ENV TTS_HOME=voices
ENV HF_HOME=voices
ENV COQUI_TOS_AGREED=1
ENV CUDA_HOME=/usr/local/cuda

CMD bash startup.sh

