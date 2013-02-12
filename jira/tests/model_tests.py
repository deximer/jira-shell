import unittest
import time
import datetime
import json
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from ..model import Story, Release, Projects, Project, Kanban, History, Links, \
    Link
from ..dao import Jira
from  xml.etree import ElementTree as ET

D20121201 = datetime.datetime(2012, 12, 1, 12, 0, 0)
D20121202 = datetime.datetime(2012, 12, 2, 13, 0, 0)
D20121203 = datetime.datetime(2012, 12, 3, 14, 0, 0)
D20121205 = datetime.datetime(2012, 12, 5, 15, 0, 0)
D20121208 = datetime.datetime(2012, 12, 8, 16, 0, 0)
D20121213 = datetime.datetime(2012, 12, 13, 17, 0, 0)

def make_story(key, points=1.0, status=3, scrum_team='foo', type='72',
        created=D20121201, started=D20121202, resolved=D20121203):
    story = Story(key)
    story.points = points
    story.status = status
    story.scrum_team = scrum_team
    story.type = type
    story.created = created
    story.history = History()
    story.history.data.append((started, 1, 3))
    story.history.data.append((resolved, 3, 6))
    return story


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.story = Story('NG-1')
        self.link = Link(self.story, 'Cloners')

    def tearDown(self):
        del self.link

    def testObjectCreation(self):
        self.assertTrue(self.link is not None)

    def testCreateLink(self):
        self.assertEqual(self.link.target, self.story)
        self.assertEqual(self.link.type, 'Cloners')

class LinksTests(unittest.TestCase):
    def setUp(self):
        self.obj = Jira().json_to_object(
            open('jira/tests/data/NG-12425.json').read())[
            'fields']['issuelinks']
        self.links = Links()
        for link in self.obj:
            if link.has_key('inwardIssue'):
                self.links.data.append(make_story(link['inwardIssue']['key'],
                    type=int(link['inwardIssue']['fields']['issuetype']['id'])))
            if link.has_key('outwardIssue'):
                self.links.data.append(make_story(link['outwardIssue']['key'],
                    type=int(link['outwardIssue']['fields']['issuetype']['id'])))

    def testObjectCreation(self):
        self.assertTrue(self.obj is not None)

    def testCorrectNumberOfIssues(self):
        self.assertEqual(len(self.links.data), 4)

    def testCorrectIssueId(self):
        self.assertEqual(self.links.data[0].key, 'NG-13471')

    def testGetLinks(self):
        self.assertEqual(self.links.get_links(1)[0].key, 'NG-13471')

    def testHasLink(self):
        self.assertEqual(self.links.has_link('NG-13471'), True)

class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.obj = Jira().json_to_object(
            open('jira/tests/data/NG-13332.json').read())['changelog']
        self.history = History(Jira().json_to_object(
            open('jira/tests/data/NG-13332.json').read())['changelog'])

    def tearDown(self):
        pass

    def testObjectCreation(self):
        self.assertTrue(self.history is not None)

    def testCorrectNumberOfTransitions(self):
        self.assertEqual(len(self.history.data), 4)

    def testGetTransition(self):
        expected_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime('2013-01-04T09:36:22.000','%Y-%m-%dT%H:%M:%S.%f')))
        self.assertEqual(self.history.get_transition(10090)[0], expected_date)

    def testGetTransitionOutOfBounds(self):
        self.assertEqual(self.history.get_transition('x'), [])

    def testStarted(self):
        started = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime('2013-01-01T15:31:39.000','%Y-%m-%dT%H:%M:%S.%f')))
        self.assertEqual(self.history.started, started)

    def testStartedNotStarted(self):
        del self.history.data[1]
        self.assertEqual(self.history.started, None)

    def testResolvedNotResolved(self):
        del self.history.data[3]
        self.assertEqual(self.history.resolved, None)

    def testResolved(self):
        resolved = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime('2013-01-08T10:45:59.000','%Y-%m-%dT%H:%M:%S.%f')))
        self.assertEqual(self.history.resolved, resolved)

    def testBackflowTrue(self):
        self.history.data = []
        self.history.data.append((D20121201, 1, 3))
        self.history.data.append((D20121203, 3, 1))
        self.assertTrue(self.history.backflow)

    def testBackflowFalse(self):
        self.history.data = []
        self.history.data.append((D20121201, 1, 3))
        self.history.data.append((D20121202, 3, 10090))
        self.history.data.append((D20121203, 10090, 6))
        self.assertFalse(self.history.backflow)

    def testBackflowOneTransition(self):
        self.history.data = []
        self.history.data.append((D20121201, 1, 3))
        self.assertFalse(self.history.backflow)


