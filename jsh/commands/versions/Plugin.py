import argparse
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release
import jira as JIRA

class Command(BaseCommand):
    help = 'Various ways of looking at issue versions'
    usage = 'versions'

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
        versions = container.unique_versions()
        print 'CT:'.ljust(5), 'Version:'
        for version in sorted(versions):
            days = container.cycle_time_for_version(version)
            if not days:
                days = ''
            else:
                days = str(days)
            print days.ljust(5), version
