import argparse
import os
import json
import pysrt
import librosa
import soundfile
import warnings
import time
import re
from pytube import YouTube
from pytube.exceptions import AgeRestrictedError

SUBTITLE_MAPPING = {
    "fr": "French",
    "en": "English",
    "de": "German",
    "zh": "Chinese",
}

AUDIO_SAMPLING_RATE = 16000

def time2ms(time):
    return ((time.hour * 60 + time.minute) * 60 + time.second) * 1000 + time.microsecond // 1000

def filter_subtitle(subtitle: str, alphabet):
    subtitle_only_alphabet = ''.join(c for c in subtitle.lower() if c in alphabet)
    subtitle_only_single_space = re.sub(r'\s+',' ', subtitle_only_alphabet)
    return subtitle_only_single_space.strip()

def success(data_path, msg, samples, total_time):
    log(data_path, msg)
    update_metric(data_path, {"success": 1, "samples": samples, "total_time": total_time})

def error(data_path, msg):
    log(data_path, msg)
    update_metric(data_path, {"success": 0 })

def log(data_path, msg):
    print(msg)
    with open(os.path.join(data_path, "log.txt"), "a") as f:
        f.write(msg + "\n")

def update_metric(data_path, values):
    try:
        with open(os.path.join(data_path, "metric.json"), "r") as f:
            metric = json.load(f)
            downloaded_videos = metric["download"]
            success_videos = metric["success"]
            samples = metric["samples"]
            total_time = metric["total_time"]
    except:
        downloaded_videos = 0
        success_videos = 0
        samples = 0
        total_time = 0

    downloaded_videos += 1
    success_videos += values.get("success", 0)
    samples += values.get("samples", 0)
    total_time += values.get("total_time", 0)

    with open(os.path.join(data_path, "metric.json"), "w") as f:
        json.dump({"download": downloaded_videos, "success": success_videos, "samples": samples, "total_time": total_time, "avg_time": total_time / samples if samples > 0 else 0}, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lang", help="Language used", default="fr")
    parser.add_argument("-n", "--num_videos", help="Number of videos to download", default=1, type=int)
    args = parser.parse_args()

    lang = args.lang
    num_videos = args.num_videos

    with open(f"alphabet/{lang}.txt", 'r') as f:
        alphabet = set(f.read().replace('\n', ''))

    youtuber_videos = {}
    for file in os.listdir(f"videos/{lang}"):
        youtuber = file.split('.')[0]
        with open(f"videos/{lang}/{file}", "r") as f:
            videos = [line.strip() for line in f.readlines()]
            youtuber_videos[youtuber] = list(reversed(videos))
            os.makedirs(f"data/{lang}/{youtuber}", exist_ok=True)

            if not os.path.exists(f"data/{lang}/{youtuber}/metric.json"):
                with open(f"data/{lang}/{youtuber}/metric.json", "w") as f:
                    json.dump({"download": 0, "success": 0, "samples": 0, "total_time": 0, "avg_time": 0}, f)
    
    print(f"Downloading {num_videos} videos for {list(youtuber_videos.keys())}")
    for _ in range(num_videos):
        for youtuber in youtuber_videos:
            data_path = f"data/{lang}/{youtuber}"
            with open(f"{data_path}/metric.json", "r") as f:
                metric = json.load(f)
                downloaded_videos = metric["download"]
                success_videos = metric["success"]

            total_videos = len(youtuber_videos[youtuber])
            print("\n" + "=" * 50)
            print(f"[{youtuber}] Videos success/downloaded/total: {success_videos}/{downloaded_videos}/{total_videos}")

            if downloaded_videos >= total_videos:
                print(f"Already downloaded all available videos for {youtuber}")
                continue

            video_id = youtuber_videos[youtuber][downloaded_videos]

            url = f"https://www.youtube.com/watch?v={video_id}"
            youtube = YouTube(url)
            print(f"[{youtuber}] Downloading video {downloaded_videos+1} {url}. Title: {youtube.title}")

            subtitle_lang = SUBTITLE_MAPPING[lang].capitalize()
            try:
                youtube.bypass_age_gate()
            except AgeRestrictedError as are:
                error(data_path, f"{url}: age restricted, {are}")
                continue
            except Exception as e:
                print("Error:", e)
                continue

            caption_exist = False
            for captions in youtube.caption_tracks:
                print("Available subtitles:", captions.name)
                if captions.name.startswith(subtitle_lang):
                    captions = captions.generate_srt_captions()
                    audio_path = os.path.join(data_path, f"{video_id}")
                    os.makedirs(audio_path, exist_ok=True)
                    srt_path = os.path.join(audio_path, 'subtitles.srt')
                    with open(srt_path, 'w') as f:
                        f.write(captions)
                    caption_exist = True
                    break
            
            if not caption_exist:
                error(data_path, f"{url}: no {lang} subtitles")
                continue
            
            audio_start = time.time()
            audio = youtube.streams.filter(only_audio = True, file_extension = 'mp4').last()  # Last audio is in the original language
            audio.download(output_path = audio_path, filename = 'audio.mp4')
            mp4_path = os.path.join(audio_path, 'audio.mp4')
            audio_end = time.time()
            
            download_time_ms = (audio_end - audio_start) * 1000
            print(f"Downloaded audio in {download_time_ms:.2f} ms")

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # https://github.com/librosa/librosa/issues/1015
                y, sr = librosa.load(mp4_path, sr = AUDIO_SAMPLING_RATE, mono = True)

            subtitles = pysrt.open(srt_path)

            samples = 0
            total_time = 0

            i = 0
            print("Processing subtitles")
            while i < len(subtitles):
                start = subtitles[i].start
                end = subtitles[i].end
                start_ms = time2ms(start.to_time())
                end_ms = time2ms(end.to_time())
                combined_text = subtitles[i].text

                while (end_ms - start_ms) < 10 * 1000 and i < len(subtitles) - 1:
                    i += 1
                    end = subtitles[i].end
                    end_ms = time2ms(end.to_time())
                    combined_text += " " + subtitles[i].text
                
                subtitle = filter_subtitle(combined_text, alphabet)
                if subtitle and subtitle != "musique" and (end_ms - start_ms) >= 10 * 1000:
                    clip_path = os.path.join(audio_path, str(start) + '-' + str(end))
                    os.mkdir(clip_path)
                    clip_text_path = os.path.join(clip_path,'subtitles.txt')
                    with open(clip_text_path, 'w') as f:
                        f.write(subtitle)

                    start_time = start_ms * sr // 1000
                    end_time = end_ms * sr // 1000
                    clip = y[start_time:end_time + 1]
                    soundfile.write(os.path.join(clip_path, 'audio.wav'), clip, sr)

                    total_time += (end_ms - start_ms) // 1000
                    samples += 1
                
                i += 1

            os.remove(mp4_path)
            os.remove(srt_path)
            success(data_path, f"{url}: OK", samples, total_time)
        
if __name__ == "__main__":
    folders = ["videos", "youtubers", "data"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    main()