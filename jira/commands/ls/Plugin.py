import getopt
import argparse
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'List issues in a release'
    usage = 'ls'
    options_help = '    -s : Show only issues with the specified status'
    examples = '    ls -s 3'

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', type=int)
        parser.add_argument('-t')
        args = parser.parse_args(args)
        self.refresh_data(jira, False)
        print 'Team:'.ljust(18), \
              'Pts:'.ljust(5), \
              'Stat:'.ljust(5), \
              'CT:'.ljust(5), \
              'Type:'.ljust(5), \
              'Title:'
        issues = 0
        points = 0
        for story in sorted(self.release.data, key=lambda x: x.scrum_team):
            if args.s and story.status != args.s:
                continue
            if args.t and story.type != args.t:
                continue
            team = story.scrum_team
            if not team:
                team = 'Everything Else'
            print team[:18].ljust(18), \
                  str(story.points).ljust(5), \
                  str(story.status).ljust(5), \
                  str(story.cycle_time).ljust(5), str(story.type).ljust(5), \
                  story.title[:37]
            issues += 1
            if story.points:
                points += story.points
        print 'Total Issues: %d, Total Points: %d' % (issues, points)

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
