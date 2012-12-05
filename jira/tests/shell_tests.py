import unittest
from ..shell import Story
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
        print item
        obj = Story(item)
        self.assertTrue(obj.key == 12345)
