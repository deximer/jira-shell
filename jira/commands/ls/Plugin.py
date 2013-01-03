import getopt
from commands.base import BaseCommand

class Command(BaseCommand):
    help = 'List issues in a release'
    usage = 'ls'

    def run(self, jira, args):
        opts, args = getopt.getopt(args, '1:', ())
        self.refresh_data(jira, False)
        print 'Team:'.ljust(18), \
              'Pts:'.ljust(5), \
              'Stat:'.ljust(5), \
              'CT:'.ljust(5), \
              'Title:'
        for story in self.release.data:
            team = story.scrum_team
            if not team:
                team = 'Everything Else'
            print team[:18].ljust(18), \
                  str(story.points).ljust(5), \
                  str(story.status).ljust(5), \
                  str(story.cycle_time).ljust(5), story.title[:43]

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
