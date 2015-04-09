import getopt
import argparse
try:
    from ...dao import Jira
except:
    from dao import Jira
try:
    from ...model import Story, History, Release, Project
except:
    from model import Story, History, Release, Project
from datetime import datetime
from random import random
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Fake Data'
    usage = 'fake'
    examples = '''    fake'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('dir', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
	project = Project('fP1', 'Fake Project 1', 'ted')
	if not 'fP1' in Jira.cache.data:
	    Jira.cache.data['fP1'] = project
            docid = Jira.cache.document_map.add(
                ['jira', '', '', project.key]
            )
            Jira.cache.catalog.index_doc(docid, project)
	release = Release('f1.0')
	if not 'f1.0' in Jira.cache.data:
	    Jira.cache.data['fP1']['f1.0'] = release
	for id in range(1, 20):
	    data = {}
	    data['key'] = 'fS-%d' % id
	    data['title'] = 'Story %s' % id
	    data['points'] = [1,2,3,5,8,13,21][int(random() * 7)]
	    data['ready'] = datetime(2015, 1, 1)
            started = int(random() * 15 + 1)
	    data['started'] = datetime(2015, 1, started)
            if random() > 0.4:
                month = 1
                resolved = started + int(random() * data['points'] * 2)
                if resolved > 30:
                    month = 2
                    resolved = resolved - 30
	        data['resolved'] = datetime(2015, month, resolved)
	    data['dev'] = ['ann', 'nic', 'sam', 'mia'][int(random() * 4)]
            story = make_story(data)
	    release.add_story(story)
            docid = Jira.cache.document_map.add(
                ['jira', 'fP1', 'f1.0', story.key]
            )
            Jira.cache.catalog.index_doc(docid, story)
        print 'Created fake project "fP1"'

def make_story(data):
    story = Story()
    story.key = data['key']
    story.title = data['title']
    story.root_cause = ''
    story.root_cause_details = ''
    story.developer = data['dev']
    story.components = []
    story.history = History()
    story.points = data['points']
    story.created = datetime(15,1,1)
    story.scrum_team = 'Team 1'
    story.history.data.append((data['ready'], 1, 10089, None, 'Jane Powner'))
    story.history.data.append((data['started'], 10089, 3, None, 'Sarah Conner'))
    story.status = 3
    if 'resolved' in data:
        story.history.data.append((data['resolved'],3, 6, None, 'Ellen Ripley'))
        story.status = 6
    story.type = '72'
    story.fix_versions = ['2.0']
    return story
