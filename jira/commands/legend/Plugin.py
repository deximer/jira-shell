from ..base import BaseCommand

LEGEND_TYPES = {
    'status': 'Status codes',
    'issuetype': 'Issue types'
}


class Command(BaseCommand):
    help = 'List the meaning of the various codes'
    usage = 'legend [type]'
    options_help = '''type is one of "status" or "issuetype"'''

    def print_meta(self, jira, type):
        codes = jira.fetch_meta(type)
        print LEGEND_TYPES[type] + ':'
        for key in sorted(codes.keys(), key=lambda val: int(val)):
            print key.ljust(6) + ':', codes[key]
        print

    def run(self, jira, args):
        if len(args) == 0:
            types = LEGEND_TYPES.keys()
        else:
            types = args

        for type in types:
            self.print_meta(jira, type)
