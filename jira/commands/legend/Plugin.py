from ..base import BaseCommand
from model import STATUS_CODES, ISSUE_TYPES

class Command(BaseCommand):
    help = 'List the meaning of the various codes'
    usage = 'legend'

    def run(self, jira, args):
        print 'Status codes:'
        for key in STATUS_CODES:
            print key.ljust(6) + ':', STATUS_CODES[key]
        print
        print 'Story types:'
        for key in ISSUE_TYPES:
            print key.ljust(6) + ':', ISSUE_TYPES[key]
