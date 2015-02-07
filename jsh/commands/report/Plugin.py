import argparse
import copy
from ..base import BaseCommand
from model import Release, humanize

class Command(BaseCommand):
    help = 'Report on the current release'
    usage = 'report [team] [-d developer]'
    options_help = '''    -d : report on a specific developer'''
    exmamples = '''    report
    report App'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        parser.add_argument('-d', nargs='*', required=False)
        parser.add_argument('-f', action='store_true', required=False)
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
        smallest = 'None'
        if release.sort_by_size():
            smallest = release.sort_by_size()[-1].points
        largest = 'None'
        if release.sort_by_size():
            largest = release.sort_by_size()[0].points
        print 'Points in scope  :', round(release.total_points(), 1)
        print 'Points completed :', round(release.points_completed(), 1)
        print 'Total WIP        :', round(release.wip(), 1)
        print 'Stories          :', release.total_stories()
        print '  Avg Size       :', round(release.average_story_size(), 1)
        print '  Std Dev        :', round(release.std_story_size(), 1)
        print '  Smallest       :', smallest
        print '  Largest        :', largest 
        print '  # In Process   :', release.stories_in_process()
        print '  Avg Cycle Time :', kanban.average_cycle_time()
        print '  Std Cycle Time :', kanban.stdev_cycle_time()
        print '  Skew           :', release.skew_cycle_time()
        print '  m Cycle Time   :', kanban.median_cycle_time()
        print '  Total Variance :', kanban.variance_cycle_time()
        print '  Total Dev CT   :', release.aggregate_developer_cycle_time()
        print '  Avg Dev CT     :', release.average_developer_cycle_time()
        print '  Std Dev CT     :', release.stdev_developer_cycle_time()
        print 'Bugs             :', len(release.bugs())
        print '  Production     :', len(release.stories(type=['78']))
        print '    Closed         :', len(release.resolved_stories(['78']))
        print '    Avg Cycle Time :', kanban.average_lead_time(type=['78'])
        print '    m Cycle Time   :', kanban.median_lead_time(type=['78'])
        print '    Std Cycle Time :', kanban.stdev_lead_time(type=['78'])
        print '  Development    :', len(release.stories(type=['1']))
        print '    Closed         :', len(release.resolved_stories(['1']))
        print '    Avg Cycle Time :', kanban.average_lead_time(type=['1'])
        print '    m Cycle Time   :', kanban.median_lead_time(type=['1'])
        print '    Std Cycle Time :', kanban.stdev_lead_time(type=['1'])
        print
        print 'WIP by Status:'
        wip = release.wip_by_status()
        print 'Status:', '           WIP:', '  #:'
        for key in wip:
            print humanize(int(key)).ljust(16), ':', \
                str(wip[key]['wip']).ljust(6), wip[key]['stories']
        print
        print 'WIP by Team:'
        wip = release.wip_by_component()
        print 'Team:', '             WIP:', '  #:', ' Largest:'
        for key in wip:
            print key[:16].ljust(16), ':',  str(wip[key]['wip']).ljust(6), \
                str(wip[key]['stories']).ljust(3), wip[key]['largest']
        print
        print 'Total Cycle Times by Status:'
        cycle_times_in_status = kanban.cycle_times_in_status()
        total = 0
        cycle_times = []
        for status in cycle_times_in_status.keys():
            if status in (1, 10089, 6): # ignore 'open' and 'ready'
                continue
            total += cycle_times_in_status[status]
            cycle_times.append((str(status), cycle_times_in_status[status]))
        cycle_times.sort(key=lambda x:x[1], reverse=True)
        for cycle_time in cycle_times:
            print humanize(int(cycle_time[0])).ljust(5), ':', \
                str(cycle_time[1]).ljust(4), \
                '%' + str(round(cycle_time[1]/float(total), 2) * 100)
        print 'Total   :', total
        print 'Max PCE : %' + str(kanban.process_cycle_efficiency())
        print
        print 'Average Takt Time in Status:'
        print '  Status:', 'Average:', 'Stdev:'
        averages = kanban.average_times_in_status()
        stds = kanban.std_times_in_status()
        for key in averages:
            print ' ', humanize(key).ljust(7), str(averages[key]).ljust(8), stds[key]
        print
        print 'Arrival Times for Status:'
        print '  Status:', 'Average:', 'Stdev:'
        averages = kanban.average_arrival_for_status()
        stds = kanban.std_arrival_for_status()
        for key in averages:
            print ' ', humanize(key).ljust(7), str(averages[key]).ljust(8), stds[key]
        print
        print 'State Transition Probabilities:'
        states = kanban.state_transition_probabilities()
        print 'Status: ', 'Stories:', 'Days:', 'Avg:', 'Std:'
        for state in states:
            print humanize(state) + ':'
            for exit in states[state]:
                print '  ', humanize(exit).ljust(5), str(len(states[state][exit]['days'])).ljust(8), str(sum(states[state][exit]['days'])).ljust(5), str(states[state][exit]['average']).ljust(5), states[state][exit]['std']

        intervals = kanban.all_state_arrival_intervals()
        print
        print 'Arrival Intervals:'
        for state in intervals:
            print humanize(state).ljust(5), \
                  str(intervals[state]['average']).ljust(7), \
                  intervals[state]['std']

        print
        print 'Root Causes:'
        causes = {}
        for story in release.bugs():
            if story.root_cause not in causes:
                causes[story.root_cause] = [story.key]
            else:
                causes[story.root_cause].append(story.key)
        causes['Not Specified'] = causes['']
        del causes['']
        for cause in causes:
            print cause, ':', len(causes[cause])
