import argparse
import random
import copy
import datetime
import numpy
import pylab
import scipy
import transaction
import dao
from persistent.list import PersistentList
from ..base import BaseCommand
from model import Release, Project, Story, History

simulations = {}

if not 'SIMS' in dao.Jira.cache.data:
    transaction.begin()
    dao.Jira.cache.data['SIMS'] = Project('SIMS', 'simulations')
    transaction.commit()

class Command(BaseCommand):
    help = 'Simulate a release'
    usage = '''    simulate
simulate -a I -d F -s I -p I -b I -c I -t I'''
    options_help = '''    -a : Average cycle time of simulated release
    -d : Standard deviation of cycle time of simulated release
    -e : Average and standard deviation of estimates
    -b : Average developer bandwidth to simulate, in cycle time
    -p : Number of developer pairs to simulate
    -v : Standard deviation of developer bandwidth to simulate, in cycle time
    -s : Number of stories to simulate
    -t : Number of teams to simulate
    -c : Number of simulations to run
    -z : Print simulation history
    -x : Execute a simulation from the history
    -i : Print information about a previous simulation
    '''
    examples = '''    simulate -a 7.9 -d 9.1 -s 136 -p 19 -b 33 -v 23 -t 1 -c 10
    '''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        parser.add_argument('-a', nargs='?', required=False)
        parser.add_argument('-b', nargs='?', required=False)
        parser.add_argument('-d', nargs='?', required=False)
        parser.add_argument('-e', nargs='*', required=False)
        parser.add_argument('-s', nargs='?', required=False)
        parser.add_argument('-t', nargs='?', required=False)
        parser.add_argument('-c', nargs='?', required=False)
        parser.add_argument('-p', nargs='?', required=False)
        parser.add_argument('-v', nargs='?', required=False)
        parser.add_argument('-z', action='store_true', required=False)
        parser.add_argument('-x', nargs='?', required=False)
        parser.add_argument('-i', nargs='*', required=False)
        parser.add_argument('-y', action='store_true', required=False)
        try:
            self.args = parser.parse_args(args)
        except:
            return
        if self.args.z:
            for key in sorted(simulations.keys()):
                failures = len([s for s in simulations[key]['runs'].values()
                    if not s['success']])
                print key, ':', simulations[key]['command'].ljust(63), \
                      'Fails:', str(failures)
            return
        if self.args.x:
            Command().run(jira, simulations[int(self.args.x)][
                'command'].split()[1:])
            return
        if self.args.i:
            key = int(self.args.i[0])
            run = int(self.args.i[1])
            print key, ':', simulations[key]['command']
            print 'Run %d of %d runs' % (
                run, len(simulations[key]['runs'].keys()))
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
            print
            if simulations[key]['runs'][run]['success']:
                print 'Simulation Succeeded'
            else:
                print 'Simulation Failed'
            return
        try:
            release = jira.cache.get_by_path(jira.cache.cwd)
            kanban = release.kanban()
        except:
            release = None
            kanban = None
            if not self.all_params_specified(args):
                print 'Error: you must be in a release to run simulate without all parameters specified'
                return
        if self.args.a:
            average = float(self.args.a)
        else:
            average = kanban.average_cycle_time()
        if self.args.d:
            std = float(self.args.d)
        else:
            std = kanban.stdev_cycle_time()
        if self.args.e:
            avg_pts = float(self.args.e[0])
            std_pts = float(self.args.e[1])
        else:
            if release:
                avg_pts = release.average_story_size()
                std_pts = release.std_story_size()
        if self.args.s:
            stories = int(self.args.s)
        else:
            stories = release.total_stories()
        if self.args.t:
            teams = int(self.args.t)
        else:
            teams = len(release.tasked_teams())
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
        if self.args.y:
            self.make_release(average, std, stories, bandwidth, count,
                num_pairs, teams, std_dev_ct, avg_pts, std_pts)
            return

        command = 'simulate -s %d -a %.1f -d %.1f -p %d -b %.1f -v %.1f -t %d -c %d' % (stories, average, std, num_pairs, bandwidth,  std_dev_ct, teams, count)
        sim = len(simulations.keys()) + 1
        simulations[sim] = {'runs': {}}
        simulations[sim]['command'] = command
        for c in xrange(count):
            tasks = scipy.stats.norm.rvs(loc=average, scale=std, size=stories)
            dev_capacity = scipy.stats.norm.rvs(loc=bandwidth,
                scale=std_dev_ct, size=num_pairs*2)
            dev_capacity = [a+b for a, b in zip(dev_capacity[1::2],
                dev_capacity[::2])]
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
                print 'Fail -> ', \
                      'Work:', str(int(sum(tasks))).ljust(4), \
                      'Capacity:', str(int(capacity)).ljust(5), \
                      'Cap Remaining:', '%' + str(round(
                          sum(pairs.values())/capacity, 2)* 100).ljust(5), \
                      'Max:', str(round(max(pairs.values()), 1)).ljust(5), \
                      'Missed:', round(missed, 1)
                simulations[sim]['runs'][c]['success'] = False
            else:
                print '        ', \
                      'Work:', str(int(sum(tasks))).ljust(4), \
                      'Capacity:', str(int(capacity)).ljust(5), \
                      'Cap Remaining:', '%' + str(round(
                          sum(pairs.values())/capacity, 2)* 100).ljust(5), \
                      'Max:', round(max(pairs.values()), 1)
                simulations[sim]['runs'][c]['success'] = True
        print
        print 'Command:', command

    def all_params_specified(self, args):
        for param in ['-a', '-b', '-d', '-p', '-v', '-s', '-t']:
            if not param in args:
                return False
        return True

    def get_estimates(self, avg, std, count):
        estimates = scipy.stats.norm.rvs(loc=avg, scale=std, size=count)
        return [round(e, 2) if e >= 0 else 0. for e in estimates]

    def get_pairs(self, avg, std, count):
        devs = scipy.stats.norm.rvs(loc=avg, scale=std, size=count*2)
        return [a+b for a, b in zip(devs[1::2], devs[::2])]

    def make_release(self, average, std, stories, bandwidth, count, num_pairs,
        teams, std_dev_ct, avg_pts, std_pts):
        release = Release()
        sim = len(dao.Jira.cache.data['SIMS']) + 1
        release.version = 'SIM-%d' % sim
        transaction.begin()
        dao.Jira.cache.data['SIMS'][release.version] = release
        transaction.commit()

        tasks = scipy.stats.norm.rvs(loc=average, scale=std, size=stories)
        tasks = [round(task, 1) if task >= 0 else 0. for task in tasks]
        points = self.get_estimates(avg_pts, std_pts, stories)
        dev_capacity = self.get_pairs(bandwidth, std_dev_ct, num_pairs)

        command = 'simulate -s %d -a %.1f -d %.1f -p %d -b %.1f -v %.1f -c %d' \
            % (stories, average, std, num_pairs, bandwidth,  std_dev_ct, count)
        simulations[sim] = {'runs': {}}
        simulations[sim]['command'] = command
        simulations[sim]['runs'][0] = {}
        simulations[sim]['runs'][0]['tasks'] = copy.copy(tasks)
        pairs = dict((k, round(v, 1)) for (k, v) in zip(xrange(num_pairs),
            dev_capacity))
        simulations[sim]['runs'][0]['pairs'] = copy.copy(pairs)

        capacity = sum(pairs.values())
        count = 1
        for estimate in points:
            story = Story('SIM-X%d' % count)
            story.id = count
            story.points = int(estimate)
            story.title = 'Story %d for simulation %d' % (count, sim)
            story.fix_versions = PersistentList()
            story.fix_versions.append('SIM-%d' % sim)
            story.history = History()
            story.created = datetime.datetime.now()
            story.type = '72'
            story.assignee = None
            story.developer = None
            story.scrum_team = 'Sim Team %d' % int(random.random() * teams)
            story.status = 1
            story.project = 'SIMS'
            transaction.begin()
            release[story.key] = story
            transaction.commit()
            transaction.begin()
            docid = dao.Jira.cache.document_map.add(
                ['sim', story.project, story.fix_versions[0], story.key])
            dao.Jira.cache.catalog.index_doc(docid, story)
            transaction.commit()
            count += 1

        for day in xrange(20):
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
