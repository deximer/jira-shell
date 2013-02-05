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
    '65': 'Configuration',
    '71': 'Epic',
    '72': 'Story',
    '78': 'Production Bug',
    '156': 'Spike'
}

class Command(BaseCommand):
    help = 'List the meaning of the various codes'
    usage = 'legend'

    def run(self, jira, args):
        print 'Status codes:'
        for key in sorted(STATUS_CODES.keys()):
            print key.ljust(6) + ':', STATUS_CODES[key]
        print
        print 'Story types:'
        for key in sorted(ISSUE_TYPES.keys()):
            print key.ljust(6) + ':', ISSUE_TYPES[key]
