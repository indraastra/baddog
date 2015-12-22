#!/bin/bash

PHOTO_DIR=photos

mkdir -p $PHOTO_DIR
DATE=$(TZ="America/Los_Angeles" date +"%Y-%m-%d_%H%M%S")
OUTPUT_FILE=$PHOTO_DIR/$DATE.jpg

echo $OUTPUT_FILE
raspistill -n -vf -hf -o $OUTPUT_FILE
