 = New-Object -ComObject WScript.Shell  
 = 'H:\بروجكت برنامج OCR\dist\Portable_SmartDocConverter\Smart Document Converter.lnk'  
 = .CreateShortcut()  
.TargetPath = 'H:\بروجكت برنامج OCR\dist\Portable_SmartDocConverter\Run_Program.bat'  
.WorkingDirectory = 'H:\بروجكت برنامج OCR\dist\Portable_SmartDocConverter'  
.IconLocation = 'H:\بروجكت برنامج OCR\dist\Portable_SmartDocConverter\app\assets\icon.ico'  
.Save()  
