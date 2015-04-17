import argparse
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release
import jira as JIRA

class Command(BaseCommand):
    help = 'Various ways of looking at issue components'
    usage = 'components'

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
        components = container.unique_components()
        print 'CT:'.ljust(5), 'Components:'
        for component in sorted(components):
            days = container.cycle_time_for_component(component)
            if not days:
                days = ''
            else:
                days = str(days)
            print days.ljust(5), component
