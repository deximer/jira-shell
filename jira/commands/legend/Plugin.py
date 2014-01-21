from ..base import BaseCommand

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
    STATUS_CODES = {}
    ISSUE_TYPES = {}

    def run(self, jira, args):
        self.fetch_status_codes(jira)
        print 'Status codes:'
        for key in sorted(self.STATUS_CODES.keys(), key=lambda val: int(val)):
            print key.ljust(6) + ':', self.STATUS_CODES[key]
        print
        self.fetch_issue_types(jira)
        print 'Story types:'
        for key in sorted(ISSUE_TYPES.keys(), key=lambda val: int(val)):
            print key.ljust(6) + ':', ISSUE_TYPES[key]


    def fetch_status_codes(self, jira):
        if len(self.STATUS_CODES) != 0:
            return
        status_codes = jira.call_api('status')
        for status in status_codes:
            self.STATUS_CODES[status['id']] = status['name']


    def fetch_issue_types(self, jira):
        if len(self.ISSUE_TYPES) != 0:
            return
        issue_types = jira.call_api('issuetype')
        for issue_type in issue_types:
            self.ISSUE_TYPES[issue_type['id']] = issue_type['name']