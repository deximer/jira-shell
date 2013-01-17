import unittest
import datetime
import json
from ..model import Story, Release, Projects, Project, Kanban
from ..dao import Jira
from  xml.etree import ElementTree as ET

D20121201 = datetime.datetime(2012, 12, 1)
D20121202 = datetime.datetime(2012, 12, 2)
D20121203 = datetime.datetime(2012, 12, 3)
D20121205 = datetime.datetime(2012, 12, 5)
D20121208 = datetime.datetime(2012, 12, 8)
D20121213 = datetime.datetime(2012, 12, 13)

class StoryTest(unittest.TestCase):
    ''' Unit tests for the Story class
    '''

    def testObjectCreation(self):
        ''' Verify we can create a Story object
        '''
        obj = Story()
        self.assertTrue(obj is not None)

    def testObjectInitialized(self):
        import time
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.findall('.//*/item')
        obj = Story(item[3])
        self.assertEqual(obj.key, 'NG-12391')
        self.assertEqual(obj.type, '72')
        self.assertEqual(obj.started.isoformat(), '2012-12-13T11:17:19')
        self.assertEqual(obj.created.isoformat(), '2012-10-22T15:34:26')

    def testCycleTime(self):
        story = Story()
        story.started = D20121201
        story.resolved = D20121205
        self.assertEqual(story.cycle_time, 4)

    def testCycleTimeNullDates(self):
        story = Story()
        story.started = None
        story.resolved = None
        self.assertEqual(story.cycle_time, None)

    def testCycleTimeLife(self):
        story = Story()
        story.created = D20121201
        story.started = D20121203
        story.resolved = D20121205
        self.assertEqual(story.cycle_time_life, 4)


