import argparse
import copy
from ..base import BaseCommand
from model import Release

class Command(BaseCommand):
    help = 'Report on the current release'
    usage = 'report [team]'
    options_help = '''    -d : report on a specific developer'''
    exmamples = '''    report
    report App'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        parser.add_argument('-d', nargs='*', required=False)
        try:
            args = parser.parse_args(args)
        except:
            return
        self.release = jira.cache.get_by_path(jira.cache.cwd)
        if not isinstance(self.release, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        if args.team:
            stories = [s for s in self.release.values()
                if s.scrum_team and s.scrum_team[:len(args.team)] == args.team]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if args.d:
            stories = [s for s in self.release.values()
                if s.developer and s.developer[:len(args.d[0])] == args.d[0]]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if not self.release.keys():
            print 'No data to report'
            return
        release = self.release
        kanban = release.kanban()
        print 'Points in scope  :', round(release.total_points(), 1)
        print 'Points completed :', round(release.points_completed(), 1)
        print 'Total WIP        :', round(release.wip(), 1)
        print 'Stories          :', release.total_stories()
        print '  Avg Size       :', round(release.average_story_size(), 1)
        print '  Std Dev        :', round(release.std_story_size(), 1)
        print '  Smallest       :', release.sort_by_size()[-1].points
        print '  Largest        :', release.sort_by_size()[0].points
        print '  # In Process   :', release.stories_in_process()
        print '  Avg Cycle Time :', kanban.average_cycle_time()
        print '  Std Cycle Time :', kanban.stdev_cycle_time()
        print '  m Cycle Time   :', kanban.median_cycle_time()
        print '  Total Variance :', kanban.variance_cycle_time()
        print 'Bugs             :', len(release.bugs())
        print '  Production     :', len(release.stories(type=['78']))
        print '    Open           :', len(release.resolved_stories(['78']))
        print '    Avg Cycle Time :', kanban.average_lead_time(
            type=['78'])
        print '    m Cycle Time   :', kanban.median_lead_time(
            type=['78'])
        print '    Std Cycle Time :', kanban.stdev_lead_time(
            type=['78'])
        print '  Development    :', len(release.stories(type=['1']))
        print '    Open           :', len(release.resolved_stories(['1']))
        print '    Avg Cycle Time :', kanban.average_lead_time(
            type=['1'])
        print '    m Cycle Time   :', kanban.median_lead_time(
            type=['1'])
        print '    Std Cycle Time :', kanban.stdev_lead_time(
            type=['1'])
        print
        print 'WIP by Status:'
        wip = release.wip_by_status()
        for key in wip:
            print key.ljust(16), ':', str(wip[key]['wip']).ljust(6), \
                wip[key]['stories']
        print
        print 'WIP by Team:'
        wip = release.wip_by_component()
        for key in wip:
            print key[:16].ljust(16), ':',  str(wip[key]['wip']).ljust(6), \
                str(wip[key]['stories']).ljust(3), wip[key]['largest']
        print
        bugs = release.upper_percentiles(0.85, ['1'])
        bugs = []
        if bugs:
            print 'Development Bug Cycle Time 85th Percentile:'
            for bug in bugs:
                print '  ', bug.key, bug.lead_time, bug.scrum_team
            print
        stories = release.upper_percentiles(0.85, ['72'])
        stories = []
        if stories:
            print 'Story Cycle Time 85th Percentile:'
            for story in stories:
                print '  ', story.key, story.cycle_time, story.scrum_team
        print 'Total Cycle Times by Status:'
        cycle_times_in_status = kanban.cycle_times_in_status()
        total = 0
        cycle_times = []
        for status in cycle_times_in_status.keys():
            if status in [1, 10089]:
                continue
            total += cycle_times_in_status[status]
            cycle_times.append((str(status), cycle_times_in_status[status]))
        cycle_times.sort(key=lambda x:x[1], reverse=True)
        for cycle_time in cycle_times:
            print cycle_time[0].ljust(5), ':', cycle_time[1]
        print 'Total :', total
            


