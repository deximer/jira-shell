import unittest
import time
import datetime
import json
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from ..model import Story, Release, Projects, Project, Kanban, History, Links
from repoze.folder import Folder

from ..dao import Jira
from  xml.etree import ElementTree as ET
from persistent.mapping import PersistentMapping

D20121001 = datetime.datetime(2012, 10, 1, 12, 0, 0)  # Monday
D20121002 = datetime.datetime(2012, 10, 2, 13, 0, 0)  # Tuesday
D20121003 = datetime.datetime(2012, 10, 3, 14, 0, 0)  # Wednesday
D20121005 = datetime.datetime(2012, 10, 5, 15, 0, 0)  # Friday
D20121008 = datetime.datetime(2012, 10, 8, 16, 0, 0)  # Monday
D20121013 = datetime.datetime(2012, 10, 13, 17, 0, 0) # Saturday

def make_story(key, points=1.0, status=10004, scrum_team='foo', type='7',
        created=D20121001, started=D20121002, resolved=D20121003, dev='joe'):
    story = Story()
    story.key = key
    story.points = points
    story.status = status
    story.scrum_team = scrum_team
    story.developer = dev
    story.type = type
    story.created = created
    story.history = History()
    story.history.data.append((started, 1, 10004, 'Ann Doe'))
    story.history.data.append((resolved, 10004, 6, 'Joe Doe'))
    return story


class LinksTests(unittest.TestCase):
    def setUp(self):
        self.obj = Jira().json_to_object(
            open('jsh/tests/data/NG-12425.json').read())[
            'fields']['issuelinks']
        self.links = Links()
        self.links['out']['Related'] = PersistentMapping()
        self.links['in']['Related'] = PersistentMapping()
        for link in self.obj:
            if link.has_key('inwardIssue'):
                self.links['in']['Related'][link['inwardIssue']['key']] = \
                    make_story(link['inwardIssue']['key'], type=int(
                    link['inwardIssue']['fields']['issuetype']['id']))
            if link.has_key('outwardIssue'):
                self.links['out']['Related'][link['outwardIssue']['key']] = \
                    make_story(link['outwardIssue']['key'], type=int(
                    link['outwardIssue']['fields']['issuetype']['id']))

    def testObjectCreation(self):
        self.assertTrue(self.obj is not None)

    def testCorrectNumberOfIssues(self):
        self.assertEqual(len(self.links.all), 4)

    def testCorrectIssueId(self):
        self.assertEqual(self.links['in']['Related']['NG-13471'].key,'NG-13471')

    def testGetLinks(self):
        self.assertEqual(self.links.get_links(1)[0].key, 'NG-13471')

    def testHasLink(self):
        self.assertEqual(self.links.has_link('NG-13471'), True)

    def testOutward(self):
        self.assertEqual(len(self.links.outward), 1)

    def testInward(self):
        self.assertEqual(len(self.links.inward), 3)

class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.obj = Jira().json_to_object(
            open('jsh/tests/data/NG-13332.json').read())['changelog']
        self.history = History(Jira().json_to_object(
            open('jsh/tests/data/NG-13332.json').read())['changelog'])

    def tearDown(self):
        pass

    def testObjectCreation(self):
        self.assertTrue(self.history is not None)

    def testCorrectNumberOfTransitions(self):
        self.assertEqual(len(self.history.data), 4)

    def testGetTransitionTo(self):
        expected_date = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime('2013-01-04T09:36:22.000','%Y-%m-%dT%H:%M:%S.%f')))
        self.assertEqual(self.history.get_transition_to(
            10090)[0], expected_date)

    def testGetTransitionToOutOfBounds(self):
        self.assertEqual(self.history.get_transition_to('x'), [])

    def testGetTaktTime(self):
        # This is not impl. See method in model.py for details
        self.assertEqual(self.history.get_takt_time(3, 10092), None)

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

    def testFirstStarted(self):
        started = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime('2013-01-01T15:31:39.000','%Y-%m-%dT%H:%M:%S.%f')))
        self.assertEqual(self.history.first_started, started)

    def testSkippedTrue(self):
        self.history.data = []
        self.history.data.append((D20121001, 1, 3, 'Jane Doe'))
        self.assertTrue(self.history.skipped)

    def testSkippedFalse(self):
        self.history.data = []
        self.history.data.append((D20121001, 1, 10089, 'Jane Doe'))
        self.history.data.append((D20121001, 10089, 3, 'Jane Doe'))
        self.history.data.append((D20121001, 3, 10090, 'Jane Doe'))
        self.history.data.append((D20121001, 10090, 10104, 'Jane Doe'))
        self.history.data.append((D20121001, 10104, 10092, 'Jane Doe'))
        self.history.data.append((D20121001, 10092, 10036, 'Jane Doe'))
        self.history.data.append((D20121001, 10036, 6, 'Jane Doe'))
        self.assertFalse(self.history.skipped)

    def testSkippedForeignState(self):
        self.history.data = []
        self.history.data.append((D20121001, 1, 9999, 'Jane Doe'))
        self.assertFalse(self.history.skipped)

    def testBackflowTrue(self):
        self.history.data = []
        self.history.data.append((D20121001, 1, 3, 'Jane Doe'))
        self.history.data.append((D20121003, 3, 1, 'Joe Doe'))
        self.assertTrue(self.history.backflow)

    def testBackflowFalse(self):
        self.history.data = []
        self.history.data.append((D20121001, 1, 3, 'Jane Doe'))
        self.history.data.append((D20121002, 3, 10090, 'Joe Doe'))
        self.history.data.append((D20121003, 10090, 6, 'Bill Doe'))
        self.assertFalse(self.history.backflow)

    def testBackflowOneTransition(self):
        self.history.data = []
        self.history.data.append((D20121001, 1, 3, 'Jane Doe'))
        self.assertFalse(self.history.backflow)


