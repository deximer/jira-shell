import unittest
from ..model import Story, Release, Projects, Project, Root
from ..dao import Jira
from  xml.etree import ElementTree as ET

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
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        obj = Story(item)
        print obj.key
        self.assertTrue(obj.key == 'NG-12805')

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

    def testTotalStories(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        self.assertTrue(release.total_stories() == 1)
        release.add(Story(item))
        self.assertTrue(release.total_stories() == 2)

    def testTotalPoints(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        self.assertTrue(release.total_points() == 0.998)

    def testPointsCompleted(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        self.assertTrue(release.total_points() == 0.998)

    def test_average_story_size(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[1].points = 4.0
        release.data[2].points = 8.0
        self.assertEqual(release.average_story_size(), 4.666666666666667)

    def test_average_story_size_null_values(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[1].points = None
        release.data[2].points = 8.0
        self.assertEqual(release.average_story_size(), 5.0)

    def test_std_story_size(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].points = 2.0
        release.data[1].points = 4.0
        release.data[2].points = 8.0
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
        release.data[1].points = None
        release.data[2].points = 3.0
        self.assertEqual(len(release.only_groomed_stories()), 2)

    def testStoriesInProcess(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3
        release.data[1].status = 10092
        release.data[2].status = 6
        self.assertEqual(release.stories_in_process(), 2)

    def testWip(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3
        release.data[1].status = 6
        self.assertTrue(release.wip() == 0.499)

    def testWipByStatus(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3 # In Progress
        release.data[1].status = 6 # Closed
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
        release.data[1].status = 3 # In Progress
        release.data[1].points = 2.0
        release.data[2].status = 6 # Closed
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
        release.data[1].status = 3 # In Progress
        release.data[1].points = 2.0
        release.data[2].status = 6 # Closed
        release.data[2].points = 2.0
        self.assertEqual(release.kanban()['Reader']['3']['wip'], 4.0)
        self.assertEqual(release.kanban()['Reader']['6']['wip'], 2.0)

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

