[app]
title = LocalDocumentSearch
project_dir = .
input_file = launcher.py
exec_directory = output
project_file =
icon =

[python]
packages = Nuitka==4.1.1

[qt]
qml_files =
excluded_qml_plugins =
modules = Core,Gui,Widgets
plugins = platforms,styles

[nuitka]
mode = standalone
extra_args = --msvc=14.3 --windows-console-mode=disable --output-filename=LocalDocumentSearch.exe --include-qt-plugins=platforms,styles --noinclude-qt-plugins=iconengines --noinclude-qt-plugins=imageformats --noinclude-qt-plugins=tls --include-windows-runtime-dlls=yes --noinclude-qt-translations --report=compilation-report.xml --assume-yes-for-downloads --jobs=4
