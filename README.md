# Graph Editor

Graph Editor is a very simple graph editor which can load and save in the
graphml format (and more to come).

It is written in python, with pyglet and networkx

When the application is started, it should show a simple black background, with the words `press 'h' for help`, and `node`. Like it says, the majority of the instructions can be showed by holding the `h` key, or by consulting the `help.txt` file in the same folder.

## Installation

For now I do not support installation of the program, however you can just
run it from its folder.

## Dependencies

You need to have pyglet and networkx installed in your system.
Try using the following versions:

pyglet==1.5.26

networkx==2.5.1

The editor works for in both python 2.7 and 3+.

## Running

Be sure to be in the base directory (that is the directory which contains
the file graph\_editor.py) and type in the terminal:

    python graph_editor.py

## File IO

When you save with the application, there is no save dialog. Instead, a `graph.graphml` file is created in the same folder as the main `graph_editor.py` file
