from ..base import BaseCommand


class Command(BaseCommand):
    help = 'List the meaning of the various codes'
    usage = 'legend'

    def run(self, jira, args):
        status_codes = jira.fetch_meta('status')
        print 'Status codes:'
        for key in sorted(status_codes.keys(), key=lambda val: int(val)):
            print key.ljust(6) + ':', status_codes[key]
        print
        issue_types = jira.fetch_meta('issuetype')
        print 'Story types:'
        for key in sorted(issue_types.keys(), key=lambda val: int(val)):
            print key.ljust(6) + ':', issue_types[key]
