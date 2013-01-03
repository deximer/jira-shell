import getopt
import curses
from commands.base import BaseCommand

class Command(BaseCommand):
    help = 'Print details of specified issues'
    usage = 'stat [issue_id]'
    examples = '''    stat 12345
    stat NG-12345
    '''

    def run(self, jira, args):
        opts, args = getopt.getopt(args, '1:', ())
        self.refresh_data(jira, False)
        story = self.release.get(args[0])
        print 'ID: ', story.key
        print 'Title: ', story.title
        print 'Status: ', story.status

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
