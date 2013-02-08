import argparse
import copy
import numpy
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from matplotlib import pyplot, gridspec
from ..base import BaseCommand
from model import Release

class Command(BaseCommand):
    help = 'Render various charts based on the data'
    usage = 'chart [team] [-t chart_type] [-d developer] [-s sort_by]' \
        ' [-p point] [-c cycle_time]'
    options_help = '''    -c : specify cycle time outlier limit
    -d : chart for developer
    -k : chart using or surpressing specific issue keys
    -p : chart for estimate value 
    -s : sorting criteria
    -t : specify chart type (default is cycle times)
    '''
    examples = '''    chart
    chart App
    chart -k !1234
    chart -s scrum_team points'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        parser.add_argument('-t', nargs='*', required=False)
        parser.add_argument('-d', nargs='*', required=False)
        parser.add_argument('-p', nargs='*', required=False)
        parser.add_argument('-s', nargs='*', required=False)
        parser.add_argument('-k', nargs='*', required=False)
        parser.add_argument('-c', nargs='*', required=False)
        try:
            args = parser.parse_args(args)
        except:
            return
        self.release = copy.deepcopy(jira.cache.get_by_path(jira.cache.cwd))
        if not isinstance(self.release, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        if args.team:
            stories = [s for s in self.release.stories()
                if s.scrum_team and s.scrum_team[:len(args.team)] == args.team]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if args.d:
            stories = [s for s in self.release.stories()
                if s.developer and s.developer[:len(args.d[0])] == args.d[0]]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if args.p:
            stories = [s for s in self.release.stories()
                if s.points and s.points == float(args.p[0])]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if args.c:
            cycle_time = int(args.c[0])
            stories = [s for s in self.release.stories()
                if s.cycle_time < cycle_time]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if args.k:
            hide_keys = []
            show_keys = []
            for k in args.k:
                if k[0] == '!':
                    hide_keys.append('NG-' + k[1:])
                else:
                    show_keys.append('NG-' + k)
            if show_keys:
                stories = [s for s in self.release.stories() if s.points
                    and s.key in show_keys]
                self.release = Release()
                for story in stories:
                    self.release.add_story(story)
            if hide_keys:
                stories = [s for s in self.release.stories() if s.points
                    and s.key not in hide_keys]
                self.release = Release()
                for story in stories:
                    self.release.add_story(story)
        if not self.release.stories():
            print 'No data to report'
            return
        kanban = self.release.kanban()
        stories = self.release.stories(type='72')
        stories.sort(key=lambda i:i.key)
        if args.s:
            sorting = args.s
            if 'cycle_time' not in sorting:
                sorting.append('cycle_time')
        else:
            sorting = ['points', 'scrum_team', 'cycle_time']
        if not args.t or args.t == 'cycles':
            self.cycles(stories, sorting)
        else:
            print 'Unknown chart type: %s' % args.t[0]

    def cycles(self, stories, sorting):
        data = []
        wip = []
        estimates = []
        estimate_labels = []
        developer_labels = []
        alldata = []
        labels = []
        ratios = []
        count = [0]
        stories = [s for s in stories if s.started and s.scrum_team
           and s.scrum_team != 'Continuous Improvement ']
        stories.sort(key=lambda x:tuple([getattr(x, key) for key in sorting]))
        for story in stories:
            alldata.append(story.cycle_time)
            if not story.resolved:
                wip.append(story.cycle_time)
                data.append(None)
            else:
                data.append(story.cycle_time)
                wip.append(None)
            estimates.append(story.points)
            labels.append(story.key)
            estimate_labels.append(story.scrum_team)
            developer_labels.append(story.developer)
            count.append(count[-1] + 1)

        std = numpy.std([d for d in alldata if d])
        average = numpy.average([d for d in alldata if d])
        nsul = []
        nsuw = []
        nsll = []
        nslw = []
        avg = []
        for x in data:
            nsul.append(average + (std * 3))
            nsuw.append(average + (std * 2))
            nslw.append(average - (std * 2))
            nsll.append(average - (std * 3))
            avg.append(average)
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1]) 
        pyplot.subplot(gs[0])
        pyplot.plot(count[1:], data, '*', color='g')
        pyplot.plot(count[1:], wip, '^', color='r')
        pyplot.plot(count[1:], nsul, 'o', linestyle='-', color='r')
        pyplot.plot(count[1:], nsuw, '.', linestyle=':', color='y')
        pyplot.plot(count[1:], nslw, '.', linestyle=':', color='y')
        pyplot.plot(count[1:], nsll, 'o', linestyle='-', color='r')
        pyplot.plot(count[1:], avg, '',linestyle='-.',  markerfacecolor='None')
        for label, x, y in zip(labels, count[1:], alldata):
            pyplot.annotate(
            label,
            xy=(x, y), xytext=(-10,10),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=7,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        yoffset = -10
        odd = True
        for label, x, y in zip(developer_labels, count[1:], nsll):
            if odd:
                odd = False
            else:
                odd = True
                continue
            if not label:
                continue
            if yoffset < -30:
                yoffset = -10
            pyplot.annotate(
            label,
            xy=(x, y), xytext=(10, yoffset),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=8,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='cyan', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            yoffset -= 10
        odd = True
        yoffset = 10
        for label, x, y in zip(developer_labels, count[1:], nsul):
            if odd:
                odd = False
                continue
            else:
                odd = True
            if not label:
                continue
            if yoffset > 30:
                yoffset = 10
            pyplot.annotate(
            label,
            xy=(x, y), xytext=(10, yoffset),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=8,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='cyan', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            yoffset += 10
        pyplot.grid(True)
        pyplot.subplot(gs[1])
        pyplot.plot(count[1:], estimates, 'o', linestyle='-', color='b')
        previous_label = ''
        label_count = 0
        elevated = True
        for label, x, y in zip(estimate_labels, count[1:], estimates):
            if label == previous_label:
                label_count += 1
                continue
            if label_count <=1 and not elevated:
                elevated = True
                yoffset = 25
            else:
                elevated = False
                yoffset = 10
            label_count = 0
            previous_label = label
            pyplot.annotate(
            label,
            xy=(x, y), xytext=(-10,yoffset),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=7,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        pyplot.show()