class StoryTest(unittest.TestCase):
    ''' Unit tests for the Story class
    '''
    def setUp(self):
        def mock_request_page(url, refresh=False):
            return open('jsh/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jsh/tests/data/rest_changelog.json').read())
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
        obj = make_story('NG-1', type='7')
        self.assertEqual(obj.key, 'NG-1')
        self.assertEqual(obj.type, '7')

    def testBackflow(self):
        story = make_story('NG-1')
        story.history.data = []
        story.history.data.append((D20121001, 1, 10004, 'Jane Doe'))
        story.history.data.append((D20121003, 10004, 1, 'Bill Doe'))
        self.assertTrue(story.backflow)

    def testBackflowGracePeriod(self):
        story = make_story('NG-1')
        story.history.data = []
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 30, 0), 1, 10004, 'Jane Doe'))
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 34, 59), 10004, 1, 'Joe Doe'))
        self.assertFalse(story.backflow) # 4 minutes 59 seconds
        story.history.data = []
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 30, 0), 1, 10004, 'Nik Doe'))
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 35, 0), 10004, 1, 'Joe Blow'))
        self.assertFalse(story.backflow) # 5 minutes
        story.history.data = []
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 30, 0), 1, 10004, 'Phil Doe'))
        story.history.data.append(
            (datetime.datetime(2012, 12, 1, 12, 35, 1), 10004, 1, 'Bill Doe'))
        self.assertTrue(story.backflow) # 5 minutes 1 second

    def testCycleTimeWithWeekends(self):
        story = make_story('NG-1', started=D20121001, resolved=D20121005)
        self.assertEqual(story.cycle_time_with_weekends, 4)
        story = make_story('NG-1', started=D20121002, resolved=D20121005)
        self.assertEqual(story.cycle_time_with_weekends, 3)
        story = make_story('NG-1', started=D20121003, resolved=D20121005)
        self.assertEqual(story.cycle_time_with_weekends, 2)
        story = make_story('NG-1', started=D20121001, resolved=D20121013)
        self.assertEqual(story.cycle_time_with_weekends, 12)
        story = make_story('NG-1', started=D20121005, resolved=D20121013)
        self.assertEqual(story.cycle_time_with_weekends, 8)

    def testCycleTime(self):
        story = make_story('NG-1', started=D20121001, resolved=D20121005)
        self.assertEqual(story.cycle_time, 4)
        story = make_story('NG-1', started=D20121002, resolved=D20121005)
        self.assertEqual(story.cycle_time, 3)
        story = make_story('NG-1', started=D20121003, resolved=D20121005)
        self.assertEqual(story.cycle_time, 2)
        story = make_story('NG-1', started=D20121001, resolved=D20121013)
        self.assertEqual(story.cycle_time, 9)
        story = make_story('NG-1', started=D20121005, resolved=D20121013)
        self.assertEqual(story.cycle_time, 5)
        story = make_story('NG-1', started=D20121001, resolved=D20121002)
        self.assertEqual(story.cycle_time, 1)

    def testCycleTimeNullDates(self):
        story = make_story('NG-1', started=None, resolved=None)
        self.assertEqual(story.cycle_time, None)

    def testCycleTimeLife(self):
        story = make_story('NG-1', created=D20121001, started=None,
            resolved=D20121005)
        self.assertEqual(story.lead_time, 4)

    def testLongCycleTime(self):
        story = make_story('NG-1', started=D20121001, resolved=D20121005)
        self.assertEqual(story.aggregate_cycle_time, 4)
        story = make_story('NG-1', started=D20121002, resolved=D20121005)
        self.assertEqual(story.aggregate_cycle_time, 3)
        story = make_story('NG-1', started=D20121003, resolved=D20121005)
        self.assertEqual(story.aggregate_cycle_time, 2)
        story = make_story('NG-1', started=D20121001, resolved=D20121013)
        self.assertEqual(story.aggregate_cycle_time, 9)
        story = make_story('NG-1', started=D20121005, resolved=D20121013)
        self.assertEqual(story.aggregate_cycle_time, 5)
        story = make_story('NG-1', started=D20121001, resolved=D20121002)
        self.assertEqual(story.aggregate_cycle_time, 1)


