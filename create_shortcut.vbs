Set oWS = WScript.CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetAbsolutePathName(".")
portableDir = currentDir & "\dist\Portable_SmartDocConverter"
sLinkFile = portableDir & "\Smart Document Converter.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = portableDir & "\Run_Program.bat"
oLink.WorkingDirectory = portableDir
oLink.IconLocation = portableDir & "\app\assets\icon.ico"
oLink.Save
