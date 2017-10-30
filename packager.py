"""
Collects, builds and packages all files for the course

Architecture
Each folder in the main course folder is a chapter, except for ignored folders
Each series, chapter or module should be in its own folder. Packager uses the folder's name to log changes in the changelog

In each chapter the script walks the folder tree and reproduces it in the dist folder. But it builds and merges subfolders along the way.

Take a course folder. You'll likely have a subfolder for each video project, documents, etc. In each folder you may have a source markdown file, a mix of videos and images.

```
- chapter-1/
-- course/
--- 1.introduction/
---- intro.md
---- img/
--- 2.programming-basics/
---- programming-basics.md
---- img/
--- 3.code-your-first-game/
```

Packager builds them so they stay organized and are convenient for the students to read:

```
- chapter-1
-- course
--- 1.introduction.html
--- 2.programming-basics.html
--- 3.code-your-first-game.html
--- img/
```

Ignored folders
Packager skips all folders named "src", "_src", "temp", "_temp", "old", "_old". It's case insensitive


Possible improvements:
- add a .packagerignore file with names to ignore. One global next to the script, one at the project's root
"""

import os
import subprocess
import shutil
import glob
import re
import sys


# Settings
RE_IGNORED_FOLDERS = r'^_?(src|temp|old|dist|template)$'
re.IGNORECASE = True

COURSE_FOLDER = 'course'
EXERCISE_FOLDER = 'exercises'
DEMO_FOLDER = 'demo'

debug = True


# Methods
def get_shell_args():
    """
    Returns the course folder path to package
    """
    if len( sys.argv ) == 1:
        return
    path = os.path.abspath(sys.argv[1])
    return path

def print_debug(*args):
    if not debug:
        return
    for arg in args:
        print(arg)


# Script
path = get_shell_args()
if not os.path.isdir(path):
    path = os.path.abspath('.')
if not os.path.isdir(path):
    print('Please provide the script with a folder')
    sys.exit()

css_file_name = 'pandoc.css'
css_file_path = os.path.join(path, css_file_name)
# Find modules, dict with the form { name: abspath }
modules = { folder:os.path.join(path, folder) for folder in os.listdir(path) \
            if not re.match(RE_IGNORED_FOLDERS, folder) and os.path.isdir(os.path.join(path,folder)) }
if not modules:
    print('The folder is empty, Packager will now exit')
    sys.exit()
print('{!s} Modules found: {!s}'.format(len(modules.keys()), modules.keys()))


file_paths = {}
COURSE, TO_COPY = 'course', 'copy'
for module_name in modules.keys():
    file_paths[module_name]  = {
        COURSE: [],
        TO_COPY: []
    }
    course_folder_path = os.path.join(modules[module_name], COURSE_FOLDER)
    exercise_folder_path = os.path.join(modules[module_name], EXERCISE_FOLDER)
    if os.path.exists(course_folder_path):
        glob_pattern = os.path.join(course_folder_path, '**/*.md')
        file_paths[module_name][COURSE].extend(glob.glob(glob_pattern))
    if os.path.exists(exercise_folder_path):
        glob_pattern = os.path.join(exercise_folder_path, '**/*.md')
        file_paths[module_name][COURSE].extend(glob.glob(glob_pattern))
    print_debug('\n', course_folder_path, exercise_folder_path)
    print_debug('\n', file_paths[module_name])



folders_to_create = []
dist_folder = os.path.join(path, '_dist')
# Prepare build and move commands
pandoc_build_commands = []
for module_name in modules.keys():
    markdown_files = file_paths[module_name][COURSE]
    if not markdown_files:
        continue

    module_dist_path = os.path.join(dist_folder, module_name)
    course_folder_path = os.path.join(module_dist_path, COURSE)
    folders_to_create.append(course_folder_path)

    for f in markdown_files:
        folder_path, file_name = os.path.split(f)
        name = os.path.splitext(file_name)[0]
        export_file_name = name + '.html'
        dist_path = os.path.join(course_folder_path, export_file_name)
        pandoc_build_commands.append(['pandoc', f, '-t', 'html5', '--css', css_file_name, '-o', dist_path])
print_debug(pandoc_build_commands[0])

# Create folders
for folder_path in folders_to_create:
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    shutil.copy(css_file_path, folder_path)

for command in pandoc_build_commands:
    subprocess.run(command)



# use os.path.split() on filepaths to find if their parent folder is a given folder or not?

# def find_in_folder_tree(extensions = []):
#     """
#     returns a dictionary of files:
#     """

# course/ -> videos and course pdfs
# exercises/01 -> contains pdf exercise + companion files (e.g. godot start and end)

# Output all to _dist folder
# Build html to original folder but pdf to _dist
# copy godot projects and videos

# USE AND STORE TIMESTAMPS!
# Get last modified time
# try:
#     mtime = os.path.getmtime(file_name)
# except OSError:
#     mtime = 0
# last_modified_date = datetime.fromtimestamp(mtime)

# pandoc build htmls with the course css
# build pdfs from html

# For folders in _dist, if folder changed, auto ZIP


# def has_changed_since_last_build(file_path):


# Store build date
# Print all changes to a file -> changelog
# Separate changed and new things
