import argparse
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Report on the current release'
    usage = 'report [team]'
    exmamples = '''    report
    report App'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        self.refresh_data(jira, False)
        if args.team:
            self.release.data = [s for s in self.release.data
                if s.scrum_team and s.scrum_team[:len(args.team)] == args.team]
        release = self.release
        kanban = self.release.kanban()
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
        print 'Bugs             :', len(release.bugs())
        print '  Production     :', len(release.stories(type=['78']))
        print '    Avg Cycle Time :', kanban.average_cycle_time_life(
            type=['78'])
        print '    m Cycle Time   :', kanban.median_cycle_time_life(
            type=['78'])
        print '    Std Cycle Time :', kanban.stdev_cycle_time_life(
            type=['78'])
        print '  Development    :', len(release.stories(type=['1']))
        print '    Avg Cycle Time :', kanban.average_cycle_time_life(
            type=['1'])
        print '    m Cycle Time   :', kanban.median_cycle_time_life(
            type=['1'])
        print '    Std Cycle Time :', kanban.stdev_cycle_time_life(
            type=['1'])
        print
        print 'WIP by Status:'
        wip = release.wip_by_status()
        for key in wip:
            print key.ljust(16), ':', str(wip[key]['wip']).ljust(6), \
                wip[key]['stories']
        print
        bugs = release.upper_percentiles(0.85, ['1'])
        if bugs:
            print 'Development Bug Cycle Time 85th Percentile:'
            for bug in bugs:
                print '  ', bug.key, bug.cycle_time_life, bug.scrum_team
            print
        stories = release.upper_percentiles(0.85, ['72'])
        if stories:
            print 'Story Cycle Time 85th Percentile:'
            for story in stories:
                print '  ', story.key, story.cycle_time, story.scrum_team

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
