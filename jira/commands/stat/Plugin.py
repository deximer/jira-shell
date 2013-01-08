import curses
import argparse
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Print details of specified issues'
    usage = 'stat [issue_id]'
    examples = '''    stat 12345
    stat NG-12345
    '''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('key')
        args = parser.parse_args(args)
        self.refresh_data(jira, False)
        kanban = self.release.kanban()
        story = self.release.get(args.key)
        print 'ID: ', story.key
        print 'Title: ', story.title
        print 'Type: ', story.type
        print 'Team: ', story.scrum_team
        print 'Points: ', story.points
        print 'Status: ', story.status
        print 'Started:', story.started
        print 'Resolved:', story.resolved
        print 'Cycle Time:', story.cycle_time
        print 'Contingincy:'
        print '    Inside:', kanban.contingency_inside(story.key)
        print '    Average:', kanban.contingency_average(story.key)
        print '    Outside:', kanban.contingency_outside(story.key)
        print 'Components:'
        for component in story.components:
            print '   ', component

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
