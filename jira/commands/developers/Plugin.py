import argparse
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'List the developers working on the release'
    usage = 'developers'

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
        developers = container.developers()
        for developer in developers:
            print '%s: %d' % (developer, developers[developer])
