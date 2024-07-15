import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lang", help="Language used", default="fr")
    args = parser.parse_args()

    lang = args.lang

    youtubers = []
    with open(f"youtubers/{lang}.txt", "r") as f:
        for line in f:
            youtubers.append(line.strip())

    for youtuber in youtubers:
        info = youtuber.split(':')
        channel=info[0]
        date_after = info[1] if len(info) > 1 else None
        
        videos_path = f"videos/{lang}"
        os.makedirs(videos_path, exist_ok=True)

        args = '--flat-playlist --skip-download --extractor-args youtubetab:approximate_date --print "%(upload_date)s:%(id)s"'
        os.system(f"yt-dlp {args} https://www.youtube.com/@{channel}/videos > {videos_path}/{channel}.txt")
        print(f"Downloaded videos for {channel}{' after ' + date_after if date_after else ''}")

        with open(f"{videos_path}/{channel}.txt", "r") as f:
            filter_before = lambda x: x.split(":")[0] > date_after if date_after else True
            videos = list(filter(filter_before, f.readlines()))

        with open(f"{videos_path}/{channel}.txt", "w") as f:
            for video in videos:
                video_id = video.split(':')[1]
                f.write(video_id)
