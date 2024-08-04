#!/bin/bash

#[ -f speech.env ] && . speech.env

echo "First startup may download 2GB of speech models. Please wait."

bash download_voices_tts-1.sh
bash download_voices_tts-1-hd.sh $PRELOAD_MODEL

[ -e /app/deepspeed.flag ] && DEEPSPEED="--use-deepspeed"

python speech.py ${PRELOAD_MODEL:+--preload $PRELOAD_MODEL} \
	--log-level $LOG $TIMER $DEEPSPEED $EXTRA_ARGS $@

