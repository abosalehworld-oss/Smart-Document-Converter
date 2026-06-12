# models directory - EasyOCR model files go here
# These files are NOT committed to git (see .gitignore)
# They are downloaded automatically on first run via setup.bat

# After running setup.bat, this folder will contain:
# - arabic.pth       (Arabic recognition model ~120MB)
# - english.pth      (English recognition model ~50MB)
# - craft_mlt_25k.pth (Text detection model ~80MB)

# To pre-download models for offline deployment:
# Run setup.bat ONCE on a machine with internet
# Then copy the ENTIRE project folder (including venv/ and models/) to the offline machine
