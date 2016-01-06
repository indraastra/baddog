import os

# OAuth 2.0 scope that will be authorized.
OAUTH2_SCOPE = 'https://www.googleapis.com/auth/drive'

# Location of the client secrets.
CLIENT_SECRETS = os.path.abspath('client_secret.json')

# Location of the last used credentials.
CLIENT_CREDENTIALS = os.path.abspath('credentials.dat')

# Path to the file to upload.
FOLDER_NAME = MUST_SET_THIS
FOLDER_QUERY = "mimeType = 'application/vnd.google-apps.folder' and title = '%s'" % FOLDER_NAME

# Metadata about the file.
MIMETYPE = 'image/jpeg'

###########
DETECTOR_IN_PIN = 23
LED_OUT_PIN = 6

###########
PHOTO_DIR = os.path.abspath('photos')
BURST_PHOTOS = 4
BURST_DELAY_S = 5
