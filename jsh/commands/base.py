import getopt
import curses

class BaseCommand(object):
    help = ''
    options_help = ''
    examples = ''

    def run(self, jira, args):
        pass # override in command

    def refresh_data(self, jira, boards=[], links=True, time_range=None,
        all_issues=False, add_only=False, issue_types=[]):
        self.release = jira.refresh_cache(boards, links, time_range, all_issues
            , add_only, issue_types)
