import unittest
import json
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from ..dao import Jira, LocalDB

class DBTest(unittest.TestCase):
    def testObjectCreation(self):
        obj = LocalDB()
        self.assertTrue(obj is not None)

class JiraTest(unittest.TestCase):
    ''' Unit tests for the Jira DAO class
    '''
    SERVER = 'jira.cengage.com'
    AUTH = 'user:pass'

    def setUp(self):
        self.fs = FileStorage('testing_cache.fs')
        self.db = DB(self.fs)
        self.connection = self.db.open()
        self.jira = Jira('jira.cengage.com', 'user:pass',self.connection)
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        self.jira.call_rest = mock_call_rest
        self.jira.request_page = mock_request_page

    def tearDown(self):
        self.connection.close()
        self.db.close()
        self.fs.close()

    def testObjectCreation(self):
        ''' Verify we can create a Story object
        '''
        self.assertTrue(self.jira is not None)

    def testInitialization(self):
        self.assertEqual(self.jira.server, self.SERVER)
        self.assertEqual(self.jira.auth, self.AUTH)
        self.assertEqual(self.jira.cwd, ['/'])

    def testFormatRequest(self):
        self.assertEqual(self.jira.format_request('test/path.html'),
            'http://user:pass@jira.cengage.com/test/path.html')

    def testAllProjects(self):
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/projects.html').read()
        self.jira.request_page = mock_request_page
        projects = self.jira.all_projects()
        keys = ['NG', 'MTQA', 'MTA']
        count = 0
        for project in projects.data:
            self.assertEqual(project.key, keys[count])
            count += 1

    def testGetRelease(self):
        release = self.jira.get_release()
        self.assertEqual(release.data[0].key, 'NG-12459')

    def testGetReleaseKeys(self):
        keys = self.jira.get_release_keys()
        self.assertEqual(keys[0], 'NG-12459')

    def testGetStory(self):
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        self.jira.call_rest = mock_call_rest
        story = self.jira.get_story('NG-12345')
        self.assertEqual(story.key, 'NG-12345')
        import datetime
        import time
        creation_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime('2012-12-21T15:05:23.000-0500'[:23]
            , '%Y-%m-%dT%H:%M:%S.%f')))
        self.assertEqual(story.created, creation_date)
        self.assertEqual(story.assignee['displayName'], 'Abdul Habra')

    def testGetChangeLog(self):
        data = self.jira.get_changelog('NG-13332')
        self.assertEqual(data['key'], 'NG-13332')
