import httplib2
import json
import logging
import os

import apiclient.discovery
import apiclient.http

from oauth2client import client
from oauth2client import file
from oauth2client import tools

import config


def make_oauth_flow():
    # Perform OAuth2.0 authorization flow.
    # Name of a file containing the OAuth 2.0 information for this
    # application, including client_id and client_secret, which are found
    # on the API Access tab on the Google APIs
    # Console <http://code.google.com/apis/console>.
    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(config.CLIENT_SECRETS,
            scope=config.OAUTH2_SCOPE,
            message=tools.message_if_missing(config.CLIENT_SECRETS))
    flow.redirect_uri = client.OOB_CALLBACK_URN
    return flow


def get_credentials(log_in=False):
    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native 
    # client flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storage = file.Storage(config.CLIENT_CREDENTIALS)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        logging.warning('Invalid credentials!')
        if not log_in: return None

        flow = make_oauth_flow()
        authorize_url = flow.step1_get_authorize_url()
        print('Go to the following link in your browser: ' + authorize_url)
        code = raw_input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code)
        storage.put(credentials)

    return credentials


def drive_getdir(folder_name):
    folder_query = config.BASE_QUERY % folder_name
    folder_search = drive_service.files().list(q=folder_query, maxResults=1).execute()
    folder_search = folder_search['items']
    if len(folder_search) > 0:
        return folder_search[0]['id']


def drive_mkdir(folder_name, parent=None):
    folder_id = drive_getdir(folder_name)
    if folder_id:
        # Found the folder.
        logging.debug('Folder found: {0}'.format(folder_id))
    else:
        # Didn't find the folder, so we need to create it.
        new_folder = drive_service.files().insert(
            body={
                'title': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [{'id': parent}] if parent else None
            }
        ).execute()
        folder_id = new_folder['id']
        logging.debug('Folder created: {0}'.format(folder_id))
    return folder_id


def upload_photo(path, folder_id):
    photo = os.path.join(os.path.abspath(config.PHOTO_DIR), os.path.basename(path))
    if not os.path.exists(photo): return None

    # Insert a file. Files are comprised of contents and metadata.
    # MediaFileUpload abstracts uploading file contents from a file on disk.
    media_body = apiclient.http.MediaFileUpload(
        photo,
        mimetype=config.MIMETYPE,
        resumable=True
    )
    # The body contains the metadata for the file.
    body = {
      'title': os.path.basename(photo),
      'parents': [{'id': folder_id}]
    }

    new_file = drive_service.files().insert(body=body, media_body=media_body).execute()
    logging.debug('Uploaded file {0}!'.format(new_file['id']))

    return new_file['id']


credentials = get_credentials(log_in=False)
http = credentials.authorize(http = httplib2.Http())
drive_service = apiclient.discovery.build('drive', 'v2', http=http)


if __name__ == '__main__':
    credentials = get_credentials(log_in=True)
    if credentials:
        print('Credentials are up-to-date!')
    upload_photo('test.jpg')

