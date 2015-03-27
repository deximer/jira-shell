import getopt
import argparse
import sets
import datetime
from dateutil.rrule import DAILY, SA, SU, rrule
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
        story = container.get(args.select)
        days = int(round(kanban.average_atp(story), 0))
        now = datetime.datetime.now()
        atp = now + datetime.timedelta(days)
        print str(atp)[:10], days, 'days'

