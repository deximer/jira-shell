from ..base import BaseCommand

STATUS_CODES = {
    '1': 'Open',
    '3': 'In Progress',
    '4': 'Reopened',
    '6': 'Closed',
    '10036': 'Verified',
    '10089': 'Ready',
    '10090': 'Completed',
    '10092': 'QA Active',
    '10104': 'QA Ready'
}

ISSUE_TYPES = {
    '1' : 'Development Bug',
    '72': 'Story',
    '78': 'Production Bug'
}

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
