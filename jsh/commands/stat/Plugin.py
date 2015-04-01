import curses
import argparse
from termcolor import cprint
from ..base import BaseCommand
from model import Release, KANBAN, humanize

class Command(BaseCommand):
    help = 'Print details of specified issues'
    usage = 'stat <issue_id>'
    examples = '''    stat NG-12345
    '''

    def run(self, jira, args):
        if not args:
            print 'Error: you must specify an issue key'
            return
        elif len(args) > 1:
            print 'Error: please supply a single id'
            return
        parser = argparse.ArgumentParser()
        parser.add_argument('key')
        args = parser.parse_args(args)
        story = jira.cache.get(args.key)
        if not story:
            print 'Error: story key %s not found' % args.key
            return
        story = story[0]
        self.release = jira.cache.get_by_path(jira.cache.cwd[:3])
        kanban = self.release.kanban()
        if not story:
            print 'No story matching key: %s' % args.key
            return
        print 'ID:', story.key
        print 'Release:', ', '.join(story.fix_versions)
        print 'Type:', story.type
        print 'Title:', story.title
        print 'Team:', story.scrum_team
        if hasattr(story, 'labels'):
            print 'Labels:', story.labels
        print 'Developer:', story.developer
        print 'Points:', story.points
        print 'Status:', humanize(story.status)
        print 'Order:', kanban.rank_depth(story)
        print 'Created:', story.created
        print 'Started:', story.started
        print 'Updated:', story.updated
        print 'Resolved:', story.resolved
        print 'Resolution:', story.resolution
        print 'Cycle Time:', story.cycle_time
        print 'Aggregate Cycle Time:', story.aggregate_cycle_time
        avg_ct = self.release.kanban().average_cycle_time()
        ct = story.cycle_time
        sq_ct = self.release.kanban().squared_cycle_times()
        if ct and avg_ct and sq_ct:
            spread = ct - avg_ct
            variance = spread * spread
            percent_variance = variance / sq_ct
            print '% Variance:', '%' + str(round(percent_variance, 4) * 100)
        else:
            print '% Variance:', 'nan'
        print 'ATP:', kanban.atp(story)
        print 'Contingency:'
        print '    Inside:', kanban.contingency_inside(story.key)
        print '    Average:', kanban.contingency_average(story.key)
        print '    Outside:', kanban.contingency_outside(story.key)
        if story.history.data:
            print
            print 'Transition Log:'
            previous_date = None
            for t in story.history.all:
                backflow = ''
                skipped = ''
                if t[1] in KANBAN and t[2] in KANBAN:
                    steps = KANBAN.index(t[2]) - KANBAN.index(t[1])
                    if steps == 2 and t[1] == 10089:
                        skipped = ''
                    elif steps > 1:
                        if t[1] == 10089 or t[1] == 1:
                            steps -= 1
                        skipped = '-> skipped %d' % (steps - 1)
                    if KANBAN.index(t[1]) > KANBAN.index(t[2]):
                        if previous_date and \
                            (t[0] - previous_date).total_seconds() > 300:
                            backflow = '<- backflow'
                previous_date = t[0]
                if not t[3]:
                    days = ''.ljust(3)
                else:
                    days = str(t[3]).ljust(3)
                name = t[4][:17].ljust(18) if t[4] else ''.ljust(18)
                color = 'black'
                if humanize(t[2]) == 'Start':
                    color = 'green'
                if humanize(t[2]) == 'Closd':
                    color = 'red'
                if color == 'black':
                    print '  %s, [%s], %s, %s -> %s %s' % (t[0], days, name,
                        humanize(t[1]).ljust(5), humanize(t[2]).ljust(5), \
                        backflow or skipped)
                else:
                    cprint('  %s, [%s], %s, %s -> %s %s' % (t[0], days, name,
                        humanize(t[1]).ljust(5), humanize(t[2]).ljust(5), \
                        backflow or skipped), color)
        print
        for direction in ['out', 'in']:
            print 'Links %s:' % direction
            for links in story['links'][direction]:
                print '  %s:' % links
                for link in story['links'][direction][links].values():
                    print '    %s %s %s' % (link.key, link.type,
                        link.title[:60])
