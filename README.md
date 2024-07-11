# YTASR Dataset

## Introduction

This dataset is a collection of YouTube videos audio with their subtitles.

## Getting Started

Clone the repository

```bash
git clone https://github.com/PopoDev/YTASR.git
cd YTASR
```
Create a new environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies in a new environment
```bash
pip install -r requirements.txt
```

Run the main script to start downloading videos by providing Youtubers' channel IDs in the `youtubers` folder.

```bash
python main.py
```


## Important

### Changes in Pytube 15.0.0

#### captions.py
KeyError 'start' when getting captions from a video
https://github.com/pytube/pytube/issues/1085#issuecomment-950327958

```python
def xml_caption_to_srt(self, xml_captions: str) -> str:
    """Convert xml caption tracks to "SubRip Subtitle (srt)".

    :param str xml_captions:
    XML formatted caption tracks.
    """
    segments = []
    root = ElementTree.fromstring(xml_captions)
    i=0
    for child in list(root.iter("body"))[0]:
        if child.tag == 'p':
            caption = ''
            if len(list(child))==0:
                # instead of 'continue'
                caption = child.text
            for s in list(child):
                if s.tag == 's':
                    caption += ' ' + s.text
            caption = unescape(caption.replace("\n", " ").replace("  ", " "),)
            try:
                duration = float(child.attrib["d"])/1000.0
            except KeyError:
                duration = 0.0
            start = float(child.attrib["t"])/1000.0
            end = start + duration
            sequence_number = i + 1  # convert from 0-indexed to 1.
            line = "{seq}\n{start} --> {end}\n{text}\n".format(
                seq=sequence_number,
                start=self.float_to_srt_time_format(start),
                end=self.float_to_srt_time_format(end),
                text=caption,
            )
            segments.append(line)
            i += 1
    return "\n".join(segments).strip()
```

#### cipher.py

RegexMatchError: get_throttling_function_name: could not find match for multiple
https://github.com/pytube/pytube/issues/1954#issuecomment-2218287594

```python
function_patterns = [
    # https://github.com/ytdl-org/youtube-dl/issues/29326#issuecomment-865985377
    # https://github.com/yt-dlp/yt-dlp/commit/48416bc4a8f1d5ff07d5977659cb8ece7640dcd8
    # var Bpa = [iha];
    # ...
    # a.C && (b = a.get("n")) && (b = Bpa[0](b), a.set("n", b),
    # Bpa.length || iha("")) }};
    # In the above case, `iha` is the relevant function name
    r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&.*?\|\|\s*([a-z]+)',
    r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',
    r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])\([a-z]\)',
]
```
