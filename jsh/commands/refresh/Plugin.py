import argparse
import datetime
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Refresh the local cache of Jira data'
    usage = 'refresh [release_key [...]] -a -l -n -t [time_range]'
    options_help = '''    -a : refresh all issues
    -l : refresh link graph (takes a lot longer)
    -n : only add missing issues, skip updates
    -t : time range (e.g. 3d)'''

    def run(self, jira, args):
        start = datetime.datetime.now()
        parser = argparse.ArgumentParser()
        parser.add_argument('boards', nargs='*')
        parser.add_argument('-a', action='store_true', required=False)
        parser.add_argument('-l', action='store_true', required=False)
        parser.add_argument('-n', action='store_true', required=False)
        parser.add_argument('-t', nargs='*', required=False)
        try:
            args = parser.parse_args(args)
        except:
            print 'Error parseing arguments'
            return
        if args.a:
            self.refresh_data(jira, all_issues=True)
        time_range = None
        if args.t:
            time_range = '-' + args.t[0]
        if not args.boards:
            folder = jira.cache.get_by_path(jira.cache.cwd)
            if hasattr(folder, 'key'):
                args.boards.append(folder)
        self.refresh_data(jira, args.boards, args.l, time_range, args.a, args.n)
        elapsed = datetime.datetime.now() - start
        print 'Cache refreshed in about %d minutes' \
            % round(elapsed.seconds/60.0, 1)
