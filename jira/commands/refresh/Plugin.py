import argparse
import datetime
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Refresh the local cache of Jira data'
    usage = 'refresh [release_key [...]]'

    def run(self, jira, args):
        start = datetime.datetime.now()
        parser = argparse.ArgumentParser()
        parser.add_argument('releases', nargs='*')
        try:
            args = parser.parse_args(args)
        except:
            return
        self.refresh_data(jira, args.releases)
        elapsed = datetime.datetime.now() - start
        print 'Cache refreshed in about %d minutes' \
            % round(elapsed.seconds/60.0, 1)
