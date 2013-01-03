import getopt
import curses
from commands.base import BaseCommand

class Command(BaseCommand):
    help = 'List issues in a release'
    usage = 'ls'

    def run(self, jira, args):
        opts, args = getopt.getopt(args, '1:', ())
        print 'Retrieving data...'
        self.refresh_data(jira, False)
        for story in self.release.data:
            team = story.scrum_team
            if not team:
                team = 'Everything Else'
            print team[:18].ljust(18), \
                  str(story.points).ljust(5), \
                  str(story.status).ljust(5), \
                  str(self.release.kanban().contingency_outside(story.key)).ljust(5), story.title[:43]

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
