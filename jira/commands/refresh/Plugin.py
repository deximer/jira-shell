import getopt
import curses
from commands.base import BaseCommand

class Command(BaseCommand):
    help = 'Refresh the local cache of Jira data'
    usage = 'refresh'

    def run(self, jira, args):
        opts, args = getopt.getopt(args, '1:', ())
        print 'Retrieving data...'
        self.refresh_data(jira, True)
        print 'Cache refreshed'

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
