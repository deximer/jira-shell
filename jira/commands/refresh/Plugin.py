import argparse
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Refresh the local cache of Jira data'
    usage = 'refresh [release_key [...]]'

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('releases', nargs='*')
        try:
            args = parser.parse_args(args)
        except:
            return
        self.refresh_data(jira, args.releases)
        print 'Cache refreshed'
