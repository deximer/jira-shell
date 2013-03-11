import argparse
import datetime
import transaction
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

        if args.commands and args.commands[0] == 'del':
            if len(args.commands) > 1:
                for obj in args.commands[1:]:
                    transaction.begin()
                    del jira.cache.data[''.join(jira.cache.cwd[1:])][obj]
                    transaction.commit()
                    print 'Deleted: %s' % \
                        (''.join(jira.cache.cwd[1:]) + '/' + obj)
            return

        for command in args.commands:
            if command not in ['pack']:
                print 'db.%s command not allowed' % command
                continue
            print 'Executing db.%s' % command
            getattr(jira.cache.db, command)()
            print 'Finished db.%s' % command
