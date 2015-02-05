import getopt
import curses

class BaseCommand(object):
    help = ''
    options_help = ''
    examples = ''

    def run(self, jira, args):
        pass # override in command

    def refresh_data(self, jira, releases, links=True):
        self.release = jira.refresh_cache(releases, links=links)
