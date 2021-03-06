import argparse
import copy
import numpy
import pylab
import scipy
import warnings
import datetime
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from matplotlib import pyplot, gridspec
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release

class Command(BaseCommand):
    help = 'Render various charts'
    usage = 'chart [team] [-o chart_type] [-d developer] [-s sort_by]' \
        ' [-p point] [-c cycle_time] [-x file_name.ext] [-t issue types] [-f]' \
        ' [-l [issue keys]]'
    options_help = '''    -c : specify cycle time outlier limit
    -d : chart for developer
    -e : include estimates subplot
    -k : chart using or surpressing specific issue keys
    -f : calculate cycle times from the first in process date (default is last)
    -g : group stories by this strategy (default || estimate || resolved)
    -l : label points
    -o : specify chart type: cycle (default) || hist || arrival [state]
    -p : priority to chart
    -s : sorting criteria
    -t : issue types to chart
    -v : chart for estimate value 
    -x : export graph to a file (valid extensions are pdf, png, or jpg)
    '''
    examples = '''    chart
    chart App
    chart -k !1234
    chart -o arrival 10090
    chart -s scrum_team points -t 3 7 15'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        parser.add_argument('-c', nargs='*', required=False)
        parser.add_argument('-d', nargs='*', required=False)
        parser.add_argument('-e', action='store_true', required=False)
        parser.add_argument('-f', action='store_true', required=False)
        parser.add_argument('-g', nargs='?', required=False)
        parser.add_argument('-l', nargs='*', required=False)
        parser.add_argument('-k', nargs='*', required=False)
        parser.add_argument('-o', nargs='*', required=False)
        parser.add_argument('-p', nargs='*', required=False)
        parser.add_argument('-v', nargs='*', required=False)
        parser.add_argument('-s', nargs='*', required=False)
        parser.add_argument('-t', nargs='*', required=False)
        parser.add_argument('-x', nargs='*', required=False)
        try:
            self.args = parser.parse_args(args)
        except:
            return
        self.release = jira.cache.get_by_path(jira.cache.cwd)
        if not isinstance(self.release, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        if self.args.f:
            self.cycle_time = 'aggregate_cycle_time'
        else:
            self.cycle_time = 'cycle_time'
        types = ['7']
        if self.args.t:
            if len(self.args.t) == 1:
                types = self.args.t[0].split(',')
            else:
                types = self.args.t
        if self.args.team:
            stories = [s for s in self.release.clean_stories(type=types)
                if s.scrum_team and s.scrum_team[:len(self.args.team)] \
                    == self.args.team]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if self.args.d:
            stories = [s for s in self.release.clean_stories(type=types)
                if s.developer and s.developer[:len(self.args.d[0])] \
                    == self.args.d[0]]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if self.args.v:
            stories = [s for s in self.release.clean_stories(type=types)
                if s.points and s.points == float(self.args.p[0])]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if self.args.c:
            cycle_time = int(self.args.c[0])
            stories = [s for s in self.release.clean_stories(type=types)
                if getattr(s, self.cycle_time) < cycle_time]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if self.args.k:
            hide_keys = []
            show_keys = []
            for k in self.args.k:
                if k[0] == '!':
                    hide_keys.append('NG-' + k[1:])
                else:
                    show_keys.append('NG-' + k)
            if show_keys:
                stories = [s for s in self.release.clean_stories(type=types)
                    and s.key in show_keys]
                self.release = Release()
                for story in stories:
                    self.release.add_story(story)
            if hide_keys:
                stories = [s for s in self.release.clean_stories(type=types)
                    and s.key not in hide_keys]
                self.release = Release()
                for story in stories:
                    self.release.add_story(story)
        if self.args.x:
            self.file = 'cycles-%s.%s' % (self.release.version, self.args.x[0])
        else:
            self.file = None
        kanban = self.release.kanban()
        stories = self.release.clean_stories(type=types)
        if self.args.p:
            stories = [s for s in stories if s.priority in self.args.p]
        if not stories:
            print 'No data to report'
            return
        stories.sort(key=lambda i:i.key)
        if self.args.s:
            sorting = self.args.s
            if 'cycle_time' not in sorting:
                sorting.append('cycle_time')
        else:
            sorting = ['cycle_time']

        if self.args.o and self.args.o[0] == 'hist':
            self.histogram(stories)
        elif self.args.o and self.args.o[0] == 'arrival':
            if len(self.args.o) == 2:
                if self.args.o[1] in self.release.WIP.keys():
                    state = self.release.WIP[self.args.o[1]]
                elif int(self.args.o[1]) in self.release.WIP.values():
                    state = int(self.args.o[1])
                else:
                    print 'Invalid state specified: %s' % self.args.o[1]
                    return
                self.arrivals(stories, state)
            else:
                self.arrivals(stories)
        elif not self.args.o or self.args.o[0] == 'cycles':
            self.cycles(stories, sorting)
        else:
            print 'Unknown chart type: %s' % self.args.t[0]

    def histogram(self, stories):
        bins = len(stories)/5
        if bins < 10:
            bins = 10
        cycle_times = [s.cycle_time for s in stories if s.cycle_time]
        param = scipy.stats.norm.fit(cycle_times)
        x = numpy.linspace(min(cycle_times), max(cycle_times), 200)
        pdf_fitted = scipy.stats.norm.pdf(x, loc=param[0], scale=param[1])
        pylab.plot(x, pdf_fitted, 'r-', label='Fitted')
        pylab.hist(cycle_times, bins, normed=True, alpha=.3)
        pylab.show(block=False)

    def arrivals(self, stories, state=6):
        ''' Chart a plot point for every arrival time in state
        '''
        arrivals = self.release.kanban().state_arrival_interval(state)
        dates = [a['date'] for a in arrivals]
        arrivals = [round(a['interval']/60./60., 1) for a in arrivals]
        average = numpy.median([arrivals])
        std = numpy.std([arrivals])
        iql = numpy.percentile([arrivals], 25)
        iqh = numpy.percentile([arrivals], 75)
        nsul = []
        nsuw = []
        nsll = []
        nslw = []
        avg = []
        for x in arrivals:
            nsul.append(average + (iqh * 3))
            nsuw.append(average + (iqh * 2))
            nslw.append(average - (iql * 2))
            nsll.append(average - (iql * 3))
            avg.append(average)
        pyplot.plot(dates, arrivals, '*', color='g')
        pyplot.plot(dates, nsul, 'o', linestyle='-', color='r')
        pyplot.plot(dates, nsuw, '.', linestyle=':', color='y')
        pyplot.plot(dates, nslw, '.', linestyle=':', color='y')
        pyplot.plot(dates, nsll, 'o', linestyle='-', color='r')
        pyplot.plot(dates, avg, '',linestyle='-.',  markerfacecolor='None')
        pyplot.show(block=False)

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
        def compare(a, b):
            if not a[0]:
                return -1
            if not b[0]:
                return 1
            return cmp(a, b)
        stories.sort(key=lambda x:tuple([getattr(x, key) for key in sorting]),
            cmp=compare)
        for story in stories:
            if not story.started:
                continue
            alldata.append(getattr(story, self.cycle_time))
            if not story.resolved:
                wip.append(getattr(story, self.cycle_time))
                data.append(None)
            else:
                data.append(getattr(story, self.cycle_time))
                wip.append(None)
            estimates.append(story.points)
            labels.append(story.key)
            estimate_labels.append(story.key)
            developer_labels.append(story.developer)
            if self.args.g and not self.args.g == 'default':
                if self.args.g == 'estimate':
                    count.append(getattr(story, sorting[0]))
                elif self.args.g == 'resolved':
                    if story.resolved:
                        count.append(story.resolved)
                    elif story.started:
                        count.append(story.started)
                    else:
                        count.append(datetime.datetime.now())
            else:
                count.append(count[-1] + 1)

        all_non_empty_data = [d for d in alldata if d]
        if not all_non_empty_data:
            print 'Nothing to do. Probably need to finish some work.'
            return
        std = numpy.std(all_non_empty_data)
        iql = numpy.percentile(all_non_empty_data, 25)
        iqh = numpy.percentile(all_non_empty_data, 75)
        average = numpy.median(all_non_empty_data)
        nsul = []
        nsuw = []
        nsll = []
        nslw = []
        avg = []
        for x in data:
            nsul.append(average + (iqh * 3))
            nsuw.append(average + (iqh * 2))
            nslw.append(average - (iql * 2))
            nsll.append(average - (iql * 3))
            avg.append(average)
        if self.args.e:
            gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1]) 
            pyplot.subplot(gs[0])
        pyplot.plot(count[1:], data, '*', color='g')
        pyplot.plot(count[1:], wip, '^', color='r')
        pyplot.plot(count[1:], nsul, 'o', linestyle='-', color='r')
        pyplot.plot(count[1:], nsuw, '.', linestyle=':', color='y')
        pyplot.plot(count[1:], nslw, '.', linestyle=':', color='y')
        pyplot.plot(count[1:], nsll, 'o', linestyle='-', color='r')
        pyplot.plot(count[1:], avg, '',linestyle='-.',  markerfacecolor='None')

        previous_y = None 
        y_label = 10
        for label, x, y in zip(labels, count[1:], alldata):
            if not y:
                y = 0.0
            if y == previous_y:
                y_label += 10
            else:
                previous_y = y
                y_label = 10
            if self.args.l is None:
                if y < iqh * 3 + average:
                    continue
            if self.args.l is not None and len(self.args.l) \
                and label not in self.args.l:
                continue
            pyplot.annotate(
            label,
            url='http://www.google.com',
            xy=(x, y), xytext=(-10,y_label),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=7,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        yoffset = -10
        odd = True
        for label, x, y in zip(developer_labels, count[1:], nsll):
            if not self.args.l:
                continue
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
            url='http://www.google.com',
            xy=(x, y), xytext=(10, yoffset),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=8,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='cyan', alpha=0.1),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            yoffset -= 10
        odd = True
        yoffset = 10
        for label, x, y in zip(developer_labels, count[1:], nsul):
            if not self.args.l:
                continue
            if not self.args.l:
                if y < iqh * 3:
                    continue
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
            url='http://www.google.com',
            xy=(x, y), xytext=(10, yoffset),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=8,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='cyan', alpha=0.1),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            yoffset += 10

        if not self.args.e:
            if self.file:
                pyplot.savefig(self.file, bbox=0)
            else:
                pyplot.show(block=False)
            return

        pyplot.grid(True)
        pyplot.subplot(gs[1])
        pyplot.plot(count[1:], estimates, 'o', linestyle='', color='b')
        previous_label = ''
        label_count = 0
        elevated = True
        for label, x, y in zip(estimate_labels, count[1:], estimates):
            if not self.args.l:
                continue
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
            url='http://www.google.com',
            xy=(x, y), xytext=(-10,yoffset),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=7,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        if self.file:
            pyplot.savefig(self.file, bbox=0)
        else:
            pyplot.show(block=False)
