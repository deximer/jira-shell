import argparse
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release, humanize

class Command(BaseCommand):
    help = 'View all transiions in a board'
    usage = '''transitions [-a] [-s [state]] [-t issue_type] [-p priority]
    transitions
    transitions -p Critical
    transitions -a -p Critical -t 7 1
    '''
    options_help = '''    -a: List all transitions
    -p: List only specified priorities
    -t: List only specified issue types
    '''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('dir', nargs='?')
        parser.add_argument('-a', action='store_true', required=False)
        parser.add_argument('-p', nargs='*', required=False)
        parser.add_argument('-s', nargs='*', required=False)
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

        if args.s:
            transitions = [t for t in transitions if humanize(t[3]) ==args.s[0]]
            args.a = True

        if args.a:
            print 'Date:'.ljust(19), 'From:'.ljust(8), 'To:'.ljust(5), 'Days:', 'ID:'
            for transition in transitions:
                print transition[1] \
                    , humanize(transition[2]).ljust(5) \
                    , '->' \
                    , humanize(transition[3]).ljust(5) \
                    , str(transition[4]).ljust(5) \
                    , transition[0].key

        if args.s == []:
            results = {}
            for transition in transitions:
                state = str(humanize(transition[3]))
                if state in results.keys():
                    results[state] += 1
                else:
                    results[state] = 1
            ordered = []
            for key in results:
                ordered.append((key, results[key]))
            ordered.sort(key=lambda x:x[1])
            for item in ordered:
                print item[0].ljust(5), ':', item[1]

        print
        print 'Total :', len(transitions)
        if not transitions:
            return
        print 'First :', transitions[0][1], transitions[0][0].key 
        print 'Last  :', transitions[-1][1], transitions[-1][0].key
        print 'Spread:', (transitions[-1][1] - transitions[0][1]).days, 'days'

