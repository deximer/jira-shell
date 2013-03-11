import getopt
import argparse
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Change Directory'
    usage = 'cd [container]'
    examples = '''    cd 2.6'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('dir', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        if not args.dir or (len(args.dir) == 1 and args.dir[0] == '/'):
            jira.cache.cwd = ['/']
            return
        import copy
        backup_cwd = copy.copy(jira.cache.cwd)
        for dir in args.dir.split('/'):
            if dir == '..':
                if len(jira.cache.cwd) > 1:
                    del jira.cache.cwd[-1]
            elif dir == '':
                jira.cache.cwd = ['/']
            else:
                jira.cache.cwd.append(dir)
                try:
                    obj = jira.cache.get_by_path(jira.cache.cwd)
                except KeyError:
                    print 'Error: No such path'
                    jira.cache.cwd = backup_cwd

