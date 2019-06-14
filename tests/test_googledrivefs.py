from contextlib import suppress
from json import load, loads
from logging import info
from os import environ
from unittest import TestCase
from uuid import uuid4

from google.oauth2.credentials import Credentials

from fs.errors import DirectoryExpected, FileExists, ResourceNotFound
from fs.googledrivefs import GoogleDriveFS
from fs.test import FSTestCases

_safeDirForTests = "/test-googledrivefs"

def FullFS():
	if "GOOGLEDRIVEFS_TEST_TOKEN_READ_ONLY" in environ:
		credentialsDict = loads(environ["GOOGLEDRIVEFS_TEST_TOKEN_READ_ONLY"])
	else:
		with open(environ["GOOGLEDRIVEFS_TEST_CREDENTIALS_PATH"]) as f:
			credentialsDict = load(f)
	credentials = Credentials(credentialsDict["access_token"],
		refresh_token=credentialsDict["refresh_token"],
		token_uri="https://www.googleapis.com/oauth2/v4/token",
		client_id=environ["GOOGLEDRIVEFS_TEST_CLIENT_ID"],
		client_secret=environ["GOOGLEDRIVEFS_TEST_CLIENT_SECRET"])
	return GoogleDriveFS(credentials)

class TestGoogleDriveFS(FSTestCases, TestCase):

	@classmethod
	def setUpClass(cls):
		cls._perRunDir = str(uuid4())
		info(f"Tests are running in {cls._perRunDir}")
		cls.perRunFS = FullFS().opendir(_safeDirForTests).makedir(cls._perRunDir)

	@classmethod
	def tearDownClass(cls):
		with suppress(Exception):
			FullFS().opendir(_safeDirForTests).removetree(cls._perRunDir)

	def make_fs(self):
		self._fullFS = self.__class__.perRunFS
		self._thisTestDir = str(uuid4())
		info(f"Tests are running in {self._thisTestDir}")
		return self.__class__.perRunFS.makedir(self._thisTestDir)

	def destroy_fs(self, fs):
		self.__class__.perRunFS.removetree(self._thisTestDir)

	def test_directory_paging(self):
		# default page size is 100
		fileCount = 101
		for i in range(fileCount):
			self.fs.writebytes(str(i), b"x")
		files = self.fs.listdir("/")
		self.assertEqual(len(files), fileCount)

	def test_add_remove_parents(self):
		parent1 = self.fs.makedir("parent1")
		parent2 = self.fs.makedir("parent2")
		parent3 = self.fs.makedir("parent3")
		self.fs.writebytes("parent1/file", b"data1")
		self.fs.writebytes("parent2/file", b"data2")
		with self.assertRaises(FileExists):
			self.fs.add_parent("parent1/file", "parent2")

		with self.assertRaises(DirectoryExpected):
			self.fs.add_parent("parent1/file", "parent2/file")

		with self.assertRaises(ResourceNotFound):
			self.add_parent("parent1/file2", "parent3")

		self.fs.add_parent("parent1/file", "parent3")
		self.assert_bytes("parent3/file", b"data")

		with self.assertRaises(ResourceNotFound):
			self.fs.remove_parent("parent1/file2")

		self.fs.remove_parent("parent1/file")
		self.assert_not_exists("parent1/file")
		self.assert_bytes("parent3/file", "data1")

def testRoot(): # pylint: disable=no-self-use
	fullFS = FullFS()
	info(fullFS.listdir("/"))
