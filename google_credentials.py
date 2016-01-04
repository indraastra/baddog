import json

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
        print("Invalid credentials!")
        if not log_in: return None

        flow = make_oauth_flow()
        authorize_url = flow.step1_get_authorize_url()
        print 'Go to the following link in your browser: ' + authorize_url
        code = raw_input('Enter verification code: ').strip()
        credentials = flow.step2_exchange(code)
        storage.put(credentials)

    return credentials


if __name__ == "__main__":
    credentials = get_credentials(log_in=True)
    if credentials:
        print("Credentials are up-to-date!")

