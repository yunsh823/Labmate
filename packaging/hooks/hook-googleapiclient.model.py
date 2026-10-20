# Overrides the stock hook, which ships all ~600 Google API descriptions (~100 MB).
# The app only needs Calendar's, which build.py adds explicitly.
from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata("google_api_python_client")
