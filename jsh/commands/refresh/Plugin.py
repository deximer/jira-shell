import argparse
import datetime
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Refresh the local cache of Jira data'
    usage = 'refresh [release_key [...]]'
    options_help = '''    -l : refresh link graph (takes a lot longer)'''

    def run(self, jira, args):
        start = datetime.datetime.now()
        parser = argparse.ArgumentParser()
        parser.add_argument('releases', nargs='*')
        parser.add_argument('-l', action='store_true', required=False)
        try:
            args = parser.parse_args(args)
        except:
            return
        if not args.l:
            print 'Ignoring links...'
        else:
            print 'Traversing link graph...'
        self.refresh_data(jira, args.releases, args.l, '-8d')
        elapsed = datetime.datetime.now() - start
        print 'Cache refreshed in about %d minutes' \
            % round(elapsed.seconds/60.0, 1)
