import curses
import argparse
from ..base import BaseCommand
from model import Release, KANBAN

class Command(BaseCommand):
    help = 'Print details of specified issues'
    usage = 'stat <issue_id>'
    examples = '''    stat 12345
    stat NG-12345
    '''

    def run(self, jira, args):
        if not args:
            print 'Error: you must specify an issue key'
            return
        parser = argparse.ArgumentParser()
        parser.add_argument('key')
        args = parser.parse_args(args)
        self.release = jira.cache.get_by_path(jira.cache.cwd)
        if not isinstance(self.release, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        kanban = self.release.kanban()
        story = self.release.get(args.key)
        if not story:
            print 'No story matching key: %s' % args.key
            return
        print 'ID:', story.key
        print 'Title:', story.title
        print 'Team:', story.scrum_team
        print 'Developer:', story.developer
        print 'Type:', story.type
        print 'Points:', story.points
        print 'Status:', story.status
        print 'Created:', story.created
        print 'Started:', story.started
        print 'Resolved:', story.resolved
        print 'Cycle Time:', story.cycle_time
        print 'Fix Versions:', ', '.join(story.fix_versions)
        print 'Contingency:'
        print '    Inside:', kanban.contingency_inside(story.key)
        print '    Average:', kanban.contingency_average(story.key)
        print '    Outside:', kanban.contingency_outside(story.key)
        print 'Transition Log:'
        for t in story.history.data:
            backflow = ''
            if KANBAN.index(t[1]) > KANBAN.index(t[2]):
                backflow = ' <- backflow'
            print '    %s, %s -> %s %s' % (t[0], t[1], t[2], backflow)
        #print 'Outward Links:'
        #for link in story.links.data:
        #    print '    %s %s' % (link.key, link.title[:70])
