import unittest
import datetime
from ..model import Story, Release, Projects, Project, Root, Kanban
from ..dao import Jira
from  xml.etree import ElementTree as ET

D20121201 = datetime.date(2012, 12, 1)
D20121202 = datetime.date(2012, 12, 2)
D20121203 = datetime.date(2012, 12, 3)
D20121205 = datetime.date(2012, 12, 5)
D20121208 = datetime.date(2012, 12, 8)
D20121213 = datetime.date(2012, 12, 13)

class RootTest(unittest.TestCase):
    ''' Unit tests for the Root object class
    '''
    def testObjectCreation(self):
        ''' Verify a Root object can be created
        '''
        obj = Root()
        self.assertTrue(obj is not None)

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
        item = tree.find('.//*/item')
        obj = Story(item)
        self.assertEqual(obj.key, 'NG-12805')
        self.assertEqual(obj.type, '1')
        self.assertEqual(obj.started.isoformat(), '2012-11-19T09:35:03')
        self.assertEqual(obj.resolved.isoformat(), '2012-11-27T01:03:48')
        self.assertEqual(obj.cycle_time.days, 7)

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
        jira.request_page = mock_request_page
        release = jira.get_release()
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(len(kanban.stories), 116)
        self.assertEqual(len(kanban.grid['Reader']), 6)

    def testAverageCycleTime(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        jira.request_page = mock_request_page
        release = jira.get_release()
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time(), 5)

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
        self.assertEqual(kanban.stdev_cycle_time(), 3.1622776601683795)

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
        release.data[0].resolved = D20121205
        release.data[0].type = '72'
        release.data[0].points = 2.0
        release.data[1].started = D20121203
        release.data[1].resolved = D20121205
        release.data[1].type = '72'
        release.data[1].points = 6.0
        release.data[2].started = D20121205
        release.data[2].resolved = D20121213
        release.data[2].type = '72'
        release.data[2].points = 1.0
        release.data[3].started = D20121203
        release.data[3].resolved = D20121213
        release.data[3].type = '72'
        release.data[3].points = 3.0
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.cycle_time_per_point(), 2.0)

    def testCycleTimeForComponent(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        jira.request_page = mock_request_page
        release = jira.get_release()
        kanban = Kanban()
        kanban.add_release(release)
        self.assertEqual(kanban.average_cycle_time('Appification'), 2)
        

class ReleaseTests(unittest.TestCase):
    ''' Unit tests for the Release class
    '''

    def testObjectCreation(self):
        obj = Release()
        self.assertTrue(obj is not None)

    def testAddStory(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        self.assertTrue(release.data[0].key == 'NG-12805')

    def testGetStory(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        key = 'NG-12805'
        story = release.get(key)
        self.assertEqual(story.key, key)

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

    def testOnlyStartedStories(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[0].resolved = D20121201
        release.data[2].type = '72'
        release.data[2].resolved = None
        self.assertEqual(len(release.resolved_stories()), 1)

    def testOnlyBugs(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[2].type = '72'
        self.assertEqual(len(release.bugs()), 1)

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
        self.assertTrue(release.total_points() == 0.998)

    def testPointsCompleted(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].type = '72'
        release.data[1].type = '72'
        self.assertTrue(release.total_points() == 0.998)

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
        self.assertEqual(release.std_story_size(), 2.4944382578492941)

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

    def test_only_groomed_stories(self):
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
        release.data[0].status = 3
        release.data[0].type = '72'
        release.data[1].status = 6
        release.data[1].type = '72'
        self.assertTrue(release.wip() == 0.499)

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
        self.assertTrue(release.wip_by_status()['3']['wip'] == 0.499)
        self.assertTrue(sum([v['wip'] for v in release.wip_by_status().values()
            ]) == 0.499)

    def testWipByComponent(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3 # In Progress
        release.data[0].type = '72'
        release.data[1].status = 3 # In Progress
        release.data[1].points = 2.0
        release.data[1].type = '72'
        release.data[2].status = 6 # Closed
        release.data[2].type = '72'
        self.assertEqual(release.wip_by_component()['Reader']['wip'], 2.499)
        self.assertEqual(release.wip_by_component()['Reader']['largest'], 2.0)
        self.assertEqual(len(release.wip_by_component()), 1)

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
        self.assertEqual(release.kanban().grid['Reader']['3']['wip'], 4.0)
        self.assertEqual(release.kanban().grid['Reader']['6']['wip'], 2.0)
        self.assertEqual(len(release.kanban().grid['Reader']['3']['stories']),2)

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
        jira.request_page = mock_request_page
        release = jira.get_release()
        self.assertEqual(release.graph_kanban(), '.Oo')

    def testGraphKanbanByComponent(self):
        jira = Jira()
        def mock_request_page(url, refresh=False):
            return open('jira/tests/data/rss.xml').read()
        jira.request_page = mock_request_page
        release = jira.get_release()
        self.assertEqual(release.graph_kanban('Core'), '_O.')

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

