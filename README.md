# Course tools

Creating courses, training series, or digital products in general takes time. Packaging a product release, organizing your project, and making sure you got all files before you upload takes a lot of time. I released a few products already and spent a lot of energy updating everything.

GDquest is all about quality over quantity, supporting open education, and open source technologies. There are premium courses that make this possible. Although they're products, they're still community-driven: supporters get to review content as soon as it's ready. Thanks to everyone's feedback we can keep improving content. But this means frequent updates and patching videos and documents. If you've ever released a product you know it takes hours and sometimes more.

This repository is here to help you save time and efforts. It's barebones at the moment but I'll share tools and my product creation workflow as I code them. Everything here is open source thanks to the 765 backers of the [ Godot 3 course ](https://gumroad.com/l/godot-tutorial-make-professional-2d-games).

Got questions? Message me on [Twitter](https://twitter.com/NathanGDquest). For issues use the [GitHub issues](https://github.com/GDquest/course-tools/issues).

## How it works

Packager treats each folder in the main course folder as a chapter, except for ignored folders. Thus each series, chapter or module should be in its own folder. Packager also uses the folder's name to log changes in the changelog.

In each chapter the script walks the folder tree and reproduces it in the dist folder. But it builds and merges files from subfolders along the way.

Take a course folder. You'll likely have a subfolder for each video project, documents, etc. In each folder you may have a source markdown file, a mix of videos and images.

```
source folder:
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
dist folder:
- chapter-1
-- course
--- 1.introduction.html
--- 2.programming-basics.html
--- 3.code-your-first-game.html
--- img/
```

## Ignored folders

Packager skips all folders named "src", "\_src", "temp", "\_temp", "old", "\_old". It's not sensitive to case.
