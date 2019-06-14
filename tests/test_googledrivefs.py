from contextlib import suppress
from json import load, loads
from logging import info
from os import environ
from unittest import TestCase
from uuid import uuid4

from google.oauth2.credentials import Credentials

from fs.errors import DirectoryExpected, FileExists, ResourceNotFound
from fs.googledrivefs import GoogleDriveFS
from fs.path import join
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
		fullFS = FullFS()
		testDir = join(_safeDirForTests, str(uuid4()))
		fullFS.makedirs(testDir)
		fullFS.makedir(join(testDir, "parent1"))
		fullFS.makedir(join(testDir, "parent2"))
		fullFS.makedir(join(testDir, "parent3"))
		fullFS.writebytes(join(testDir, "parent1/file"), b"data1")
		fullFS.writebytes(join(testDir, "parent2/file"), b"data2")

		# can't link into a parent where there's already a file there
		with self.assertRaises(FileExists):
			fullFS.add_parent(join(testDir, "parent1/file"), join(testDir, "parent2"))

		# can't add a parent which is a file
		with self.assertRaises(DirectoryExpected):
			fullFS.add_parent(join(testDir, "parent1/file"), join(testDir, "parent2/file"))

		# can't add a parent which doesn't exist
		with self.assertRaises(ResourceNotFound):
			fullFS.add_parent(join(testDir, "parent1/file2"), join(testDir, "parent4"))

		# can't add a parent to a file that doesn't exist
		with self.assertRaises(ResourceNotFound):
			fullFS.add_parent(join(testDir, "parent1/file2"), join(testDir, "parent3"))

		# when linking works, the data is the same
		fullFS.add_parent(join(testDir, "parent1/file"), join(testDir, "parent3"))
		self.assert_bytes(join(testDir, "parent3/file"), b"data1")

		# can't remove a parent from a file that doesn't exist
		with self.assertRaises(ResourceNotFound):
			fullFS.remove_parent(join(testDir, "parent1/file2"))

		# successful remove_parent call removes one file and leaves the other the same
		fullFS.remove_parent(join(testDir, "parent1/file"))
		self.assert_not_exists(join(testDir, "parent1/file"))
		self.assert_bytes(join(testDir, "parent3/file"), "data1")
		fullFS.removetree(testDir)

def test_root(): # pylint: disable=no-self-use
	fullFS = FullFS()
	info(fullFS.listdir("/"))
