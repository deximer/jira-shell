import unittest
import json
import transaction
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from ..dao import Jira, LocalDB, connection

class DBTest(unittest.TestCase):
    def setUp(self):
        self.db = LocalDB(connection)

    def tearDown(self):
        del self.db

    def testObjectCreation(self):
        self.assertTrue(self.db is not None)

    def testCwdContents(self):
        self.db.data.root()['1.0'] = 'Release 1'
        self.db.data.root()['2.0'] = 'Release 2'
        self.assertEqual(self.db.cwd_contents(), ('1.0', '2.0'))

    def testGetByPath(self):
        self.db.data.root()['1.0'] = {}
        self.assertEqual(self.db.get_by_path('/1.0'), {})

    def testGetByPathNested(self):
        self.db.data.root()['1.0'] = {}
        self.db.data.root()['1.0']['NG-2'] = 'Issue 2'
        self.assertEqual(self.db.get_by_path('/1.0/NG-2'), 'Issue 2')

    def testGetByPathNestedByList(self):
        self.db.data.root()['1.0'] = {}
        self.db.data.root()['1.0']['NG-2'] = 'Issue 2'
        self.assertEqual(self.db.get_by_path(['', '1.0', 'NG-2']), 'Issue 2')

    def testGetByPathRelative(self):
        self.db.data.root()['1.0'] = {}
        self.db.data.root()['1.0']['NG-1'] = 'Issue 1'
        self.db.cwd = ['', '1.0']
        self.assertEqual(self.db.get_by_path('NG-1'), 'Issue 1')


class JiraTest(unittest.TestCase):
    ''' Unit tests for the Jira DAO class
    '''
    SERVER = 'jira.cengage.com'
    AUTH = 'user:pass'

    def setUp(self):
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        self.jira = Jira('jira.cengage.com', 'user:pass')
        self.jira.call_rest = mock_call_rest
        self.jira.request_page = mock_request_page

    def tearDown(self):
        import transaction
        transaction.abort()

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
