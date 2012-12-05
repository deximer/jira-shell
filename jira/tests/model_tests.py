import unittest
from ..model import Story
from ..model import Release
from  xml.etree import ElementTree as ET

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
        print release.wip_by_status()
        self.assertTrue(release.wip_by_status()['3'] == 0.499)
        self.assertTrue(sum([v for v in release.wip_by_status().values()]) \
            == 0.499)

    def testWipByComponent(self):
        release = Release()
        xml = open('jira/tests/data/rss.xml').read()
        tree = ET.fromstring(xml)
        item = tree.find('.//*/item')
        release.add(Story(item))
        release.add(Story(item))
        release.data[0].status = 3 # In Progress
        release.data[1].status = 6 # Closed
        self.assertTrue(release.wip_by_component()['Reader'] == 0.499)
        self.assertTrue(len(release.wip_by_component()) == 1)