class StoryTest(unittest.TestCase):
    ''' Unit tests for the Story class
    '''
    def setUp(self):
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        self.jira = Jira('jira.cengage.com', 'user:pass')
        self.jira.call_rest = mock_call_rest
        self.jira.request_page = mock_request_page
        self.jira.call_rest = mock_call_rest
        self.jira.request_page = mock_request_page

    def tearDown(self):
        import transaction
        transaction.abort()
        for key in self.jira.cache.data.keys():
            transaction.begin()
            del self.jira.cache.data[key]
            transaction.commit()

    def testObjectCreation(self):
        ''' Verify we can create a Story object
        '''
        obj = Story()
        self.assertTrue(obj is not None)

    def testObjectInitialized(self):
        import time
        obj = make_story('NG-1', type='72')
        self.assertEqual(obj.key, 'NG-1')
        self.assertEqual(obj.type, '72')

    def testBackflow(self):
        story = make_story('NG-1')
        story.history.data = []
        story.history.data.append((D20121201, 1, 3))
        story.history.data.append((D20121203, 3, 1))
        self.assertTrue(story.backflow)

    def testBackflowGracePeriod(self):
        story = make_story('NG-1')
        story.history.data = []
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 30, 0), 1, 3))
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 34, 59), 3, 1))
        self.assertFalse(story.backflow) # 4 minutes 59 seconds
        story.history.data = []
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 30, 0), 1, 3))
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 35, 0), 3, 1))
        self.assertFalse(story.backflow) # 5 minutes
        story.history.data = []
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 30, 0), 1, 3))
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 35, 1), 3, 1))
        self.assertTrue(story.backflow) # 5 minutes 1 second

    def testCycleTimeWithWeekends(self):
        story = make_story('NG-1', started=D20121201, resolved=D20121205)
        self.assertEqual(story.cycle_time_with_weekends, 4)
        story = make_story('NG-1', started=D20121202, resolved=D20121205)
        self.assertEqual(story.cycle_time_with_weekends, 3)
        story = make_story('NG-1', started=D20121203, resolved=D20121205)
        self.assertEqual(story.cycle_time_with_weekends, 2)
        story = make_story('NG-1', started=D20121201, resolved=D20121213)
        self.assertEqual(story.cycle_time_with_weekends, 12)
        story = make_story('NG-1', started=D20121205, resolved=D20121213)
        self.assertEqual(story.cycle_time_with_weekends, 8)

    def testCycleTime(self):
        story = make_story('NG-1', started=D20121201, resolved=D20121205)
        self.assertEqual(story.cycle_time, 2)
        story = make_story('NG-1', started=D20121202, resolved=D20121205)
        self.assertEqual(story.cycle_time, 2)
        story = make_story('NG-1', started=D20121203, resolved=D20121205)
        self.assertEqual(story.cycle_time, 2)
        story = make_story('NG-1', started=D20121201, resolved=D20121213)
        self.assertEqual(story.cycle_time, 8)
        story = make_story('NG-1', started=D20121205, resolved=D20121213)
        self.assertEqual(story.cycle_time, 6)
        story = make_story('NG-1', started=D20121201, resolved=D20121202)
        self.assertEqual(story.cycle_time, 0)

    def testCycleTimeNullDates(self):
        story = make_story('NG-1', started=None, resolved=None)
        self.assertEqual(story.cycle_time, None)

    def testCycleTimeLife(self):
        story = make_story('NG-1', created=D20121201, started=None,
            resolved=D20121205)
        self.assertEqual(story.lead_time, 2)


