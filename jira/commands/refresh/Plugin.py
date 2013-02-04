from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Refresh the local cache of Jira data'
    usage = 'refresh'

    def run(self, jira, args):
        self.refresh_data(jira, True)
        print 'Cache refreshed'
