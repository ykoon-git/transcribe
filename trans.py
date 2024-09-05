import pyaudio
import boto3
import json
from botocore.exceptions import BotoCoreError, ClientError
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

# AWS 설정
session = boto3.Session(profile_name='default')
client = TranscribeStreamingClient(region="us-west-2")

# 오디오 설정
CHUNK = 1024 * 2
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


def get_audio_stream():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    return stream
class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, transcript_result_stream):
        super().__init__(transcript_result_stream)
        self.last_result = ""

    def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            if not result.is_partial:
                self.last_result = result.alternatives[0].transcript
                print(f"자막: {self.last_result}")

def main():
    stream = get_audio_stream()

    try:
        # 스트리밍 세션 시작
        stream_response = client.start_stream_transcription(
            language_code="ko-KR",
            media_sample_rate_hz=RATE,
            media_encoding="pcm",
        )

        # 이벤트 핸들러 연결
        handler = MyEventHandler(stream_response.transcript_result_stream)
        stream_response.add_event_handler(handler)

        # 오디오 스트리밍
        with stream_response.stream_transcription() as stream_transcription:
            print("* 녹음 시작")
            while True:
                data = stream.read(CHUNK)
                stream_transcription.send_audio_event(audio_chunk=data)

    except (BotoCoreError, ClientError) as error:
        print(f"Error occurred: {error}")
    finally:
        stream.stop_stream()
        stream.close()


if __name__ == "__main__":
    main()
