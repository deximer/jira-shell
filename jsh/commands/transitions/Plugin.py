import argparse
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release, humanize

class Command(BaseCommand):
    help = 'View all transiions in a board'
    usage = '''transitions [-a] [-t issue_type] [-p priority]
    transitions
    transitions -p Critical
    transitions -a -p Critical -t 7 1
    '''
    options_help = '''    -a: List all transitions for all stories
    -p: List only specified priorities
    -t: List only issue types
    '''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('dir', nargs='?')
        parser.add_argument('-a', action='store_true', required=False)
        parser.add_argument('-p', nargs='*', required=False)
        parser.add_argument('-t', nargs='*', required=False)
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

        transitions = container.all_transitions(args.t)
        if args.p:
            transitions = [t for t in transitions
                if t[0].priority in args.p]

        if args.a:
            for transition in transitions:
                print transition[1] \
                    , humanize(transition[2]).ljust(5) \
                    , '->' \
                    , humanize(transition[3]).ljust(5) \
                    , str(transition[4]).ljust(5) \
                    , transition[0].key

        print 'Total :', len(transitions)
        print 'First :', transitions[0][1], transitions[0][0].key 
        print 'Last  :', transitions[-1][1], transitions[-1][0].key
        print 'Spread:', (transitions[-1][1] - transitions[0][1]).days, 'days'

