import argparse
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release
import jira as JIRA

class Command(BaseCommand):
    help = 'Various ways of looking at issue labels'
    usage = 'labels'
    option_help = '    -a : show only active labels'

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('dir', nargs='?')
        parser.add_argument('-a', action='store_true', required=False)
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
        labels = container.unique_labels()
        print 'CT:'.ljust(5), 'Label:'
        for label in sorted(labels):
            days = container.cycle_time_for_label(label)
            if args.a:
                stories = container.stories_for_labels([label])
                if not [s for s in stories if s.status != 6]:
                    continue
            if not days:
                days = ''
            else:
                days = str(days)
            print days.ljust(5), label
