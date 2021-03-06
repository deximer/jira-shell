import argparse
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release

class Command(BaseCommand):
    help = 'List the teams with commitments to the release'
    usage = 'teams'

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('dir', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        if args.dir:
            container = jira.cache.get_by_path(args.dir)
        else:
            container = jira.cache.get_by_path(jira.cache.cwd)
        if not isinstance(container, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        teams = container.tasked_teams()
        print 'Team:'.ljust(25), '   Issues:', 'Max PCE:'
        for team in sorted(teams.keys()):
            print team.ljust(25), ': ', str(teams[team]).ljust(7), '%' + str(container.kanban().process_cycle_efficiency(component=team))
        print 'Total:', str(len(teams))