class KanbanTest(unittest.TestCase):
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
        for key in self.jira.cache.data.keys():
            del self.jira.cache.data[key]
        transaction.commit()

    def testObjectCreation(self):
        obj = Kanban()
        self.assertTrue(obj is not None)

    def testAddStory(self):
        release = Release()
        release.add_story(make_story('NG-1'))
        kanban = release.kanban()
        self.assertEqual(len(kanban.stories), 1)
        self.assertEqual(len(kanban.grid.keys()), 1)

    def testAddRelease(self):
        release = Release()
        release.add_story(make_story('NG-1'))
        self.assertEqual(len(release.kanban().stories), 1)

    def testAverageCycleTimeLife(self):
        release = Release()
        release.add_story(make_story('NG-1', created=D20121201, resolved=D20121202))
        release.add_story(make_story('NG-2', created=D20121201, resolved=D20121205))
        release.add_story(make_story('NG-3', created=D20121201, resolved=D20121208))
        release.add_story(make_story('NG-4', created=D20121201, resolved=D20121205))
        kanban = release.kanban()
        self.assertEqual(kanban.average_lead_time(), 4.0)

    def testAverageCycleTime(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121202))
        release.add_story(make_story('NG-2', started=D20121201, resolved=D20121205))
        release.add_story(make_story('NG-3', started=D20121201, resolved=D20121208))
        release.add_story(make_story('NG-4', started=D20121201, resolved=D20121205))
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time(), 4.0)

    def testAverageCycleTimeNoScrumTeam(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121202))
        release.add_story(make_story('NG-2', started=D20121201, resolved=D20121205))
        release.add_story(make_story('NG-3', started=D20121201, resolved=D20121208))
        release.add_story(make_story('NG-4', started=D20121201, resolved=D20121205))
        del release['NG-1'].scrum_team
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time(), 4.0)


    def testAverageCycleTimeBugs(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121203,
            type='1'))
        release.add_story(make_story('NG-2', started=D20121201, resolved=D20121208,
            type='1'))
        release.add_story(make_story('NG-3', started=D20121201, resolved=D20121208,
            type='72'))
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time(type=['1']), 4.5)

    def testMedianCycleTime(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121203))
        release.add_story(make_story('NG-2', started=D20121201, resolved=D20121208))
        release.add_story(make_story('NG-3', started=D20121201, resolved=D20121213))
        kanban = release.kanban()
        self.assertEqual(kanban.median_cycle_time(), 7.0)

    def testAverageCycleTimeOnlyBugs(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205,
            type='1'))
        release.add_story(make_story('NG-2', started=D20121201, resolved=D20121205,
            type='78'))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), None)

    def testAverageCycleTimeNoCompletedStories(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=None))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), None)

    def testAverageCycleTimeStrictBaked(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121202))
        release.add_story(make_story('NG-2', started=D20121201, resolved=D20121203))
        release.add_story(make_story('NG-3', started=D20121201, resolved=D20121208))
        release.add_story(make_story('NG-4', started=D20121201, resolved=D20121213))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), 5.5)

    def testVarianceCycleTime(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213))
        release.add_story(make_story('NG-4', started=D20121203, resolved=D20121213))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.variance_cycle_time(), 6.8)

    def testSquaredCycleTimes(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213))
        release.add_story(make_story('NG-4', started=D20121203, resolved=D20121213))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.squared_cycle_times(), 36.0)


    def testStdevCycleTimeLife(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add_story(make_story('NG-1', created=D20121201, resolved=D20121205))
        release.add_story(make_story('NG-2', created=D20121203, resolved=D20121205))
        release.add_story(make_story('NG-3', created=D20121205, resolved=D20121213))
        release.add_story(make_story('NG-4', created=D20121203, resolved=D20121213))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_lead_time(), 3.7)

    def testStdevCycleTimeStrictBaked(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213))
        release.add_story(make_story('NG-4', started=D20121203, resolved=D20121213))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time(), 3.7)

    def testCycleTimePerPointStrictBaked(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205,
            points=2.0))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205,
            points=1.0))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121203, resolved=None,
            points=3.0))
        release.add_story(make_story('NG-5', started=D20121203, resolved=D20121213,
            points=3.0))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.cycle_time_per_point(), 2.5)

    def testStdevCycleTimePerPointStrictBaked(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205,
            points=2.0))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205,
            points=1.0))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121203, resolved=D20121213,
            points=3.0))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time_per_point(),
            0.6382847385042254)

    def testCycleTimeForComponent(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121202,
            scrum_team='Foo'))
        release.add_story(make_story('NG-2', started=D20121201, resolved=D20121213,
            scrum_team='Bar'))
        release.add_story(make_story('NG-3', started=D20121201, resolved=D20121205,
            scrum_team='Foo'))
        release.add_story(make_story('NG-4', started=D20121201, resolved=D20121205,
            scrum_team='Foo'))
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time('Foo'), 3.0)

    def testAverageCycleTimeForEstimate(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205,
            points=2.0))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205,
            points=1.0))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121203, resolved=D20121213,
            points=3.0))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time_for_estimate('3.0'), 7.0)
        self.assertEqual(kanban.average_cycle_time_for_estimate('2.0'), 2.0)
        self.assertEqual(kanban.average_cycle_time_for_estimate('1.0'), 2.0)

    def testStdevCycleTimeForEstimate(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205,
            points=2.0))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205,
            points=1.0))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121203, resolved=D20121213,
            points=3.0))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('3.0'), 1.0)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('2.0'), 0.0)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('1.0'), 0.0)

    def testMinimumATP(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205,
            points=2.0))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205,
            points=3.0))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121203, resolved=D20121213,
            points=3.0))
        kanban = release.kanban()
        self.assertEqual(kanban.minimum_atp('3.0'), 2.0)

    def testMinimumATPNullSet(self):
        release = Release()
        kanban = release.kanban()
        self.assertEqual(kanban.minimum_atp('999.0'), None)

    def testContingency(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, resolved=D20121205,
            points=3.0))
        release.add_story(make_story('NG-2', started=D20121203, resolved=D20121205,
            points=3.0))
        release.add_story(make_story('NG-3', started=D20121205, resolved=D20121213,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121203, resolved=D20121213,
            points=3.0))
        kanban = release.kanban()
        self.assertEqual(kanban.contingency_average('NG-1'), 2.5)
        self.assertEqual(kanban.contingency_inside('NG-1'), 0.0)
        self.assertEqual(kanban.contingency_outside('NG-1'), 8.8)
        self.assertEqual(kanban.contingency_inside('NG-2'), 0.0)

    def testContingencyNoCycleTimes(self):
        release = Release()
        kanban = release.kanban()
        release.add_story(make_story('NG-1', type='72', points=2.0, started=None,
            resolved=None))
        release.add_story(make_story('NG-2', type='72', points=2.0, started=None,
            resolved=None))
        self.assertEqual(kanban.contingency_average('NG-1'), None)
        

