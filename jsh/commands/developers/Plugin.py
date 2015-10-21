import argparse
from ..base import BaseCommand
try:
    from ...model import Release, fstory, fclean
except:
    from model import Release, fstory, fclean

class Command(BaseCommand):
    help = 'List the developers working on the release'
    usage = 'developers'

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('dir', nargs='?')
        parser.add_argument('-s', nargs='*', required=False)
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
        developers = container.developers()
        if args.s:
            stories = developers[args.s[0]]
        print 'Developer:'.ljust(25), '   Stories: Agg CT: Avg CT:'
        for developer in sorted(developers.keys()):
            if not developer:
                continue
            stories = fclean(fstory(developers[developer]))
            ct = sum([s.cycle_time for s in stories if s.cycle_time])
            if ct:
                act = ct / len(stories)
            else:
                act = 0
            print developer.ljust(25), ': ', str(len(developers[developer])).ljust(8), str(ct).ljust(7), act
        print 'Total:', str(len(developers))
