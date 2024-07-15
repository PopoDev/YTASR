import os

def verify_subtitles(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.txt') and file.startswith('subtitles'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"Error: Empty subtitles file {file_path}")
                        return False
                    print(f"OK {file_path}")
                    timestamp = file_path.split('/')[-2]
                    start, end = timestamp.split('-')
                    start_h, start_m, start_s = start.split(':')
                    end_h, end_m, end_s = end.split(':')
                    start_time = int(start_h) * 3600 + int(start_m) * 60 + int(start_s.split(',')[0])
                    end_time = int(end_h) * 3600 + int(end_m) * 60 + int(end_s.split(',')[0])
                    duration = end_time - start_time
                    if duration < 10:
                        print(f"Error: Timestamp duration {duration} seconds is less than 10 seconds in file {file_path}")
                        return False
    return True

root_dir = './data/fr'
if verify_subtitles(root_dir):
    print("All subtitles files are valid")
else:
    print("Error: One or more subtitles files are invalid")