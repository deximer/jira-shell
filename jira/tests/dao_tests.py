import unittest
import json
import transaction
import datetime
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from ..dao import Jira, LocalDB, connection
from ..model import Release, Story

class DBTest(unittest.TestCase):
    def setUp(self):
        self.db = LocalDB(connection)

    def tearDown(self):
        transaction.abort()
        for key in self.db.data.root().keys():
            transaction.begin()
            del self.db.data.root()[key]
            transaction.commit()
        del self.db

    def testObjectCreation(self):
        self.assertTrue(self.db is not None)

    def testCwdContents(self):
        self.db.data.root()['1.0'] = 'Release 1'
        self.db.data.root()['2.0'] = 'Release 2'
        self.assertEqual(self.db.cwd_contents(), ('1.0', '2.0'))

    def testCwdContentsNested(self):
        self.db.data.root()['1.0'] = {}
        self.db.data.root()['1.0']['NG-1'] = 'Issue 1'
        self.db.cwd = ['/', '1.0']
        self.assertEqual(self.db.cwd_contents(), ('NG-1',))

    def testGetByPath(self):
        self.db.data.root()['1.0'] = {}
        self.assertEqual(self.db.get_by_path('/1.0'), {})

    def testGetByPathNested(self):
        self.db.data.root()['1.0'] = {}
        self.db.data.root()['1.0']['NG-2'] = 'Issue 2'
        self.assertEqual(self.db.get_by_path('/1.0/NG-2'), 'Issue 2')

    def testGetByPathNestedByList(self):
        self.db.data.root()['1.0'] = {}
        self.db.data.root()['1.0']['NG-1'] = 'NG-1'
        self.assertEqual(self.db.get_by_path(['/', '1.0', 'NG-1']), 'NG-1')

    def testGetByPathRelative(self):
        self.db.data.root()['1.0'] = {}
        self.db.data.root()['1.0']['NG-1'] = 'Issue 1'
        self.db.cwd = ['/', '1.0']
        self.assertEqual(self.db.get_by_path('NG-1'), 'Issue 1')

    def testKeys(self):
        self.db.data.root()['1.0'] = 'Foo'
        self.assertEqual(len(self.db.keys()), 1)

    def testKeysNested(self):
        self.db.data.root()['test1.0'] = Release()
        self.db.data.root()['test1.0']['NG-test1'] = 'Issue 1'
        self.assertEqual(len(self.db.keys()), 2)

    def testKeysDeepNested(self):
        self.db.data.root()['1.0'] = {}
        self.db.data.root()['1.0']['NG-1'] = 'Issue 1'
        self.db.data.root()['1.0']['NG-2'] = 'Issue 2'
        self.db.data.root()['1.0']['Nest'] = {}
        self.db.data.root()['1.0']['Nest']['NG-3'] = 'Issue 3'
        self.assertEqual(len(self.db.keys()), 5)
    
    def testGet(self):
        self.db.data.root()['1.0'] = Release()
        self.db.data.root()['1.0']['NG-1'] = 'Issue 1'
        self.assertEqual(self.db.get('NG-1'), 'Issue 1')


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
        for key in self.jira.cache.data.root().keys():
            del self.jira.cache.data.root()[key]
        transaction.commit()

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
        release = Release()
        release.version = '1.0'
        self.jira.cache.data.root()['1.0'] = release
        release = self.jira.get_release('1.0')
        self.assertEqual(release.version, '1.0')

    def testGetReleaseFromMultiple(self):
        release = Release()
        release.version = '1.0'
        self.jira.cache.data.root()['1.0'] = release
        release = Release()
        release.version = '2.0'
        self.jira.cache.data.root()['2.0'] = release
        release = self.jira.get_release('2.0')
        self.assertEqual(release.version, '2.0')
        release = self.jira.get_release('1.0')
        self.assertEqual(release.version, '1.0')


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

    def testMakeStory(self):
        json_data = open('jira/tests/data/NG-13332.json').read()
        json_obj = self.jira.json_to_object(json_data)
        story = self.jira.make_story('NG-13332', json_obj)
        import datetime
        import time
        creation_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime('2012-12-21T15:05:23.000-0500'[:23]
            , '%Y-%m-%dT%H:%M:%S.%f')))
        self.assertEqual(story.created, creation_date)
        self.assertEqual(story.assignee['displayName'], 'Abdul Habra')
        self.assertEqual(story.key, 'NG-13332')

    def testJsonToObject(self):
        obj = self.jira.json_to_object('{"foo": ["bar", "baz"]}')
        self.assertEqual(obj['foo'][0], 'bar')
        self.assertEqual(obj['foo'][1], 'baz')

    def testGetChangeLog(self):
        data = self.jira.get_changelog('NG-13332')
        self.assertEqual(data['key'], 'NG-13332')
