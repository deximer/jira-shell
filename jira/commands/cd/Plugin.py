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
            import pdb; pdb.set_trace()
        except:
            return
        import copy
        backup_cwd = copy.copy(jira.cache.cwd)
        for dir in args.dir.split('/'):
            if dir == '..':
                if len(jira.cache.cwd) > 1:
                    del jira.cache.cwd[-1]
            else:
                jira.cache.cwd.append(dir)
                try:
                    obj = jira.cache.get_by_path(jira.cache.cwd)
                except KeyError:
                    print 'Error: No such path'
                    jira.cache.cwd = backup_cwd