class KanbanTest(unittest.TestCase):
    def setUp(self):
        def mock_request_page(url, refresh=False):
            return open('jsh/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jsh/tests/data/rest_changelog.json').read())
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
        release.add_story(make_story('NG-1', created=D20121001,
            resolved=D20121002))
        release.add_story(make_story('NG-2', created=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-3', created=D20121001,
            resolved=D20121008))
        release.add_story(make_story('NG-4', created=D20121001,
            resolved=D20121005))
        kanban = release.kanban()
        self.assertEqual(kanban.average_lead_time(), 3.3)

    def testCycleTimesInStatus(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121002))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-3', started=D20121001,
            resolved=D20121008))
        release.add_story(make_story('NG-4', started=D20121001,
            resolved=D20121005))
        kanban = release.kanban()
        self.assertEqual(kanban.cycle_times_in_status()[10004], 14)

    def testCycleTimesInStatusByPoints(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121002, points=3))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121005, points=3))
        release.add_story(make_story('NG-3', started=D20121001,
            resolved=D20121008, points=3))
        release.add_story(make_story('NG-4', started=D20121001,
            resolved=D20121005, points=2))
        kanban = release.kanban()
        self.assertEqual(kanban.cycle_times_in_status(points=[3])[10004], 10)

    def testAverageTimesInStatus(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001, # 1d
            resolved=D20121003))
        release.add_story(make_story('NG-2', started=D20121001, # 2d
            resolved=D20121005))
        release.add_story(make_story('NG-3', started=D20121001, # 5d
            resolved=D20121008))
        release.add_story(make_story('NG-4', started=D20121001, # 2d
            resolved=D20121005))
        kanban = release.kanban()
        self.assertEqual(kanban.average_times_in_status()[10004], 3.8)

    def testAverageCycleTime(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121002))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-3', started=D20121001,
            resolved=D20121008))
        release.add_story(make_story('NG-4', started=D20121001,
            resolved=D20121005))
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time(), 3.5)

    def testAverageCycleTimeNoScrumTeam(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121002))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-3', started=D20121001,
            resolved=D20121008))
        release.add_story(make_story('NG-4', started=D20121001,
            resolved=D20121005))
        del release['NG-1'].scrum_team
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time(), 3.5)


    def testAverageCycleTimeBugs(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121003, type='1'))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121008, type='7'))
        release.add_story(make_story('NG-3', started=D20121001,
            resolved=D20121008, type='1'))
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time(type=['1']), 3.5)

    def testMedianCycleTime(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121003))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121008))
        release.add_story(make_story('NG-3', started=D20121001,
            resolved=D20121013))
        kanban = release.kanban()
        self.assertEqual(kanban.median_cycle_time(), 5.0)

    def testAverageCycleTimeOnlyBugs(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001, resolved=D20121005,
            type='1'))
        release.add_story(make_story('NG-2', started=D20121001, resolved=D20121005,
            type='1'))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), None)

    def testAverageCycleTimeNoCompletedStories(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001, resolved=None))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), None)

    def testAverageCycleTimeStrictBaked(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121002))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121003))
        release.add_story(make_story('NG-3', started=D20121001,
            resolved=D20121008))
        release.add_story(make_story('NG-4', started=D20121001,
            resolved=D20121013))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), 4.3)

    def testVarianceCycleTime(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-2', started=D20121003,
            resolved=D20121005))
        release.add_story(make_story('NG-3', started=D20121005,
            resolved=D20121013))
        release.add_story(make_story('NG-4', started=D20121003,
            resolved=D20121013))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.variance_cycle_time(), 3.3)

    def testSquaredCycleTimes(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-2', started=D20121003,
            resolved=D20121005))
        release.add_story(make_story('NG-3', started=D20121005,
            resolved=D20121013))
        release.add_story(make_story('NG-4', started=D20121003,
            resolved=D20121013))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.squared_cycle_times(), 13.0)


    def testStdevCycleTimeLife(self):
        xml = open('jsh/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add_story(make_story('NG-1', created=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-2', created=D20121003,
            resolved=D20121005))
        release.add_story(make_story('NG-3', created=D20121005,
            resolved=D20121013))
        release.add_story(make_story('NG-4', created=D20121003,
            resolved=D20121013))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_lead_time(), 2.5)

    def testStdevCycleTimeStrictBaked(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-2', started=D20121003,
            resolved=D20121005))
        release.add_story(make_story('NG-3', started=D20121005,
            resolved=D20121013))
        release.add_story(make_story('NG-4', started=D20121003,
            resolved=D20121013))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time(), 1.8)

    def testCycleTimePerPointStrictBaked(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001, resolved=D20121005,
            points=2.0))
        release.add_story(make_story('NG-2', started=D20121003, resolved=D20121005,
            points=1.0))
        release.add_story(make_story('NG-3', started=D20121005, resolved=D20121013,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121003, resolved=None,
            points=3.0))
        release.add_story(make_story('NG-5', started=D20121003, resolved=D20121013,
            points=3.0))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.cycle_time_per_point(), 2.0)

    def testStdevCycleTimePerPointStrictBaked(self):
        xml = open('jsh/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121005, points=2.0))
        release.add_story(make_story('NG-2', started=D20121003,
            resolved=D20121005, points=1.0))
        release.add_story(make_story('NG-3', started=D20121005,
            resolved=D20121013, points=3.0))
        release.add_story(make_story('NG-4', started=D20121003,
            resolved=D20121013, points=3.0))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time_per_point(),
            0.23570226039551587)

    def testCycleTimeForComponent(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121002, scrum_team='Foo'))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121013, scrum_team='Bar'))
        release.add_story(make_story('NG-3', started=D20121001,
            resolved=D20121005, scrum_team='Foo'))
        release.add_story(make_story('NG-4', started=D20121001,
            resolved=D20121005, scrum_team='Foo'))
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time('Foo'), 3.0)

    def testAverageCycleTimeForEstimate(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121005, points=2.0)) # 4
        release.add_story(make_story('NG-2', started=D20121003,
            resolved=D20121005, points=1.0)) # 2
        release.add_story(make_story('NG-3', started=D20121005,
            resolved=D20121013, points=3.0)) # 8
        release.add_story(make_story('NG-4', started=D20121003,
            resolved=D20121013, points=3.0)) # 10
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time_for_estimate('3.0'), 6.0)
        self.assertEqual(kanban.average_cycle_time_for_estimate('2.0'), 4.0)
        self.assertEqual(kanban.average_cycle_time_for_estimate('1.0'), 2.0)

    def testStdevCycleTimeForEstimate(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001, resolved=D20121005,
            points=2.0))
        release.add_story(make_story('NG-2', started=D20121003, resolved=D20121005,
            points=1.0))
        release.add_story(make_story('NG-3', started=D20121005, resolved=D20121013,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121003, resolved=D20121013,
            points=3.0))
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('3.0'), 1.0)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('2.0'), 0.0)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('1.0'), 0.0)

    def testMinimumATP(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001, resolved=D20121005,
            points=2.0))
        release.add_story(make_story('NG-2', started=D20121003, resolved=D20121005,
            points=3.0))
        release.add_story(make_story('NG-3', started=D20121005, resolved=D20121013,
            points=3.0))
        release.add_story(make_story('NG-4', started=D20121003, resolved=D20121013,
            points=3.0))
        kanban = release.kanban()
        self.assertEqual(kanban.minimum_atp('3.0'), 2.0)

    def testMinimumATPNullSet(self):
        release = Release()
        kanban = release.kanban()
        self.assertEqual(kanban.minimum_atp('999.0'), None)

    def testContingency(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121005, points=3.0)) # 4
        release.add_story(make_story('NG-2', started=D20121003,
            resolved=D20121005, points=3.0)) # 2
        release.add_story(make_story('NG-3', started=D20121005,
            resolved=D20121013, points=3.0)) # 8
        release.add_story(make_story('NG-4', started=D20121003,
            resolved=D20121013, points=3.0)) # 10
        kanban = release.kanban()
        self.assertEqual(kanban.contingency_average('NG-1'), 0.5)
        self.assertEqual(kanban.contingency_inside('NG-1'), -2.0)
        self.assertEqual(kanban.contingency_outside('NG-1'), 5.9)
        self.assertEqual(kanban.contingency_inside('NG-2'), 0.0)

    def testContingencyNoCycleTimes(self):
        release = Release()
        kanban = release.kanban()
        release.add_story(make_story('NG-1', type='7', points=2.0,
            started=None, resolved=None))
        release.add_story(make_story('NG-2', type='7', points=2.0,
            started=None, resolved=None))
        self.assertEqual(kanban.contingency_average('NG-1'), None)

    def testProcesscycleEfficiency(self):
        release = Release()
        kanban = release.kanban()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121005))
        release.add_story(make_story('NG-2', started=D20121003,
            resolved=D20121005))
        release['NG-1'].history.data.append((D20121001, 1, 10002, 'Jane Doe'))
        release['NG-1'].history.data.append((D20121002, 10002,10004,'Jane Doe'))
        release['NG-1'].history.data.append((D20121005, 10004, 10005, 'Jane Doe'))
        release['NG-1'].history.data.append((D20121013, 10005, 6, 'Jane Doe'))
        release['NG-2'].history.data.append((D20121001, 1, 10002, 'Jane Doe'))
        release['NG-2'].history.data.append((D20121002, 10002, 10004, 'Jane Doe'))
        release['NG-2'].history.data.append((D20121003, 10004, 10005, 'Jane Doe'))
        release['NG-2'].history.data.append((D20121005, 10005, 6, 'Jane Doe'))
        self.assertEqual(kanban.process_cycle_efficiency(), 100.0)
        

