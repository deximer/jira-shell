import argparse
import pdb
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Activate the Python debugger'
    usage = 'debug'

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('dir', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        cwd = jira.cache.get_by_path(jira.cache.cwd)
        cache = jira.cache
        issues = jira.cache.data['issues']
        print
        print 'Helper vars set: cwd cache jira issues'
        print
        pdb.set_trace()
