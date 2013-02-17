import argparse
import datetime
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Low level local cache database maintenance'
    usage = 'db [command]'
    examples = '''    db pack
    '''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('commands', nargs='*')
        try:
            args = parser.parse_args(args)
        except:
            return

        for command in args.commands:
            if command not in ['pack']:
                print 'db.%s command not allowed' % command
                continue
            print 'Executing db.%s' % command
            getattr(jira.cache.db, command)()
            print 'Finished db.%s' % command
