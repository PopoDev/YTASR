import argparse
import os
import json
import pysrt
import librosa
import soundfile
from pytube import YouTube

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
    return ''.join(c for c in subtitle.lower() if c in alphabet)

def log(data_path, msg):
    with open(os.path.join(data_path, "log.txt"), "a") as f:
        f.write(msg + "\n")

def save_metric(data_path, values):
    try:
        with open(os.path.join(data_path, "metric.json"), "r") as f:
            metric = json.load(f)
            videos = metric["videos"]
            samples = metric["samples"]
            total_time = metric["total_time"]
    except:
        videos = 0
        samples = 0
        total_time = 0

    videos += values['videos']
    samples += values['samples']
    total_time += values["time"]

    with open(os.path.join(data_path, "metric.json"), "w") as f:
        json.dump({"videos": videos, "samples": samples, "total_time": total_time, "avg_time": total_time / samples if samples > 0 else 0}, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lang", help="Language used", default="fr")
    parser.add_argument("-n", "--num_videos", help="Number of videos to download", default=1, type=int)
    args = parser.parse_args()

    lang = args.lang
    num_videos = args.num_videos

    with open(f"alphabet/{lang}.txt", 'r') as f:
        alphabet = set(f.read().replace('\n', ''))

    youtubers = []
    with open(f"youtubers/{lang}.txt", "r") as f:
        for line in f:
            youtubers.append(line.strip())
    
    for youtuber in youtubers:
        info = youtuber.split(':')
        channel=info[0]
        date_after = info[1] if len(info) > 1 else None
        
        videos_path = f"videos/{lang}"
        data_path = f"data/{lang}/{channel}"
        os.makedirs(videos_path, exist_ok=True)
        os.makedirs(data_path, exist_ok=True)

        args = '--flat-playlist --skip-download --extractor-args youtubetab:approximate_date --print "%(upload_date)s:%(id)s"'
        os.system(f"yt-dlp {args} https://www.youtube.com/@{channel}/videos > videos/{lang}/{channel}.txt")

        video_ids = []
        with open(f"videos/{lang}/{channel}.txt", "r") as f:
            for line in f:
                date, id = line.strip().split(':')
                if date_after is None or int(date) >= int(date_after):
                    video_ids.insert(0, id)

        downloaded_videos = len(os.listdir(data_path))
        total_videos = len(video_ids)

        print(f"Currently downloaded videos for {channel}: {downloaded_videos}/{total_videos}")

        if downloaded_videos >= total_videos:
            print(f"Already downloaded all available videos for {channel}")
            continue

        videos = 0
        samples = 0
        total_time = 0
        for video_id in video_ids[downloaded_videos:downloaded_videos+num_videos]:
            url = f"https://www.youtube.com/watch?v={video_id}"

            # Download video
            youtube = YouTube(url)
            print(f"Downloading {url}. Title: {youtube.title}")

            subtitle_lang = SUBTITLE_MAPPING[lang].capitalize()
            date = youtube.publish_date.strftime("%Y%m%d")
            audio_path = os.path.join(data_path, f"{date}-{video_id}")
            os.makedirs(audio_path, exist_ok=True)
            try:
                youtube.bypass_age_gate()
            except Exception as e:
                log(data_path, f"{url}: age restricted, {e}")
                print(f"Age restricted video, skipping, {e}")
                continue

            print(f"Searching for {subtitle_lang} subtitles")

            caption_exist = False
            for captions in youtube.caption_tracks:
                print("Available subtitles:", captions.name)
                if captions.name.startswith(subtitle_lang):
                    captions = captions.generate_srt_captions()
                    srt_path = os.path.join(audio_path, 'subtitles.srt')
                    with open(srt_path, 'w') as f:
                        f.write(captions)
                    caption_exist = True
                    break
            
            if not caption_exist:
                log(data_path, f"{url}: no subtitles")
                print("No subtitles found, skipping")
                continue
            
            audio = youtube.streams.filter(only_audio = True, file_extension = 'mp4').last()  # Last audio is in the original language
            audio.download(output_path = audio_path, filename = 'audio.mp4')
            mp4_path = os.path.join(audio_path, 'audio.mp4')

            y, sr = librosa.load(mp4_path, sr = AUDIO_SAMPLING_RATE, mono = True)
            subtitles = pysrt.open(srt_path)

            i = 0
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

                clip_path = os.path.join(audio_path, str(start) + '-' + str(end))
                os.mkdir(clip_path)
                clip_text_path = os.path.join(clip_path,'subtitles.txt')
                with open(clip_text_path, 'w') as f:
                    f.write(filter_subtitle(combined_text, alphabet))

                start_time = start_ms * sr // 1000
                end_time = end_ms * sr // 1000
                clip = y[start_time:end_time + 1]
                soundfile.write(os.path.join(clip_path, 'audio.wav'), clip, sr)

                total_time += (end_ms - start_ms) // 1000
                samples += 1
                i += 1

            os.remove(mp4_path)
            os.remove(srt_path)

            log(data_path, f"{url}: OK")
            videos += 1
        
        save_metric(data_path, {"videos": videos, "samples": samples, "time": total_time})

        
if __name__ == "__main__":
    folders = ["videos", "youtubers", "data"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    main()