class ReleaseTests(unittest.TestCase):
    ''' Unit tests for the Release class
    '''
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
        for key in self.jira.cache.data.keys():
            del self.jira.cache.data[key]
        transaction.commit()

    def testObjectCreation(self):
        obj = Release()
        self.assertTrue(obj is not None)

    def testProcessRawKeyNumberOnly(self):
        release = Release()
        key = release.process_raw_key('12345')
        self.assertEqual(key, 'NG-12345')

    def testProcessRawKey(self):
        release = Release()
        key = release.process_raw_key('NG-12345')
        self.assertEqual(key, 'NG-12345')


    def testAddStory(self):
        release = Release()
        key = 'NG-1'
        release.add_story(Story(key))
        self.assertEqual(release[key].key, key)

    def testGetStory(self):
        release = Release()
        key = 'NG-1'
        release.add_story(Story(key))
        story = release.get(key)
        self.assertEqual(story.key, key)

    def testGetStoryNoStory(self):
        release = Release()
        key = 'NOKEY'
        story = release.get(key)
        self.assertEqual(story, None)

    def testTaskedTeams(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release.add_story(Story('NG-4'))
        release['NG-1'].type = '72'
        release['NG-1'].scrum_team = 'Foo'
        release['NG-2'].type = '72'
        release['NG-2'].scrum_team = 'Foo'
        release['NG-3'].type = '72'
        release['NG-3'].scrum_team = 'Bar'
        release['NG-4'].type = '72'
        release['NG-4'].scrum_team = None
        self.assertEqual(len(release.tasked_teams().keys()), 3)
        self.assertEqual(release.tasked_teams()['Foo'], 2)
        self.assertEqual(release.tasked_teams()['Bar'], 1)
        self.assertEqual(release.tasked_teams()['Everything Else'], 1)

    def testDevelopers(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release.add_story(Story('NG-4'))
        release['NG-1'].type = '72'
        release['NG-1'].developer = 'joe'
        release['NG-2'].type = '72'
        release['NG-2'].developer = 'joe'
        release['NG-3'].type = '72'
        release['NG-3'].developer = 'ann'
        release['NG-4'].type = '72'
        release['NG-4'].developer = 'joe'
        self.assertEqual(len(release.developers().keys()), 2)
        self.assertEqual(release.developers()['joe'], 3)
        self.assertEqual(release.developers()['ann'], 1)

    def testOnlyStories(self):
        release = Release()
        release.add_story(make_story('NG-1', type='72'))
        release.add_story(make_story('NG-2', type='72'))
        release.add_story(make_story('NG-3', type='1'))
        self.assertEqual(len(release.stories()), 2)

    def testOnlyStartedStories(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121201, type='72'))
        release.add_story(make_story('NG-2', started=D20121201, type='78'))
        release.add_story(make_story('NG-3', started=None, type='72'))
        self.assertEqual(len(release.started_stories()), 1)

    def testStoriesByStatus(self):
        release = Release()
        release.add_story(make_story('NG-1', type='72', status=6))
        release.add_story(make_story('NG-2', type='72', status=3))
        release.add_story(make_story('NG-3', type='72', status=3))
        self.assertEqual(len(release.stories_by_status()['3']), 2)

    def testOnlyBugs(self):
        release = Release()
        release.add_story(make_story('NG-1', type='1'))
        release.add_story(make_story('NG-2', type='72'))
        release.add_story(make_story('NG-3', type='78'))
        self.assertEqual(len(release.bugs()), 2)

    def testTotalStories(self):
        release = Release()
        release.add_story(make_story('NG-1', type='72'))
        self.assertTrue(release.total_stories() == 1)
        release.add_story(make_story('NG-2', type='72'))
        self.assertTrue(release.total_stories() == 2)

    def testTotalPoints(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add_story(make_story('NG-1', type='72', points=1.5))
        release.add_story(make_story('NG-2', type='72', points=2.0))
        release.add_story(make_story('NG-3', type='1', points=5.0))
        self.assertEqual(release.total_points(), 3.5)

    def testPointsCompleted(self):
        release = Release()
        release.add_story(make_story('NG-1', type='72', points=2.0))
        release.add_story(make_story('NG-2', type='72', points=1.0))
        release.add_story(make_story('NG-3', type='1', points=0.5))
        self.assertEqual(release.total_points(), 3.0)

    def testAverageStorySize(self):
        release = Release()
        release.add_story(make_story('NG-1', type='72', points=2.0))
        release.add_story(make_story('NG-2', type='72', points=4.0))
        release.add_story(make_story('NG-3', type='72', points=8.0))
        release['NG-1'].points = 2.0
        release['NG-1'].type = '72'
        release['NG-2'].points = 4.0
        release['NG-2'].type = '72'
        release['NG-3'].points = 8.0
        release['NG-3'].type = '72'
        self.assertEqual(release.average_story_size(), 4.666666666666667)

    def testAverageStorySizeNullValues(self):
        release = Release()
        release.add_story(make_story('NG-1', type='72', points=2.0))
        release.add_story(make_story('NG-2', type='72', points=None))
        release.add_story(make_story('NG-3', type='72', points=8.0))
        self.assertEqual(release.average_story_size(), 5.0)

    def testStdStorySize(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release['NG-1'].points = 2.0
        release['NG-1'].type = '72'
        release['NG-2'].points = 4.0
        release['NG-2'].type = '72'
        release['NG-3'].points = 8.0
        release['NG-3'].type = '72'
        self.assertEqual(release.std_story_size(), 3.0550504633038931)

    def testSortBySize(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release['NG-1'].points = 2.0
        release['NG-1'].type = '72'
        release['NG-2'].points = 1.0
        release['NG-2'].type = '72'
        release['NG-3'].points = 3.0
        release['NG-3'].type = '72'
        count = 3.0
        for story in release.sort_by_size():
            self.assertEqual(count, story.points)
            count -= 1.0

    def testOnlyGroomedStories(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release['NG-1'].points = 2.0
        release['NG-1'].type = '72'
        release['NG-2'].points = None
        release['NG-2'].type = '72'
        release['NG-3'].points = 3.0
        release['NG-3'].type = '72'
        self.assertEqual(len(release.only_groomed_stories()), 2)

    def testStoriesByEstimate(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release['NG-1'].points = 2.0
        release['NG-1'].type = '72'
        release['NG-2'].points = 2.0
        release['NG-2'].type = '72'
        release['NG-3'].points = 3.0
        release['NG-3'].type = '72'
        self.assertEqual(len(release.stories_by_estimate().keys()), 2)
        self.assertEqual(len(release.stories_by_estimate()['2.0']), 2)
        self.assertEqual(len(release.stories_by_estimate()['3.0']), 1)


    def testStoriesInProcess(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release.add_story(Story('NG-4'))
        release['NG-1'].status = 3
        release['NG-1'].type = '72'
        release['NG-1'].points = 1.0
        release['NG-2'].status = 10092
        release['NG-2'].type = '72'
        release['NG-2'].points = 2.0
        release['NG-3'].status = 6
        release['NG-3'].type = '72'
        release['NG-3'].points = 3.0
        release['NG-4'].status = 3
        release['NG-4'].type = '78'
        release['NG-4'].points = 5.0
        self.assertEqual(release.stories_in_process(), 2)

    def testWip(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release.add_story(Story('NG-4'))
        release.add_story(Story('NG-5'))
        release.add_story(Story('NG-6'))
        release.add_story(Story('NG-7'))
        release.add_story(Story('NG-8'))
        release['NG-1'].status = 1
        release['NG-1'].points = 1.0
        release['NG-1'].type = '72'
        release['NG-2'].status = 3 # WIP
        release['NG-2'].points = 1.0
        release['NG-2'].type = '72'
        release['NG-3'].status = 4
        release['NG-3'].points = 1.0
        release['NG-3'].type = '72'
        release['NG-4'].status = 10036
        release['NG-4'].points = 1.0
        release['NG-4'].type = '72'
        release['NG-5'].status = 10089
        release['NG-5'].points = 1.0
        release['NG-5'].type = '72'
        release['NG-6'].status = 10090
        release['NG-6'].points = 1.0
        release['NG-6'].type = '72'
        release['NG-7'].status = 10092
        release['NG-7'].points = 1.0
        release['NG-7'].type = '72'
        release['NG-8'].status = 10104
        release['NG-8'].points = 1.0
        release['NG-8'].type = '72'
        self.assertEqual(release.wip(), 5.0)

    def testWipByStatus(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        key = tree.find('.//*/item').text
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release['NG-1'].status = 3 # In Progress
        release['NG-1'].points = 3.0
        release['NG-1'].type = '72'
        release['NG-2'].status = 6 # Closed
        release['NG-2'].points = 5.0
        release['NG-2'].type = '72'
        release['NG-3'].status = 3 # In Progress
        release['NG-3'].points = 1.5
        release['NG-3'].type = '72'
        self.assertEqual(release.wip_by_status()['3']['wip'], 4.5)
        self.assertEqual(sum([v['wip'] for v in release.wip_by_status().values()
            ]), 4.5)

    def testWipByComponent(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        key = tree.find('.//*/item/key').text
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release['NG-1'].status = 3 # In Progress
        release['NG-1'].points = 5.0
        release['NG-1'].type = '72'
        release['NG-1'].scrum_team = 'FooTeam'
        release['NG-2'].status = 3 # In Progress
        release['NG-2'].points = 2.0
        release['NG-2'].type = '72'
        release['NG-2'].scrum_team = 'FooTeam'
        release['NG-3'].status = 6 # Closed
        release['NG-3'].points = 0.499
        release['NG-3'].type = '72'
        release['NG-3'].scrum_team = 'BarTeam'
        self.assertEqual(release.wip_by_component()['FooTeam'][
            'wip'], 7.0)
        self.assertEqual(release.wip_by_component()['FooTeam'][
            'largest'], 5.0)
        self.assertEqual(len(release.wip_by_component()), 1)

    def testWipByTeamNullTeam(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release['NG-1'].status = 3 # In Progress
        release['NG-1'].points = 5.0
        release['NG-1'].type = '72'
        release['NG-1'].scrum_team = 'Some Team'
        release['NG-2'].status = 3 # In Progress
        release['NG-2'].points = 2.0
        release['NG-2'].type = '72'
        release['NG-2'].scrum_team = None
        for story in release.stories():
            print story.scrum_team
        self.assertEqual(release.wip_by_component()['Some Team']['wip'], 5.0)
        self.assertEqual(release.wip_by_component()['Everything Else']['wip']
            , 2.0)

    def testKanban(self):
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release['NG-1'].status = 3 # In Progress
        release['NG-1'].points = 2.0
        release['NG-1'].type = '72'
        release['NG-1'].scrum_team = 'FooTeam'
        release['NG-2'].status = 3 # In Progress
        release['NG-2'].points = 2.0
        release['NG-2'].type = '72'
        release['NG-2'].scrum_team = 'FooTeam'
        release['NG-3'].status = 6 # Closed
        release['NG-3'].points = 2.0
        release['NG-3'].type = '72'
        release['NG-3'].scrum_team = 'FooTeam'
        self.assertEqual(release.kanban().grid['FooTeam'][
            '3']['wip'], 4.0)
        self.assertEqual(release.kanban().grid['FooTeam'][
            '6']['wip'], 2.0)
        self.assertEqual(len(release.kanban().grid['FooTeam'][
            '3']['stories']),2)

    def testCycleTimeByComponent(self):
        # Not implemented yet
        release = Release()
        release.add_story(Story('NG-1'))
        release.add_story(Story('NG-2'))
        release.add_story(Story('NG-3'))
        release['NG-1'].status = 3 # In Progress
        release['NG-1'].points = 2.0
        release['NG-1'].type = '72'
        release['NG-2'].status = 3 # In Progress
        release['NG-2'].points = 2.0
        release['NG-2'].type = '72'
        release['NG-3'].status = 6 # Closed
        release['NG-3'].points = 2.0
        release['NG-3'].type = '72'
        # cycle_times = release.cycle_times()
        # self.assertEqual(cycle_times['Reader'], 1)

    def testGraphKanban(self):
        release = Release()
        release.add_story(make_story('NG-1', status=1, points=1.0, scrum_team='Foo'))
        release.add_story(make_story('NG-2', status=3, points=2.0, scrum_team='Bar'))
        release.add_story(make_story('NG-3', status=3, points=4.0, scrum_team='Foo'))
        release.add_story(make_story('NG-4', status=6, points=3.0, scrum_team='Foo'))
        self.assertEqual(release.graph_kanban(), '.Oo')

    def testGraphKanbanByComponent(self):
        release = Release()
        release.add_story(make_story('NG-1', status=1, points=1.0, scrum_team='Foo'))
        release.add_story(make_story('NG-2', status=3, points=5.0, scrum_team='Bar'))
        release.add_story(make_story('NG-3', status=3, points=4.0, scrum_team='Foo'))
        release.add_story(make_story('NG-4', status=6, points=3.0, scrum_team='Foo'))
        self.assertEqual(release.graph_kanban('Foo'), '.oo')

    def TestUpperPercentile(self):
        release = Release()
        release.add_story(make_story('NG-1', type='1',created=None, started=D20121201,
            resolved=D20121203))
        release.add_story(make_story('NG-2', type='1',created=None, started=D20121201,
            resolved=D20121205))
        release.add_story(make_story('NG-3', type='1',created=None, started=D20121205,
            resolved=D20121213))
        release.add_story(make_story('NG-4', type='1',created=None, started=D20121201,
            resolved=D20121213))
        upper85 = release.upper_percentiles(0.85, ['1'])
        self.assertEqual(len(upper85), 1)
        self.assertEqual(upper85[0].key, 'NG-4')
        upper50 = release.upper_percentiles(0.50, ['1'])
        self.assertEqual(len(upper50), 2)
        self.assertEqual(upper50[0].key, 'NG-3')

    def TestUpperPercentileNoStories(self):
        release = Release()
        upper50 = release.upper_percentiles(0.50, ['1'])
        self.assertEqual(upper50, [])


class ProjectTest(unittest.TestCase):
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
        for key in self.jira.cache.data.keys():
            del self.jira.cache.data[key]
        transaction.commit()

    def testObjectCreate(self):
        obj = Project()
        self.assertTrue(obj is not None)

    def testInitializeProject(self):
        project = Project('Key', 'Name', 'Owner')
        self.assertEquals(project.name, 'Name')
        self.assertEquals(project.key, 'Key')
        self.assertEquals(project.owner, 'Owner')

class ProjectsTest(unittest.TestCase):
    def testObjectCreate(self):
        obj = Projects()
        self.assertTrue(obj is not None)

    def testInitializeProjects(self):
        projects = Projects()
        projects.add(Project('Name', 'Key', 'Owner'))
        self.assertEqual(len(projects.all_projects()), 1)

