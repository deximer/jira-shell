from ..base import BaseCommand

class Command(BaseCommand):
    help = 'List the teams with commitments to the release'
    usage = 'teams'

    def run(self, jira, args):
        self.refresh_data(jira, False)
        teams = self.release.tasked_teams()
        for team in teams:
            print '%s: %d' % (team, teams[team])