class KanbanTest(unittest.TestCase):
    def testObjectCreation(self):
        obj = Kanban()
        self.assertTrue(obj is not None)

    def testAddStory(self):
        kanban = Kanban()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        kanban.add(Story(item))
        self.assertEqual(len(kanban.stories), 1)
        self.assertEqual(len(kanban.grid.keys()), 1)

    def testAddRelease(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        jira.request_page = mock_request_page
        release = jira.get_release()
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(len(kanban.stories), 125)
        self.assertEqual(len(kanban.grid['Core and Builder']), 6)

    def testAverageCycleTimeLife(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        jira.request_page = mock_request_page
        release = jira.get_release()
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time_life(), 16.0)

    def testAverageCycleTime(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        jira.request_page = mock_request_page
        release = jira.get_release()
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time(), 8.0)

    def testAverageCycleTimeBugs(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '1'
        release.data[0].started = D20121201
        release.data[0].resolved = D20121203
        release.data[1].type = '1'
        release.data[1].started = D20121201
        release.data[1].resolved = D20121208
        release.data[2].type = '1'
        release.data[2].started = D20121201
        release.data[2].resolved = D20121208
        release.data[3].type = '72'
        release.data[3].started = D20121201
        release.data[3].resolved = D20121208
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time(type=['1']), 5.3)

    def testMedianCycleTime(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[0].started = D20121201
        release.data[0].resolved = D20121203
        release.data[1].type = '72'
        release.data[1].started = D20121201
        release.data[1].resolved = D20121208
        release.data[2].type = '72'
        release.data[2].started = D20121201
        release.data[2].resolved = D20121213
        kanban = release.kanban()
        self.assertEqual(kanban.median_cycle_time(), 7.0)

    def testAverageCycleTimeOnlyBugs(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.data[0].started = D20121201
        release.data[0].resolved = D20121205
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), None)

    def testAverageCycleTimeNoCompletedStories(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[0].started = D20121201
        release.data[0].resolved = None
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), None)

    def testAverageCycleTimeStrictBaked(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].started = D20121201
        release.data[0].resolved = D20121205
        release.data[0].type = '72'
        release.data[1].started = D20121203
        release.data[1].resolved = D20121205
        release.data[1].type = '72'
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213
        release.data[2].type = '72'
        release.data[3].started = D20121203
        release.data[3].resolved = D20121213
        release.data[3].type = '72'
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), 6)

    def testStdevCycleTimeLife(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].created = D20121201
        release.data[0].resolved = D20121205
        release.data[0].type = '72'
        release.data[1].created = D20121203
        release.data[1].resolved = D20121205
        release.data[1].type = '72'
        release.data[2].created = D20121205
        release.data[2].resolved = D20121213
        release.data[2].type = '72'
        release.data[3].created = D20121203
        release.data[3].resolved = D20121213
        release.data[3].type = '72'
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time_life(), 3.7)

    def testStdevCycleTimeStrictBaked(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].started = D20121201
        release.data[0].resolved = D20121205
        release.data[0].type = '72'
        release.data[1].started = D20121203
        release.data[1].resolved = D20121205
        release.data[1].type = '72'
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213
        release.data[2].type = '72'
        release.data[3].started = D20121203
        release.data[3].resolved = D20121213
        release.data[3].type = '72'
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time(), 3.7)

    def testCycleTimePerPointStrictBaked(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].started = D20121201
        release.data[0].resolved = D20121205 # 4 days
        release.data[0].type = '72'
        release.data[0].points = 2.0
        release.data[1].started = D20121203
        release.data[1].resolved = D20121205 # 2 days
        release.data[1].type = '72'
        release.data[1].points = 1.0
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213 # 8 days
        release.data[2].type = '72'
        release.data[2].points = 3.0
        release.data[3].started = D20121203
        release.data[3].resolved = D20121213 # 10 days
        release.data[3].type = '72'
        release.data[3].points = 3.0
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.cycle_time_per_point(), 2.5)

    def testStdevCycleTimePerPointStrictBaked(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].started = D20121201
        release.data[0].resolved = D20121205 # 4 days
        release.data[0].type = '72'
        release.data[0].points = 2.0
        release.data[1].started = D20121203
        release.data[1].resolved = D20121205 # 2 days
        release.data[1].type = '72'
        release.data[1].points = 1.0
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213 # 8 days
        release.data[2].type = '72'
        release.data[2].points = 3.0
        release.data[3].started = D20121203
        release.data[3].resolved = D20121213 # 10 days
        release.data[3].type = '72'
        release.data[3].points = 3.0
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time_per_point(),
            0.6382847385042254)

    def testCycleTimeForComponent(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        jira.request_page = mock_request_page
        release = jira.get_release()
        kanban = release.kanban()
        self.assertEqual(kanban.average_cycle_time('Continuous Improvement '), 10.0)

    def testAverageCycleTimeForEstimate(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].started = D20121201
        release.data[0].resolved = D20121205 # 4 days
        release.data[0].type = '72'
        release.data[0].points = 2.0
        release.data[1].started = D20121203
        release.data[1].resolved = D20121205 # 2 days
        release.data[1].type = '72'
        release.data[1].points = 1.0
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213 # 8 days
        release.data[2].type = '72'
        release.data[2].points = 3.0
        release.data[3].started = D20121203
        release.data[3].resolved = D20121213 # 10 days
        release.data[3].type = '72'
        release.data[3].points = 3.0
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time_for_estimate('3.0'), 9.0)
        self.assertEqual(kanban.average_cycle_time_for_estimate('2.0'), 4.0)
        self.assertEqual(kanban.average_cycle_time_for_estimate('1.0'), 2.0)

    def testStdevCycleTimeForEstimate(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].started = D20121201
        release.data[0].resolved = D20121205 # 4 days
        release.data[0].type = '72'
        release.data[0].points = 2.0
        release.data[1].started = D20121203
        release.data[1].resolved = D20121205 # 2 days
        release.data[1].type = '72'
        release.data[1].points = 1.0
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213 # 8 days
        release.data[2].type = '72'
        release.data[2].points = 3.0
        release.data[3].started = D20121203
        release.data[3].resolved = D20121213 # 10 days
        release.data[3].type = '72'
        release.data[3].points = 3.0
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('3.0'), 1.0)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('2.0'), 0.0)
        self.assertEqual(kanban.stdev_cycle_time_for_estimate('1.0'), 0.0)

    def testContingency(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].key = 'NG-TEST'
        release.data[0].started = D20121201
        release.data[0].resolved = D20121205 # 4 days
        release.data[0].type = '72'
        release.data[0].points = 2.0
        release.data[1].started = D20121203
        release.data[1].resolved = D20121205 # 2 days
        release.data[1].type = '72'
        release.data[1].points = 2.0
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213 # 8 days
        release.data[2].type = '72'
        release.data[2].points = 2.0
        release.data[3].started = D20121203
        release.data[3].resolved = D20121213 # 10 days
        release.data[3].type = '72'
        release.data[3].points = 2.0
        kanban = release.kanban()
        self.assertEqual(kanban.contingency_average('NG-TEST'), 2.0)
        self.assertEqual(kanban.contingency_inside('NG-TEST'), -4.3)
        self.assertEqual(kanban.contingency_outside('NG-TEST'), 8.3)

    def testContingencyNoCycleTimes(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        kanban = release.kanban()
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].key = 'NG-TEST'
        release.data[0].started = None
        release.data[0].resolved = None
        release.data[0].type = '72'
        release.data[0].points = 2.0
        release.data[1].started = None
        release.data[1].resolved = None
        release.data[1].type = '72'
        release.data[1].points = 2.0
        self.assertEqual(kanban.contingency_average('NG-TEST'), None)
        

