#!/usr/bin/env python3
try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

import argparse
import os
import pysbd
import queue
import sys
import tempfile
import threading
import shutil
import sys
import tempfile
import contextlib
import edge_tts

import openai

try:
    from playsound import playsound
except ImportError:
    print("Error: missing required package 'playsound'. !pip install playsound")
    sys.exit(1)

@contextlib.contextmanager
def tempdir():
    path = tempfile.mkdtemp()
    try:
        yield path
    finally:
        try:
            shutil.rmtree(path)
        except IOError:
            sys.stderr.write('Failed to clean up temp dir {}'.format(path))

class SimpleAudioPlayer:
    def __init__(self):
        self._queue = queue.Queue()
        self.running = True
        self._thread = threading.Thread(target=self.__play_audio_loop, daemon=True)
        self._thread.start()

    def put(self, file):
        self._queue.put(file)

    def stop(self):
        self.running = False
        self._thread.join()
        try:
            while True:
                file = self._queue.get_nowait()
                if os.path.exists(file):
                    os.unlink(file)
        except queue.Empty as e:
            pass

    def __play_audio_loop(self):
        while self.running:
            try:
                while True:
                    file = self._queue.get(block=True, timeout=0.01)

                    try:
                        playsound(file)
                    finally:
                        os.unlink(file)

            except queue.Empty as e:
                continue

class OpenAI_tts:
    def __init__(self, model, voice, speed, base_dir):
        self.base_dir = base_dir
        self.model = model
        if model == "edge-tts":
            self.tts_client = EdgeTTS(voice, speed)
        else:
            self.tts_client = openai.OpenAI(
                # export OPENAI_API_KEY=sk-11111111111
                # export OPENAI_BASE_URL=http://localhost:8000/v1
                api_key = os.environ.get("OPENAI_API_KEY", "sk-ip"),
                base_url = os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1"),
            )
            self.params = {
                'model': model,
                'voice': voice,
                'speed': speed
            }

    def speech_to_file(self, text: str) -> None:
        if self.model == "edge-tts":
            return self.tts_client.speech_to_file(text, self.base_dir)
        else:
            with self.tts_client.audio.speech.with_streaming_response.create(
                    input=text, response_format='opus', **self.params
                ) as response:
                tf, output_filename = tempfile.mkstemp(suffix='.wav', prefix="audio_reader_", dir=self.base_dir)
                response.stream_to_file(output_filename)
                return output_filename

class EdgeTTS:
    def __init__(self, voice, speed):
        self.voice = voice
        self.speed = speed

    async def speech_to_file(self, text: str, base_dir: str) -> str:
        communicate = edge_tts.Communicate(text, self.voice, rate=self.speed)
        tf, output_filename = tempfile.mkstemp(suffix='.wav', prefix="audio_reader_", dir=base_dir)
        await communicate.save(output_filename)
        return output_filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Text to speech player',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-m', '--model', action='store', default="tts-1", help="The OpenAI model")
    parser.add_argument('-v', '--voice', action='store', default="alloy", help="The voice to use")
    parser.add_argument('-s', '--speed', action='store', default=1.0, help="How fast to read the audio")

    args = parser.parse_args()

    try:
        with tempdir() as base_dir:
            player = SimpleAudioPlayer()
            reader = OpenAI_tts(voice=args.voice, model=args.model, speed=args.speed, base_dir=base_dir)
            seg = pysbd.Segmenter(language='en', clean=True) # text is dirty, clean it up.

            for raw_line in sys.stdin:
                for line in seg.segment(raw_line):
                    if not line:
                        continue

                    print(line)
                    player.put(reader.speech_to_file(line))

            player.stop()

    except KeyboardInterrupt:
        pass
