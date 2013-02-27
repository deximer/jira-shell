import argparse
import copy
import numpy
import pylab
import scipy
from ..base import BaseCommand
from model import Release

simulations = {}

class Command(BaseCommand):
    help = 'Simulate a release'
    usage = 'simulate -a I -d F -s I -p I -b I -c I'
    options_help = '''    -a : Average cycle time of simulated release
    -b : Average developer bandwidth to simulate, in cycle time
    -v : Standard deviation of developer bandwidth to simulate, in cycle time
    -d : Standard deviation of cycle time of simulated release
    -s : Number of stories to simulate
    -c : Number of simulations to run
    -p : Number of developer pairs to simulate
    -z : Print simulation history
    -x : Execute a simulation from the history
    -i : Print information about a previous simulation
    '''
    examples = '''    simulate -a 7.9 -d 9.1 -s 136 -p 19 -b 33 -v 23 -c 10
    '''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        parser.add_argument('-a', nargs='?', required=False)
        parser.add_argument('-b', nargs='?', required=False)
        parser.add_argument('-d', nargs='?', required=False)
        parser.add_argument('-s', nargs='?', required=False)
        parser.add_argument('-c', nargs='?', required=False)
        parser.add_argument('-p', nargs='?', required=False)
        parser.add_argument('-v', nargs='?', required=False)
        parser.add_argument('-z', action='store_true', required=False)
        parser.add_argument('-x', nargs='?', required=False)
        parser.add_argument('-i', nargs='*', required=False)
        try:
            self.args = parser.parse_args(args)
        except:
            return
        if self.args.z:
            for key in sorted(simulations.keys()):
                print key, ':', simulations[key]['command']
            return
        if self.args.x:
            Command().run(jira, simulations[int(self.args.x)][
                'command'].split()[1:])
            return
        if self.args.i:
            key = int(self.args.i[0])
            run = int(self.args.i[1])
            print key, ':', simulations[key]['command']
            print 'Run %d of %d runs' % (run, len(simulations[key]['runs'].keys()))
            print 'Work Load:'
            print
            print simulations[key]['runs'][run]['tasks']
            print
            print 'Starting Pair Capacity:'
            print
            print simulations[key]['runs'][run]['pairs']
            print
            print 'Ending Pair Capacity:'
            print
            print simulations[key]['runs'][run]['end_pairs']
            return
        try:
            release = jira.cache.get_by_path(jira.cache.cwd)
            kanban = release.kanban()
        except:
            pass
        if self.args.a:
            average = float(self.args.a)
        else:
            average = kanban.average_cycle_time()
        if self.args.d:
            std = float(self.args.d)
        else:
            std = kanban.stdev_cycle_time()
        if self.args.s:
            stories = int(self.args.s)
        else:
            stories = release.total_stories()
        if self.args.b:
            bandwidth = float(self.args.b)
        else:
            bandwidth = release.average_developer_cycle_time()
        if self.args.c:
            count = int(self.args.c)
        else:
            count = 1
        if self.args.p:
            num_pairs = int(self.args.p)
        else:
            num_pairs = len(release.developers().keys())/2
        if self.args.v:
            std_dev_ct = float(self.args.v)
        else:
            std_dev_ct = release.stdev_developer_cycle_time()

        sim = len(simulations.keys()) + 1
        simulations[sim] = {'runs': {}}
        for c in xrange(count):
            tasks = scipy.stats.norm.rvs(loc=average, scale=std, size=stories)
            dev_capacity = scipy.stats.norm.rvs(loc=bandwidth,
                scale=std_dev_ct, size=num_pairs*2)
            dev_capacity = [a+b for a, b in zip(dev_capacity[1::2], dev_capacity[::2])]
            tasks = [round(task, 1) if task >= 0 else 0. for task in tasks]
            simulations[sim]['runs'][c] = {}
            simulations[sim]['runs'][c]['tasks'] = copy.copy(tasks)
            pairs = dict((k, round(v, 1)) for (k, v) in zip(xrange(num_pairs),
                dev_capacity))
            simulations[sim]['runs'][c]['pairs'] = copy.copy(pairs)
            capacity = sum(pairs.values())
            fail = False
            tasked = False
            index = 0
            for task in sorted(tasks, reverse=True):
                missed = 0
                for pair in pairs.keys():
                    if pairs[pair] >= task:
                        pairs[pair] -= task
                        tasked = True
                        break
                if not tasked:
                    missed = task
                    fail = True
                    break
                tasked = False
            end_pairs = copy.copy(pairs)
            for k in end_pairs:
                end_pairs[k] = round(end_pairs[k], 1)
            simulations[sim]['runs'][c]['end_pairs'] = end_pairs
            if fail:
                print 'Fail -> ', 'Work:', str(int(sum(tasks))).ljust(4), 'Capacity:', str(int(capacity)).ljust(5), 'Cap Remaining:', '%' + str(round(sum(pairs.values())/capacity, 2)* 100).ljust(5), 'Max:', str(round(max(pairs.values()), 1)).ljust(5), 'Missed:', round(missed, 1)
            else:
                print '        ', 'Work:', str(int(sum(tasks))).ljust(4), 'Capacity:', str(int(capacity)).ljust(5), 'Cap Remaining:', '%' + str(round(sum(pairs.values())/capacity, 2)* 100).ljust(5), 'Max:', round(max(pairs.values()), 1)

        print
        command = 'simulate -s %d -a %.1f -d %.1f -p %d -b %.1f -v %.1f -c %d' % (stories, average, std, num_pairs, bandwidth,  std_dev_ct, count)
        print command
        simulations[sim]['command'] = command

