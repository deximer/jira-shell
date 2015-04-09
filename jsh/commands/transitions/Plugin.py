import argparse
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release

class Command(BaseCommand):
    help = 'View all transiions in a board'
    usage = 'transitions'

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
        transitions = container.all_transitions()
        print 'Total :', len(transitions)
        print 'First :', transitions[0][1], transitions[0][0].key 
        print 'Last  :', transitions[-1][1], transitions[-1][0].key
        print 'Spread:', (transitions[-1][1] - transitions[0][1]).days, 'days'
