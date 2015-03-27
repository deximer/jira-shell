from ..base import BaseCommand

STATUS_CODES = {
    '1': 'New  ',
    '6': 'Closd',
    '10024': 'Ready',
    '10002': 'Start',
    '10004': 'PeerR',
    '10014': 'NeedA',
    '10005': 'Test ',
    '10127': 'QeApp',
    '10128': 'PoApp',
}

ISSUE_TYPES = {
    '1' : 'Development Bug',
    '65': 'Configuration',
    '71': 'Epic',
    '72': 'Story',
    '78': 'Production Bug',
    '101': 'Feature',
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
