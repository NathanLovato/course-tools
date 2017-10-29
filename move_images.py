"""
Find and move images in *.md files from ./ to ./img. Renames the image paths in the markdown files too.
Either works on .md files you pass as arguments or finds them in the directory and subdirectories
"""

import os
import glob
import fileinput
import re
import sys


def get_shell_paths():
    if len( sys.argv ) == 1:
        return
    shell_args = sys.argv[1:]
    path_list = [os.path.abspath(path) for path in shell_args if os.path.exists(path)]
    return path_list

path_list = get_shell_paths()
if not path_list:
    path_list.append(os.path.abspath('.'))

markdown_files = []
for path in path_list:
    if os.path.isdir(path):
        wildcard = os.path.join(path, '*.md')
        markdown_files.append(glob.glob(wildcard))
    elif path.lower().endswith('.md'):
        markdown_files.append(path)
if not markdown_files:
    print("No markdown files found, stopping the script")
    sys.exit()


# Regex replace ![](foo.png) with ![](img/foo.png) and list img files to move
RE_IMAGE = r'^\!\[(.*)\]\((?!img/)(.+)\)'
image_files_to_move = []
for f in markdown_files:
    folder, _ = os.path.split(f)
    for line in fileinput.input(files=(f), inplace=1, backup='.bak'):
        match = re.match(RE_IMAGE, line)
        if match:
            image_files_to_move.append(folder, match.group(2))
            line = match.expand(r'![\1](img/\2)')
        print(line)


# Move image files
for f in image_files_to_move:
    folder, file_name = os.path.split(f)
    image_folder = os.path.join(folder, 'img')
    if not os.path.exists(image_folder):
        os.mkdir(image_folder)
    os.rename(f, os.path.join(image_folder, file_name))
