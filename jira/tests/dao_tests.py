import unittest
import json
from ..dao import Jira


class JiraTest(unittest.TestCase):
    ''' Unit tests for the Jira DAO class
    '''
    SERVER = 'jira.cengage.com'
    AUTH = 'user:pass'

    def testObjectCreation(self):
        ''' Verify we can create a Story object
        '''
        obj = Jira()
        self.assertTrue(obj is not None)

    def testInitialization(self):
        jira = Jira(self.SERVER, self.AUTH)
        self.assertEqual(jira.server, self.SERVER)
        self.assertEqual(jira.auth, self.AUTH)
        self.assertEqual(jira.cwd, [['/'], ['/']])

    def testFormatRequest(self):
        jira = Jira(self.SERVER, self.AUTH)
        self.assertEqual(jira.format_request('test/path.html'),
            'http://user:pass@jira.cengage.com/test/path.html')

    def testAllProjects(self):
        jira = Jira(self.SERVER, self.AUTH)
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/projects.html').read()
        jira.request_page = mock_request_page
        projects = jira.all_projects()
        keys = ['NG', 'MTQA', 'MTA']
        count = 0
        for project in projects.data:
            self.assertEqual(project.key, keys[count])
            count += 1

    def testGetRelease(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        jira.request_page = mock_request_page
        release = jira.get_release()
        self.assertEqual(release.data[0].key, 'NG-12459')

    def testGetReleaseKeys(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        jira.request_page = mock_request_page
        keys = jira.get_release_keys()
        self.assertEqual(keys[0], 'NG-12459')

    def testGetStory(self):
        jira = Jira()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        story = jira.get_story('NG-12345')
        self.assertEqual(story.key, 'NG-12345')
        import datetime
        import time
        creation_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime('2012-12-21T15:05:23.000-0500'[:23]
            , '%Y-%m-%dT%H:%M:%S.%f')))
        self.assertEqual(story.created, creation_date)
        self.assertEqual(story.assignee['displayName'], 'Abdul Habra')

    def testGetChangeLog(self):
        jira = Jira()
        def mock_call_rest(key, expand=[]):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        data = jira.get_changelog('NG-13332')
        print data
        self.assertEqual(data['key'], 'NG-13332')