class ReleaseTests(unittest.TestCase):
    ''' Unit tests for the Release class
    '''

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
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        self.assertEqual(release.data[0].key, 'NG-12459')

    def testGetStory(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        key = 'NG-12459'
        story = release.get(key)
        self.assertEqual(story.key, key)

    def testGetStoryNoStory(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        key = 'NOKEY'
        story = release.get(key)
        self.assertEqual(story, None)

    def testTaskedTeams(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[0].scrum_team = 'Foo'
        release.data[1].type = '72'
        release.data[1].scrum_team = 'Foo'
        release.data[2].type = '72'
        release.data[2].scrum_team = 'Bar'
        release.data[3].type = '72'
        release.data[3].scrum_team = None
        self.assertEqual(len(release.tasked_teams().keys()), 3)
        self.assertEqual(release.tasked_teams()['Foo'], 2)
        self.assertEqual(release.tasked_teams()['Bar'], 1)
        self.assertEqual(release.tasked_teams()['Everything Else'], 1)

    def testDevelopers(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[0].developer = 'joe'
        release.data[1].type = '72'
        release.data[1].developer = 'joe'
        release.data[2].type = '72'
        release.data[2].developer = 'ann'
        release.data[3].type = '72'
        release.data[3].developer = 'joe'
        self.assertEqual(len(release.developers().keys()), 2)
        self.assertEqual(release.developers()['joe'], 3)
        self.assertEqual(release.developers()['ann'], 1)

    def testOnlyStories(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[2].type = '72'
        self.assertEqual(len(release.stories()), 2)

    def testOnlyStartedStories(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[0].started = D20121201
        release.data[2].type = '72'
        release.data[2].started = None
        self.assertEqual(len(release.started_stories()), 1)

    def testStoriesByStatus(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[0].status = 6
        release.data[1].type = '72'
        release.data[1].status = 3
        release.data[2].type = '72'
        release.data[2].status = 3
        self.assertEqual(len(release.stories_by_status()['3']), 2)

    def testOnlyBugs(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '1'
        release.data[1].type = '72'
        release.data[2].type = '78'
        self.assertEqual(len(release.bugs()), 2)

    def testTotalStories(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.data[0].type = '72'
        self.assertTrue(release.total_stories() == 1)
        release.add(Story(item))
        release.data[1].type = '72'
        self.assertTrue(release.total_stories() == 2)

    def testTotalPoints(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[1].type = '72'
        self.assertEqual(release.total_points(), 3.0)

    def testPointsCompleted(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[1].type = '72'
        self.assertEqual(release.total_points(), 3.0)

    def testAverageStorySize(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[0].type = '72'
        release.data[1].points = 4.0
        release.data[1].type = '72'
        release.data[2].points = 8.0
        release.data[2].type = '72'
        self.assertEqual(release.average_story_size(), 4.666666666666667)

    def testAverageStorySizeNullValues(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[0].type = '72'
        release.data[1].points = None
        release.data[1].type = '72'
        release.data[2].points = 8.0
        release.data[2].type = '72'
        self.assertEqual(release.average_story_size(), 5.0)

    def testStdStorySize(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[0].type = '72'
        release.data[1].points = 4.0
        release.data[1].type = '72'
        release.data[2].points = 8.0
        release.data[2].type = '72'
        self.assertEqual(release.std_story_size(), 3.0550504633038931)

    def test_sort_by_size(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[1].points = 1.0
        release.data[2].points = 3.0
        count = 3.0
        for story in release.sort_by_size():
            self.assertEqual(count, story.points)
            count -= 1.0

    def testOnlyGroomedStories(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[0].type = '72'
        release.data[1].points = None
        release.data[1].type = '72'
        release.data[2].points = 3.0
        release.data[2].type = '72'
        self.assertEqual(len(release.only_groomed_stories()), 2)

    def testStoriesByEstimate(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[0].type = '72'
        release.data[1].points = 2.0
        release.data[1].type = '72'
        release.data[2].points = 3.0
        release.data[2].type = '72'
        self.assertEqual(len(release.stories_by_estimate().keys()), 2)
        self.assertEqual(len(release.stories_by_estimate()['2.0']), 2)
        self.assertEqual(len(release.stories_by_estimate()['3.0']), 1)


    def testStoriesInProcess(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item)) # Left as type=1, bug
        release.data[0].status = 3
        release.data[0].type = '72'
        release.data[1].status = 10092
        release.data[1].type = '72'
        release.data[2].status = 6
        release.data[2].type = '72'
        self.assertEqual(release.stories_in_process(), 2)

    def testWip(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 1
        release.data[0].points = 1.0
        release.data[0].type = '72'
        release.data[1].status = 3 # WIP
        release.data[1].points = 1.0
        release.data[1].type = '72'
        release.data[2].status = 4
        release.data[2].points = 1.0
        release.data[2].type = '72'
        release.data[3].status = 10036
        release.data[3].points = 1.0
        release.data[3].type = '72'
        release.data[4].status = 10089
        release.data[4].points = 1.0
        release.data[4].type = '72'
        release.data[5].status = 10090
        release.data[5].points = 1.0
        release.data[5].type = '72'
        release.data[6].status = 10092
        release.data[6].points = 1.0
        release.data[6].type = '72'
        release.data[7].status = 10104
        release.data[7].points = 1.0
        release.data[7].type = '72'
        self.assertEqual(release.wip(), 5.0)

    def testWipByStatus(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3 # In Progress
        release.data[0].type = '72'
        release.data[1].status = 6 # Closed
        release.data[1].type = '72'
        self.assertEqual(release.wip_by_status()['3']['wip'], 1.5)
        self.assertEqual(sum([v['wip'] for v in release.wip_by_status().values()
            ]), 1.5)

    def testWipByComponent(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3 # In Progress
        release.data[0].points = 5.0
        release.data[0].type = '72'
        release.data[1].status = 3 # In Progress
        release.data[1].points = 2.0
        release.data[1].type = '72'
        release.data[2].status = 6 # Closed
        release.data[2].points = 0.499
        release.data[2].type = '72'
        self.assertEqual(release.wip_by_component()['Core and Builder'][
            'wip'], 7.0)
        self.assertEqual(release.wip_by_component()['Core and Builder'][
            'largest'], 5.0)
        self.assertEqual(len(release.wip_by_component()), 1)

    def testWipByTeamNullTeam(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3 # In Progress
        release.data[0].points = 5.0
        release.data[0].type = '72'
        release.data[0].scrum_team = 'Some Team'
        release.data[1].status = 3 # In Progress
        release.data[1].points = 2.0
        release.data[1].type = '72'
        release.data[1].scrum_team = None
        for story in release.stories():
            print story.scrum_team
        self.assertEqual(release.wip_by_component()['Some Team']['wip'], 5.0)
        self.assertEqual(release.wip_by_component()['Everything Else']['wip']
            , 2.0)

    def testKanban(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3 # In Progress
        release.data[0].points = 2.0
        release.data[0].type = '72'
        release.data[1].status = 3 # In Progress
        release.data[1].points = 2.0
        release.data[1].type = '72'
        release.data[2].status = 6 # Closed
        release.data[2].points = 2.0
        release.data[2].type = '72'
        self.assertEqual(release.kanban().grid['Core and Builder'][
            '3']['wip'], 4.0)
        self.assertEqual(release.kanban().grid['Core and Builder'][
            '6']['wip'], 2.0)
        self.assertEqual(len(release.kanban().grid['Core and Builder'][
            '3']['stories']),2)

    def testCycleTimeByComponent(self):
        # Not implemented yet
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3 # In Progress
        release.data[0].points = 2.0
        release.data[0].type = '72'
        release.data[1].status = 3 # In Progress
        release.data[1].points = 2.0
        release.data[1].type = '72'
        release.data[2].status = 6 # Closed
        release.data[2].points = 2.0
        release.data[2].type = '72'
        # cycle_times = release.cycle_times()
        # self.assertEqual(cycle_times['Reader'], 1)

    def testGraphKanban(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        jira.request_page = mock_request_page
        release = jira.get_release()
        self.assertEqual(release.graph_kanban(), '.O.')

    def testGraphKanbanByComponent(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        def mock_call_rest(key, expand=['changelog']):
            return json.loads(open(
                'jira/tests/data/rest_changelog.json').read())
        jira.call_rest = mock_call_rest
        jira.request_page = mock_request_page
        release = jira.get_release()
        self.assertEqual(release.graph_kanban('Core and Builder'), '.O.')

    def TestUpperPercentile(self):
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release = Release()
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '1'
        release.data[0].started = D20121201
        release.data[0].resolved = D20121203
        release.data[1].type = '1'
        release.data[1].started = D20121201
        release.data[1].resolved = D20121205
        release.data[2].key = 'NG-1'
        release.data[2].type = '1'
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213
        release.data[3].key = 'NG-2'
        release.data[3].type = '1'
        release.data[3].started = D20121201
        release.data[3].resolved = D20121213
        upper85 = release.upper_percentiles(0.85, ['1'])
        self.assertEqual(len(upper85), 1)
        self.assertEqual(upper85[0].key, 'NG-2')
        upper50 = release.upper_percentiles(0.50, ['1'])
        self.assertEqual(len(upper50), 2)
        self.assertEqual(upper50[0].key, 'NG-1')
        self.assertEqual(upper50[1].key, 'NG-2')

    def TestUpperPercentileNoStories(self):
        release = Release()
        upper50 = release.upper_percentiles(0.50, ['1'])
        self.assertEqual(upper50, [])


class ProjectTest(unittest.TestCase):
    def testObjectCreate(self):
        obj = Project()
        self.assertTrue(obj is not None)

    def testInitializeProject(self):
        project = Project('Name', 'Key', 'Owner')
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

