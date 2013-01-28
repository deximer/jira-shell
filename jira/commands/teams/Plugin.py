import argparse
from ..base import BaseCommand

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
        print container
        teams = container.tasked_teams()
        for team in teams:
            print '%s: %d' % (team, teams[team])
