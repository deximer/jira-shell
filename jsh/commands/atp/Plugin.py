import getopt
import argparse
import sets
from zope.interface import Interface, implements
from zope.component import adapts
from zope.component import getGlobalSiteManager
from repoze.folder.interfaces import IFolder
from persistent.list import PersistentList
from ..base import BaseCommand
from interfaces import IRelease, IStory, IProject, ILinks, IIssues
from model import humanize

gsm = getGlobalSiteManager()

class Command(BaseCommand):
    help = 'Provide estimate delivery dates.'
    usage = 'atp issue_id'
    options_help = ''''''
    examples = '''    atp POOL-1
    '''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('select', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        container = jira.cache.get_by_path(jira.cache.cwd)
        kanban = container.kanban()
        stdev = kanban.stdev_cycle_time()
        story = container.get(args.select)
        depth = kanban.rank_depth(str(story.status), story.key)
        cycle_time = 0
        if story.cycle_time:
            cycle_time = story.cycle_time
        days = int(round((kanban.average_atp() * depth) - cycle_time, 0))
        print days, 'days'

