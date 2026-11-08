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
qml_files = local_document_search_desktop/qml/Main.qml
excluded_qml_plugins =
modules = Core,Gui,Qml,Quick,QuickControls2
plugins = platforms,qml

[nuitka]
mode = standalone
extra_args = --msvc=14.3 --windows-console-mode=disable --output-filename=LocalDocumentSearch.exe --include-qt-plugins=platforms,qml --noinclude-qt-plugins=tls --include-windows-runtime-dlls=yes --report=compilation-report.xml --assume-yes-for-downloads --jobs=4
