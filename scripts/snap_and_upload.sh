#!/bin/bash

echo Capturing...
FILENAME=$(./snap.sh)
echo Uploading $FILENAME
./upload.py $FILENAME