class ReleaseTests(unittest.TestCase):
    ''' Unit tests for the Release class
    '''
    def setUp(self):
        def mock_request_page(url, refresh=False):
            return open('jsh/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jsh/tests/data/rest_changelog.json').read())
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
        s1 = Story(); s1.key = key; release.add_story(s1)
        release.add_story(s1)
        self.assertEqual(release[key].key, key)

    def testGetStory(self):
        release = Release()
        key = 'NG-1'
        s1 = Story(); s1.key = key; release.add_story(s1)
        release.add_story(s1)
        story = release.get(key)
        self.assertEqual(story.key, key)

    def testGetStoryNoStory(self):
        release = Release()
        key = 'NOKEY'
        story = release.get(key)
        self.assertEqual(story, None)

    def testTaskedTeams(self):
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        s4 = Story(); s4.key = 'NG-4'; release.add_story(s4)
        release['NG-1'].type = '7'
        release['NG-1'].scrum_team = 'Foo'
        release['NG-2'].type = '7'
        release['NG-2'].scrum_team = 'Foo'
        release['NG-3'].type = '7'
        release['NG-3'].scrum_team = 'Bar'
        release['NG-4'].type = '7'
        release['NG-4'].scrum_team = None
        self.assertEqual(len(release.tasked_teams().keys()), 3)
        self.assertEqual(release.tasked_teams()['Foo'], 2)
        self.assertEqual(release.tasked_teams()['Bar'], 1)
        self.assertEqual(release.tasked_teams()['Everything Else'], 1)

    def testDevelopers(self):
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        s4 = Story(); s4.key = 'NG-4'; release.add_story(s4)
        release['NG-1'].type = '7'
        release['NG-1'].developer = 'joe'
        release['NG-2'].type = '7'
        release['NG-2'].developer = 'joe'
        release['NG-3'].type = '7'
        release['NG-3'].developer = 'ann'
        release['NG-4'].type = '7'
        release['NG-4'].developer = 'joe'
        self.assertEqual(len(release.developers().keys()), 2)
        self.assertEqual(len(release.developers()['joe']), 3)
        self.assertEqual(len(release.developers()['ann']), 1)

    def testAggregateDeveloperCycleTime(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001,
            resolved=D20121003, dev='ann'))
        release.add_story(make_story('NG-2', started=D20121001,
            resolved=D20121008, dev='ann'))
        release.add_story(make_story('NG-3', started=D20121005,
            resolved=D20121013, dev='nik'))
        self.assertEqual(release.aggregate_developer_cycle_time(), 12)

    def testAverageDeveloperCycleTime(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001, #Sat - Tue 1d
            resolved=D20121005, dev='ann'))
        release.add_story(make_story('NG-2', started=D20121001, #Sat - Sat 5d
            resolved=D20121008, dev='ann'))
        release.add_story(make_story('NG-3', started=D20121003, #Mon - Sat 4d
            resolved=D20121008, dev='nik'))
        self.assertEqual(release.average_developer_cycle_time(), 6.0)

    def testOnlyStories(self):
        release = Release()
        release.add_story(make_story('NG-1', type='7'))
        release.add_story(make_story('NG-2', type='7'))
        release.add_story(make_story('NG-3', type='15'))
        self.assertEqual(len(release.stories()), 2)

    def testOnlyStartedStories(self):
        release = Release()
        release.add_story(make_story('NG-1', started=D20121001, type='7'))
        release.add_story(make_story('NG-2', started=D20121001, type='15'))
        release.add_story(make_story('NG-3', started=None, type='7'))
        self.assertEqual(len(release.started_stories()), 1)

    def testStoriesByStatus(self):
        release = Release()
        release.add_story(make_story('NG-1', type='7', status=6))
        release.add_story(make_story('NG-2', type='7', status=3))
        release.add_story(make_story('NG-3', type='7', status=3))
        self.assertEqual(len(release.stories_by_status()['3']), 2)

    def testOnlyBugs(self):
        release = Release()
        release.add_story(make_story('NG-1', type='1'))
        release.add_story(make_story('NG-2', type='7'))
        release.add_story(make_story('NG-3', type='1'))
        self.assertEqual(len(release.bugs()), 2)

    def testTotalStories(self):
        release = Release()
        release.add_story(make_story('NG-1', type='7'))
        self.assertTrue(release.total_stories() == 1)
        release.add_story(make_story('NG-2', type='7'))
        self.assertTrue(release.total_stories() == 2)

    def testTotalPoints(self):
        release = Release()
        release.add_story(make_story('NG-1', type='7', points=1.5))
        release.add_story(make_story('NG-2', type='7', points=2.0))
        release.add_story(make_story('NG-3', type='1', points=5.0))
        self.assertEqual(release.total_points(), 3.5)

    def testPointsCompleted(self):
        release = Release()
        release.add_story(make_story('NG-1', type='7', points=2.0))
        release.add_story(make_story('NG-2', type='7', points=1.0))
        release.add_story(make_story('NG-3', type='15', points=0.5))
        self.assertEqual(release.total_points(), 3.0)

    def testAverageStorySize(self):
        release = Release()
        release.add_story(make_story('NG-1', type='7', points=2.0))
        release.add_story(make_story('NG-2', type='7', points=4.0))
        release.add_story(make_story('NG-3', type='7', points=8.0))
        release['NG-1'].points = 2.0
        release['NG-1'].type = '7'
        release['NG-2'].points = 4.0
        release['NG-2'].type = '7'
        release['NG-3'].points = 8.0
        release['NG-3'].type = '7'
        self.assertEqual(release.average_story_size(), 4.666666666666667)

    def testAverageStorySizeNullValues(self):
        release = Release()
        release.add_story(make_story('NG-1', type='7', points=2.0))
        release.add_story(make_story('NG-2', type='7', points=None))
        release.add_story(make_story('NG-3', type='7', points=8.0))
        self.assertEqual(release.average_story_size(), 5.0)

    def testStdStorySize(self):
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        release['NG-1'].points = 2.0
        release['NG-1'].type = '7'
        release['NG-2'].points = 4.0
        release['NG-2'].type = '7'
        release['NG-3'].points = 8.0
        release['NG-3'].type = '7'
        self.assertEqual(release.std_story_size(), 2.4944382578492941)

    def testSortBySize(self):
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        release['NG-1'].points = 2.0
        release['NG-1'].type = '7'
        release['NG-2'].points = 1.0
        release['NG-2'].type = '7'
        release['NG-3'].points = 3.0
        release['NG-3'].type = '7'
        count = 3.0
        for story in release.sort_by_size():
            self.assertEqual(count, story.points)
            count -= 1.0

    def testOnlyGroomedStories(self):
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        release['NG-1'].points = 2.0
        release['NG-1'].type = '7'
        release['NG-2'].points = None
        release['NG-2'].type = '7'
        release['NG-3'].points = 3.0
        release['NG-3'].type = '7'
        self.assertEqual(len(release.only_groomed_stories()), 2)

    def testStoriesByEstimate(self):
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        release['NG-1'].points = 2.0
        release['NG-1'].type = '7'
        release['NG-2'].points = 2.0
        release['NG-2'].type = '7'
        release['NG-3'].points = 3.0
        release['NG-3'].type = '7'
        self.assertEqual(len(release.stories_by_estimate().keys()), 2)
        self.assertEqual(len(release.stories_by_estimate()['2.0']), 2)
        self.assertEqual(len(release.stories_by_estimate()['3.0']), 1)


    def testStoriesInProcess(self):
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        s4 = Story(); s4.key = 'NG-4'; release.add_story(s4)
        release['NG-1'].status = 10004
        release['NG-1'].type = '7'
        release['NG-1'].points = 1.0
        release['NG-2'].status = 10005
        release['NG-2'].type = '7'
        release['NG-2'].points = 2.0
        release['NG-3'].status = 6
        release['NG-3'].type = '7'
        release['NG-3'].points = 3.0
        release['NG-4'].status = 10004 
        release['NG-4'].type = '1'
        release['NG-4'].points = 5.0
        self.assertEqual(release.stories_in_process(), 2)

    def testWip(self):
        release = Release()
        s2 = Story()
        s2.key = 'NG-1'
        release.add_story(s2)
        s2 = Story()
        s2.key = 'NG-2'
        release.add_story(s2)
        s3 = Story()
        s3.key = 'NG-3'
        release.add_story(s3)
        s4 = Story()
        s4.key = 'NG-4'
        release.add_story(s4)
        s5 = Story()
        s5.key = 'NG-5'
        release.add_story(s5)
        s6 = Story()
        s6.key = 'NG-6'
        release.add_story(s6)
        s7 = Story()
        s7.key = 'NG-7'
        release.add_story(s7)
        s8 = Story()
        s8.key = 'NG-8'
        release.add_story(s8)
        release['NG-1'].status = 1
        release['NG-1'].points = 1.0
        release['NG-1'].type = '1'
        release['NG-2'].status = 10005 # WIP
        release['NG-2'].points = 1.0
        release['NG-2'].type = '7'
        release['NG-3'].status = 6
        release['NG-3'].points = 1.0
        release['NG-3'].type = '7'
        release['NG-4'].status = 10004
        release['NG-4'].points = 1.0
        release['NG-4'].type = '7'
        release['NG-5'].status = 10005
        release['NG-5'].points = 1.0
        release['NG-5'].type = '7'
        release['NG-6'].status = 10005
        release['NG-6'].points = 1.0
        release['NG-6'].type = '7'
        release['NG-7'].status = 1
        release['NG-7'].points = 1.0
        release['NG-7'].type = '7'
        release['NG-8'].status = 10004
        release['NG-8'].points = 1.0
        release['NG-8'].type = '7'
        self.assertEqual(release.wip(), 5.0)

    def testWipByStatus(self):
        release = Release()
        s2 = Story()
        s2.key = 'NG-1'
        release.add_story(s2)
        s2 = Story()
        s2.key = 'NG-2'
        release.add_story(s2)
        s3 = Story()
        s3.key = 'NG-3'
        release.add_story(s3)
        release['NG-1'].status = 10005 # In Progress
        release['NG-1'].points = 3.0
        release['NG-1'].type = '7'
        release['NG-2'].status = 6 # Closed
        release['NG-2'].points = 5.0
        release['NG-2'].type = '7'
        release['NG-3'].status = 10005 # In Progress
        release['NG-3'].points = 1.5
        release['NG-3'].type = '7'
        self.assertEqual(release.wip_by_status()['10005']['wip'], 4.5)
        self.assertEqual(sum([v['wip'] for v in release.wip_by_status().values()
            ]), 4.5)

    def testWipByComponent(self):
        release = Release()
        s2 = Story()
        s2.key = 'NG-1'
        release.add_story(s2)
        s2 = Story()
        s2.key = 'NG-2'
        release.add_story(s2)
        s3 = Story()
        s3.key = 'NG-3'
        release.add_story(s3)
        release['NG-1'].status = 10004 # In Progress
        release['NG-1'].points = 5.0
        release['NG-1'].type = '7'
        release['NG-1'].scrum_team = 'FooTeam'
        release['NG-2'].status = 10004 # In Progress
        release['NG-2'].points = 2.0
        release['NG-2'].type = '7'
        release['NG-2'].scrum_team = 'FooTeam'
        release['NG-3'].status = 6 # Closed
        release['NG-3'].points = 0.499
        release['NG-3'].type = '7'
        release['NG-3'].scrum_team = 'BarTeam'
        self.assertEqual(release.wip_by_component()['FooTeam'][
            'wip'], 7.0)
        self.assertEqual(release.wip_by_component()['FooTeam'][
            'largest'], 5.0)
        self.assertEqual(len(release.wip_by_component()), 1)

    def testWipByTeamNullTeam(self):
        release = Release()
        s1 = Story()
        s1.key = 'NG-1'
        release.add_story(s1)
        s2 = Story()
        s2.key = 'NG-2'
        release.add_story(s2)
        release['NG-1'].status = 10004 # In Progress
        release['NG-1'].points = 5.0
        release['NG-1'].type = '7'
        release['NG-1'].scrum_team = 'Some Team'
        release['NG-2'].status = 10004 # In Progress
        release['NG-2'].points = 2.0
        release['NG-2'].type = '7'
        release['NG-2'].scrum_team = None
        self.assertEqual(release.wip_by_component()['Some Team']['wip'], 5.0)
        self.assertEqual(release.wip_by_component()['Everything Else']['wip']
            , 2.0)

    def testKanban(self):
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        release['NG-1'].status = 10004 # In Progress
        release['NG-1'].points = 2.0
        release['NG-1'].type = '7'
        release['NG-1'].scrum_team = 'FooTeam'
        release['NG-2'].status = 10004 # In Progress
        release['NG-2'].points = 2.0
        release['NG-2'].type = '7'
        release['NG-2'].scrum_team = 'FooTeam'
        release['NG-3'].status = 6 # Closed
        release['NG-3'].points = 2.0
        release['NG-3'].type = '7'
        release['NG-3'].scrum_team = 'FooTeam'
        self.assertEqual(release.kanban().grid['FooTeam'][
            '10004']['wip'], 4.0)
        self.assertEqual(release.kanban().grid['FooTeam'][
            '6']['wip'], 2.0)
        self.assertEqual(len(release.kanban().grid['FooTeam'][
            '10004']['stories']),2)

    def testCycleTimeByComponent(self):
        # Not implemented yet
        release = Release()
        s1 = Story(); s1.key = 'NG-1'; release.add_story(s1)
        s2 = Story(); s2.key = 'NG-2'; release.add_story(s2)
        s3 = Story(); s3.key = 'NG-3'; release.add_story(s3)
        release['NG-1'].status = 10004 # In Progress
        release['NG-1'].points = 2.0
        release['NG-1'].type = '7'
        release['NG-2'].status = 10004 # In Progress
        release['NG-2'].points = 2.0
        release['NG-2'].type = '7'
        release['NG-3'].status = 6 # Closed
        release['NG-3'].points = 2.0
        release['NG-3'].type = '7'
        # cycle_times = release.cycle_times()
        # self.assertEqual(cycle_times['Reader'], 1)

    def testGraphKanban(self):
        release = Release()
        release.add_story(make_story('NG-1', status=1, points=1.0, scrum_team='Foo'))
        release.add_story(make_story('NG-2', status=10004, points=2.0, scrum_team='Bar'))
        release.add_story(make_story('NG-3', status=10004, points=4.0, scrum_team='Foo'))
        release.add_story(make_story('NG-4', status=6, points=3.0, scrum_team='Foo'))
        self.assertEqual(release.graph_kanban(), '.Oo')

    def testGraphKanbanByComponent(self):
        release = Release()
        release.add_story(make_story('NG-1', status=1, points=1.0, scrum_team='Foo'))
        release.add_story(make_story('NG-2', status=10004, points=5.0, scrum_team='Bar'))
        release.add_story(make_story('NG-3', status=10004, points=4.0, scrum_team='Foo'))
        release.add_story(make_story('NG-4', status=6, points=3.0, scrum_team='Foo'))
        self.assertEqual(release.graph_kanban('Foo'), '.oo')

    def TestUpperPercentile(self):
        release = Release()
        release.add_story(make_story('NG-1', type='7',created=None,
            started=D20121001, resolved=D20121003))
        release.add_story(make_story('NG-2', type='7',created=None,
            started=D20121001, resolved=D20121005))
        release.add_story(make_story('NG-3', type='7',created=None,
            started=D20121005, resolved=D20121013))
        release.add_story(make_story('NG-4', type='7',created=None,
            started=D20121001, resolved=D20121013))
        upper85 = release.upper_percentiles(0.85, ['7'])
        self.assertEqual(len(upper85), 1)
        self.assertEqual(upper85[0].key, 'NG-4')
        upper50 = release.upper_percentiles(0.50, ['7'])
        self.assertEqual(len(upper50), 2)
        self.assertEqual(upper50[0].key, 'NG-3')

    def TestUpperPercentileNoStories(self):
        release = Release()
        upper50 = release.upper_percentiles(0.50, ['7'])
        self.assertEqual(upper50, [])


class ProjectTest(unittest.TestCase):
    def setUp(self):
        def mock_request_page(url, refresh=False):
            return open('jsh/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jsh/tests/data/rest_changelog.json').read())
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

