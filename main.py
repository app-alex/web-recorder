from selenium import webdriver
import cv2
import pyautogui
import pyaudio
import audioop
import wave
import numpy as np
import threading
import time


class WebBrowser:
    def __init__(self):
        self.browser = webdriver.Chrome()

    def browse(self, url="https://www.youtube.com/watch?v=vGJTaP6anOU"):
        self.browser.get(url)


class VideoRecorder:
    def __init__(self):
        self.screen_size = pyautogui.size()
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.fps = 20.0
        self.out = cv2.VideoWriter("output_video.avi", self.fourcc, self.fps, self.screen_size)

    def record(self, record_time=120):
        print("Start video recording")

        def _record(start_time=time.time(), frame_index=-1):
            time_past = time.time() - start_time
            frame_index += 1
            if time_past < record_time:
                threading.Timer(1 / self.fps - (time_past - frame_index / self.fps), _record,
                                [start_time, frame_index]).start()

                img = pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.out.write(frame)
            else:
                cv2.destroyAllWindows()
                self.out.release()
                print("Done video recording")

        _record()


class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.frames_volume = []
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 2
        self.sample_rate = 44100
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.sample_rate,
                                  input=True,
                                  output=True,
                                  input_device_index=2,
                                  frames_per_buffer=self.chunk)

    def record(self, record_time=120):
        print("Start audio recording")

        def _record():
            for i in range(0, int(self.sample_rate / self.chunk * record_time)):
                data = self.stream.read(self.chunk)
                self.frames.append(data)

                rms = audioop.rms(data, 2)
                db = 20 * np.log10(rms, where=rms > 0)
                self.frames_volume.append(db)

            print("Finished audio recording.")

            self._write_file_audio_volume()

            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

            wav_file = wave.open("output_audio.wav", "wb")
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.p.get_sample_size(self.format))
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(b"".join(self.frames))
            wav_file.close()

        audio_thread = threading.Thread(target=_record)
        audio_thread.start()

    def _write_file_audio_volume(self):
        with open('audio_volume.txt', 'w') as f:
            for db in self.frames_volume:
                f.write("%s\n" % db)


if __name__ == '__main__':
    webScraper = WebBrowser()
    webScraper.browse()

    videoRecorder = VideoRecorder()
    videoRecorder.record()

    audioRecorder = AudioRecorder()
    audioRecorder.record()
