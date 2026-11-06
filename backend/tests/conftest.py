import pathlib
import sys

# 让 pytest 在 backend/ 目录下可直接 import app.*
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
