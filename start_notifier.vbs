Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script lives
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Run pythonw (no console) with notifier_bg.py
WshShell.Run "pythonw """ & scriptDir & "\notifier_bg.py""", 0, False
