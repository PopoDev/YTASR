import os
import re
import shutil

def correct_subtitles(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file =='subtitles.txt':
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    subtitle = f.read()
                    if subtitle.lower() =='musique':
                        print(f"Removing directory: {root} (subtitles.txt only contains'musique')")
                        # Remove all files and subdirectories within the directory
                        for filename in os.listdir(root):
                            file_path = os.path.join(root, filename)
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        # Remove the directory itself
                        os.rmdir(root)
                    else:
                        new_subtitle = re.sub(r'\s+',' ', subtitle)
                        with open(file_path, 'w') as f:
                            f.write(new_subtitle)

root_dir = './data/fr'
correct_subtitles(root_dir)
print("Subtitles correction complete")