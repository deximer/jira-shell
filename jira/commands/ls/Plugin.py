import getopt
import argparse
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'List issues in a release'
    usage = 'ls [team] [-s status [status...]] [-t issue_type [issue_type...]]'
    options_help = '''    -s : Show only issues with the specified status
    -t : Show only issues of the specified type
    '''
    examples = '''    ls
    ls App
    ls Math -s 3 -t 72'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', nargs='*', type=int, required=False)
        parser.add_argument('-t', nargs='*', required=False)
        parser.add_argument('team', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
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
            if args.s and story.status not in args.s:
                continue
            if args.t and story.type not in args.t:
                continue
            if not story.scrum_team:
                story.scrum_team = 'Everything Else'
            if args.team and story.scrum_team[:len(args.team)] != args.team:
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
