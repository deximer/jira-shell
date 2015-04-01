import argparse
from ..base import BaseCommand
from model import Release

class Command(BaseCommand):
    help = 'Various ways of looking at issue labels'
    usage = 'labels'

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
        labels = container.unique_labels()
        print 'CT:'.ljust(5), 'Label:'
        for label in sorted(labels):
            days = container.cycle_time_for_label(label)
            if not days:
                days = ''
            else:
                days = str(days)
            print days.ljust(5), label
