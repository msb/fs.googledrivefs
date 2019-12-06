__all__ = ["GoogleDriveFSOpener"]

import os
from fs.opener import Opener
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials # pylint: disable=wrong-import-order

from .googledrivefs import GoogleDriveFS

class GoogleDriveFSOpener(Opener): # pylint: disable=too-few-public-methods
	protocols = ['googledrive']

	def open_fs(self, fs_url, parse_result, writeable, create, cwd): # pylint: disable=too-many-arguments
		_, _, directory = parse_result.resource.partition('/')

		if 'service_account_credentials_file' in parse_result.params:
			# support for service account credentials as file
			credentials = service_account.Credentials.from_service_account_file(
				parse_result.params['service_account_credentials_file'],
				scopes=['https://www.googleapis.com/auth/drive']
			)
		elif 'GDRIVE_SERVICE_ACCOUNT_CLIENT_EMAIL' in os.environ:
			# support for service account credentials as variables
			service_account_info = {
				"client_email": os.environ['GDRIVE_SERVICE_ACCOUNT_CLIENT_EMAIL'],
				"token_uri": os.environ['GDRIVE_SERVICE_ACCOUNT_TOKEN_URI'],
				# FIXME https://github.com/docker/compose/issues/3607
				"private_key": os.environ['GDRIVE_SERVICE_ACCOUNT_PRIVATE_KEY'].replace('\\n', '\n'),
			}
			credentials = service_account.Credentials.from_service_account_info(
				service_account_info,
				scopes=['https://www.googleapis.com/auth/drive']
			)
		else:
			# basic credentials
			credentials = Credentials(parse_result.params.get("access_token"),
				refresh_token=parse_result.params.get("refresh_token", None),
				token_uri="https://www.googleapis.com/oauth2/v4/token",
				client_id=parse_result.params.get("client_id", None),
				client_secret=parse_result.params.get("client_secret", None))

		fs = GoogleDriveFS(credentials)

		if directory:
			return fs.opendir(directory)
		return fs
