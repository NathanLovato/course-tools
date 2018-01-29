"""
Collects, builds and packages all files for the course

Possible improvements:
- debug log: add an enum of stages, and allow to print messages only for a given list of steps. E.g. only pandoc commands etc.
- debug: allow stopping execution at a given stage
- build and debug: allow to only process a given chapter
"""

import os
import subprocess
import re
import sys
import json
from enum import Enum
from utils.copy_file_tree import copy_file_tree

# TODO: Move settings to JSON
# TODO: Externalize utils (see https://github.com/GDquest/Blender-power-sequencer/)
# TODO: Store file timestamps in JSON objects
# TODO: Changelog

# Settings
RE_IGNORED_FOLDERS = r'^_?(src|draft|old|.+\.lnk|.git)$'
re.IGNORECASE = True

COURSE_FOLDER = 'course'
EXERCISE_FOLDER = 'exercises'
DEMO_FOLDER = 'demo'

settings = {
    "case_ignore": True,
    "folders": {
        "content": "content",
        "exercises": "exercises",
        "static": "static"
    }
}

info = {
    "processed_chapters": 0,
    "current_step": 0,
}

debug = True


def print_debug(*args):
    if not debug:
        return
    for arg in args:
        print(arg)


def get_project_path():
    """
    Returns the course folder path to package
    """
    if len(sys.argv) == 1:
        return
    path = os.path.abspath(sys.argv[1])
    if not os.path.isdir(path):
        path = os.path.abspath('.')
    if not os.path.isdir(path):
        print('Please provide the script with a folder')
        sys.exit()
    return path


class Folders(Enum):
    """Folder names to use as paths"""
    CONTENT = settings['folders']['content']
    EXERCISES = settings['folders']['exercises']
    STATIC = settings['folders']['static']


class FolderProcessor:
    """Finds files and folder paths to feed the CourseDatabase"""
    def __init__(self, project_folder):
        self.project_folder = project_folder
        self.project_chapters = [f for f in os.listdir(self.project_folder) if not re.match(RE_IGNORED_FOLDERS, f)]

    def find_project_files(self):
        """Finds everything"""
        project_files = []
        for chapter_name in self.project_chapters:
            data = {}
            chapter_path = os.path.join(self.project_folder, chapter_name)

            data['content'] = self._find_content(os.path.join(chapter_path, Folders.CONTENT.value), True)
            data['exercises'] = self._find_content(os.path.join(chapter_path, Folders.EXERCISES.value))
            static_path = os.path.join(chapter_path, Folders.STATIC.value)
            if os.path.isdir(static_path):
                data['static'] = Folders.STATIC.value

            chapter_data = {chapter_name: data}
            project_files.append(chapter_data)
        return project_files

    def _find_content(self, folder_path, find_static_files=False):
        """
        Finds all markdown files to build and copy
        """
        found = {
            'markdown': [],
            'img': [],
            'static': []
        }
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if not re.match(RE_IGNORED_FOLDERS, d)]

            folder_relpath = os.path.relpath(root, start=folder_path)
            found_markdown = [os.path.join(folder_relpath, f) for f in files if f.endswith('.md')]

            #TODO: refactor to have file: {timestamp: ..., abspath?}
            found['img'].extend([os.path.join(folder_relpath, folder) for folder in dirs if folder == 'img'])
            found['markdown'].extend(found_markdown)
            found['static'].extend([os.path.join(folder_relpath, f) for f in dirs if f != 'img'])

            if find_static_files:
                found['static'].extend([os.path.join(folder_relpath, f) for f in files if not f.endswith('.md')])
        return found

    def _get_timestamp(file_path):
        try:
            timestamp = os.path.getmtime(file_path)
        except OSError:
            timestamp = 0.0
            print("Couldn't get timestamp for %s".format(file_path))
        return timestamp


class CourseDatabase:
    def __init__(self):
        self.chapters = []
        self.changes = []

    def update(self, files_dict):
        """
        Rebuild the database from a files dictionary
        Use FolderProcessor to find files and get the source files_dict
        Stamps the files and stores their paths
        Stores it in self.data
        """

        # take the FolderProcessor's result and compare it to the current DB

    def write_changelog():
        pass

    def load_from(file_path):
        """Loads the database from a JSON file"""
        with open(file_path) as data:
            self.chapters = json.loads(data.read())


project_path = get_project_path()
processor = FolderProcessor(project_path)
files = processor.find_project_files()
data_json = json.dumps(files, indent=2)
print(data_json)
sys.exit()

def build():
    # BUILD AND MOVE FILES WITH PANDOC
    # Go down chapters, then folders, and in each folder there's MARKDOWN_FILES
    folders_to_create = []
    dist_folder = os.path.join(project_path, '_dist')
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
                pandoc_build_commands.append([
                    'pandoc', f, '-t', 'html5', '--css', css_file_name, '-o',
                    dist_path
                ])

            to_copy = file_paths[module_name][folder][FOLDERS_TO_COPY]
            for copy_file_path in to_copy:
                copy_file_tree(copy_file_path,
                               os.path.join(module_dist_path, 'course', 'img'))
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
