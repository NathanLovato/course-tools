"""
Collects, builds and packages all files for the course

Possible improvements:
- add a .packagerignore file with names to ignore. One global next to the script, one at the project's root
- debug log: add an enum of stages, and allow to print messages only for a given list of steps. E.g. only pandoc commands etc.
- debug: allow stopping execution at a given stage
- build and debug: allow to only process a given chapter
"""

import os
import subprocess
import shutil
import stat
import re
import sys
from enum import Enum

# TODO: use enum?
# class FolderTypes(Enum):
#     content = 1
#     exercises = 2
#     static = 3


# Settings

RE_IGNORED_FOLDERS = r'^_?(src|draft|old|.+\.lnk|.git)$'
re.IGNORECASE = True

COURSE_FOLDER = 'course'
EXERCISE_FOLDER = 'exercises'
DEMO_FOLDER = 'demo'

debug = False
debug_processed_chapters = 0
debug_chapters_process_count = 100


# Methods
def get_path_from_shell_args():
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


def copy_file_tree(src, dst, symlinks = False, ignore = None):
    if not os.path.exists(dst):
        os.makedirs(dst)
        shutil.copystat(src, dst)
    lst = os.listdir(src)
    if ignore:
        excl = ignore(src, lst)
        lst = [x for x in lst if x not in excl]
    for item in lst:
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if symlinks and os.path.islink(s):
            if os.path.lexists(d):
                os.remove(d)
            os.symlink(os.readlink(s), d)
            try:
                st = os.lstat(s)
                mode = stat.S_IMODE(st.st_mode)
                os.lchmod(d, mode)
            except:
                pass # lchmod not available
        elif os.path.isdir(s):
            copy_file_tree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


# Script
def get_project_path():
    path = get_path_from_shell_args()
    if not os.path.isdir(path):
        path = os.path.abspath('.')
    if not os.path.isdir(path):
        print('Please provide the script with a folder')
        sys.exit()



# Find modules, dict with the form { name: abspath }
modules = { folder:os.path.join(path, folder) for folder in os.listdir(path) \
            if not re.match(RE_IGNORED_FOLDERS, folder) and os.path.isdir(os.path.join(path,folder)) }
if not modules:
    print('The folder is empty, Packager will now exit')
    sys.exit()
print('{!s} Modules found: {!s}'.format(len(modules.keys()), modules.keys()))


# TODO: Redo with a fixed structure ? it's already getting hard to maintain
def find_course_files(path):
    """
    Finds .md files and corresponding folders named 'img'
    Returns two lists: markdown_files and img_folders
    """
    markdown_files, img_folders = [], [],
    files_to_copy, folders_to_copy = [], []
    for dirpath, dirnames, filenames in os.walk(path):
        # skip ignored folders
        dirnames[:] = [d for d in dirnames if not re.match(RE_IGNORED_FOLDERS, d)]
        current_folder = os.path.split(dirpath)[1]
        if re.match(RE_IGNORED_FOLDERS, current_folder):
            continue

        new_markdown_files = [os.path.join(dirpath, f) for f in filenames if f.endswith('.md')]
        markdown_files.extend(new_markdown_files)
        if new_markdown_files:
            img_folders.extend([os.path.join(dirpath, folder) for folder in dirnames if folder == 'img'])

        files_to_copy.extend([os.path.join(dirpath, f) for f in filenames if not f.endswith('.md')])
        folders_to_copy.extend([os.path.join(dirpath, folder) for folder in filenames \
                                if not re.match(RE_IGNORED_FOLDERS, folder) and not folder == 'img'])

    return markdown_files, img_folders, files_to_copy, folders_to_copy


# Find all markdown files to build and folders to copy to _dist
file_paths = {}
MARKDOWN_FILES, FOLDERS_TO_COPY = 'markdown', 'to_copy'
for module_name in modules.keys():
    file_paths[module_name] = {}
    module_path = modules[module_name]
    for folder in os.listdir(module_path):
        if re.match(RE_IGNORED_FOLDERS, folder):
            continue
        file_paths[module_name][folder] = {}
        md_files, img_folders, files_to_copy, folders_to_copy = find_course_files(os.path.join(module_path, folder))
        file_paths[module_name][folder][MARKDOWN_FILES] = md_files
        file_paths[module_name][folder][FOLDERS_TO_COPY] = img_folders
        # print(files_to_copy)
        # print(folders_to_copy)
        # print('\n')

    print_debug('\n', folder)
    print_debug('\n', file_paths[module_name])
    if debug:
        debug_processed_chapters += 1
        if debug_processed_chapters >= debug_chapters_process_count:
            break


# BUILD AND MOVE FILES WITH PANDOC
# Go down modules, then folders, and in each folder there's MARKDOWN_FILES
folders_to_create = []
dist_folder = os.path.join(path, '_dist')
pandoc_build_commands = []

css_file_name = 'pandoc.css'
for module_name in file_paths.keys():
    module_dist_path = os.path.join(dist_folder, module_name)

    for folder in file_paths[module_name].keys():
        folder_path = os.path.join(module_dist_path, folder)
        folders_to_create.append(folder_path)

        markdown_files = file_paths[module_name][folder][MARKDOWN_FILES]
        for f in markdown_files:
            markdown_folder_path, file_name = os.path.split(f)
            name = os.path.splitext(file_name)[0]
            export_file_name = name + '.html'

            dist_path = os.path.join(folder_path, export_file_name)
            pandoc_build_commands.append(['pandoc', f, '-t', 'html5', '--css', css_file_name, '-o', dist_path])

        to_copy = file_paths[module_name][folder][FOLDERS_TO_COPY]
        for copy_file_path in to_copy:
            copy_file_tree(copy_file_path, os.path.join(module_dist_path, 'course', 'img'))
            print_debug(copy_file_path)

print_debug(pandoc_build_commands[0])

# Create folders
for folder_path in folders_to_create:
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

for command in pandoc_build_commands:
    subprocess.run(command)

# TODO: copy css file once per course folder
# css_file_path = os.path.join(path, css_file_name)
# shutil.copy(css_file_path, folder_path)

# TODO timestamp files
# Get last modified time
# try:
#     mtime = os.path.getmtime(file_name)
# except OSError:
#     mtime = 0
# last_modified_date = datetime.fromtimestamp(mtime)


# TODO: For folders in _dist, if folder changed, auto ZIP
# def has_changed_since_last_build(file_path):

# TODO: changelog
# Store build date
# Print all changes to a file -> changelog
# Separate changed and new things
