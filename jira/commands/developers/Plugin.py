from ..base import BaseCommand

class Command(BaseCommand):
    help = 'List the developers working on the release'
    usage = 'developers'

    def run(self, jira, args):
        self.refresh_data(jira, False)
        developers = self.release.developers()
        for developer in developers:
            print '%s: %d' % (developer, developers[developer])

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
