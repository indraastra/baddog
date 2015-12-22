#!/usr/bin/python

import argparse
import json
import os
import pprint
import sys

import httplib2
import apiclient.discovery
import apiclient.http
from oauth2client import client
from oauth2client import file
from oauth2client import tools

import config

FILE_NAME = sys.argv[1]
FOLDER_QUERY = "mimeType = 'application/vnd.google-apps.folder' and title = '%s'" % config.FOLDER_NAME

parser = argparse.ArgumentParser(parents=[tools.argparser])
flags = parser.parse_args(sys.argv[2:])

# Perform OAuth2.0 authorization flow.
# Name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>.
# Set up a Flow object to be used if we need to authenticate.
flow = client.flow_from_clientsecrets(config.CLIENT_SECRETS, scope=config.OAUTH2_SCOPE,
    message=tools.message_if_missing(config.CLIENT_SECRETS))
flow.redirect_uri = client.OOB_CALLBACK_URN

# Prepare credentials, and authorize HTTP object with them.
# If the credentials don't exist or are invalid run through the native client
# flow. The Storage object will ensure that if successful the good
# credentials will get written back to a file.
storage = file.Storage(config.CLIENT_CREDENTIALS)
credentials = storage.get()
if credentials is None or credentials.invalid:
    print("Invalid credentials!")
    authorize_url = flow.step1_get_authorize_url()
    print 'Go to the following link in your browser: ' + authorize_url
    code = raw_input('Enter verification code: ').strip()
    credentials = flow.step2_exchange(code)
    storage.put(credentials)
http = credentials.authorize(http = httplib2.Http())
drive_service = apiclient.discovery.build('drive', 'v2', http=http)

# Create the directory structure if necessary.
folder_search = drive_service.files().list(q=FOLDER_QUERY, maxResults=1).execute()
folder_search = folder_search["items"]

if len(folder_search) == 0:
    new_folder = drive_service.files().insert(body={'title': config.FOLDER_NAME}).execute()
    folder_id = new_folder["id"]
    print("Folder created: ", folder_id)
else:
    folder_id = folder_search[0]["id"]
    print("Folder found: ", folder_id)

# Insert a file. Files are comprised of contents and metadata.
# MediaFileUpload abstracts uploading file contents from a file on disk.
media_body = apiclient.http.MediaFileUpload(
    FILE_NAME,
    mimetype=config.MIMETYPE,
    resumable=True
)
# The body contains the metadata for the file.
body = {
  'title': FILE_NAME.split("/")[-1],
  'parents': [{'id': folder_id}]
}

new_file = drive_service.files().insert(body=body, media_body=media_body).execute()
print("Uploaded file!", new_file["id"])
