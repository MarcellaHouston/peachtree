#!/bin/bash
python3 create.py
sudo systemctl restart peachtree
python3 seed.py
rm -r chroma_db

