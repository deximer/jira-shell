import getopt
import curses

class Command(object):
    def run(self, jira, args):
        opts, args = getopt.getopt(args, '1:', ())
        self.refresh_data(jira, False)
        teams = self.release.tasked_teams()
        for team in teams:
            print '%s: %d' % (team, teams[team])

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
