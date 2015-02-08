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
from model import Release

class Command(BaseCommand):
    help = 'Render various charts'
    usage = 'chart [team] [-t chart_type] [-d developer] [-s sort_by]' \
        ' [-p point] [-c cycle_time] [-x file_name.ext] [-i issue types] [-f]'
    options_help = '''    -c : specify cycle time outlier limit
    -d : chart for developer
    -e : include estimates subplot
    -k : chart using or surpressing specific issue keys
    -p : chart for estimate value 
    -f : calculate cycle times from the first in process date (default is last)
    -g : group stories by this strategy (default || estimate || resolved)
    -l : label points
    -s : sorting criteria
    -t : specify chart type: cycle (default) || hist || arrival [state]
    -x : export graph to a file (valid extensions are pdf, png, or jpg)
    -i : issue types to chart
    '''
    examples = '''    chart
    chart App
    chart -k !1234
    chart -t arrival 10090
    chart -s scrum_team points -i 3 7 15'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        parser.add_argument('-c', nargs='*', required=False)
        parser.add_argument('-d', nargs='*', required=False)
        parser.add_argument('-e', action='store_true', required=False)
        parser.add_argument('-f', action='store_true', required=False)
        parser.add_argument('-g', nargs='?', required=False)
        parser.add_argument('-l', action='store_true', required=False)
        parser.add_argument('-k', nargs='*', required=False)
        parser.add_argument('-p', nargs='*', required=False)
        parser.add_argument('-s', nargs='*', required=False)
        parser.add_argument('-t', nargs='*', required=False)
        parser.add_argument('-x', nargs='*', required=False)
        parser.add_argument('-i', nargs='*', required=False)
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
        if self.args.i:
            if len(self.args.i) == 1:
                types = self.args.i[0].split(',')
            else:
                types = self.args.i
        if self.args.team:
            stories = [s for s in self.release.stories(type=types)
                if s.scrum_team and s.scrum_team[:len(self.args.team)] \
                    == self.args.team]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if self.args.d:
            stories = [s for s in self.release.stories(type=types)
                if s.developer and s.developer[:len(self.args.d[0])] \
                    == self.args.d[0]]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if self.args.p:
            stories = [s for s in self.release.stories(type=types)
                if s.points and s.points == float(self.args.p[0])]
            self.release = Release()
            for story in stories:
                self.release.add_story(story)
        if self.args.c:
            cycle_time = int(self.args.c[0])
            stories = [s for s in self.release.stories(type=types)
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
                stories = [s for s in self.release.stories(type=types) if s.points
                    and s.key in show_keys]
                self.release = Release()
                for story in stories:
                    self.release.add_story(story)
            if hide_keys:
                stories = [s for s in self.release.stories(type=types) if s.points
                    and s.key not in hide_keys]
                self.release = Release()
                for story in stories:
                    self.release.add_story(story)
        if self.args.x:
            self.file = 'cycles-%s.%s' % (self.release.version, self.args.x[0])
        else:
            self.file = None
        if not self.release.stories(type=types):
            print 'No data to report'
            return
        kanban = self.release.kanban()
        stories = self.release.stories(type=types)
        stories.sort(key=lambda i:i.key)
        if self.args.s:
            sorting = self.args.s
            if 'cycle_time' not in sorting:
                sorting.append('cycle_time')
        else:
            sorting = ['points', 'cycle_time']

        if self.args.t and self.args.t[0] == 'hist':
            self.histogram(stories)
        elif self.args.t and self.args.t[0] == 'arrival':
            if len(self.args.t) == 2:
                self.arrivals(stories, int(self.args.t[1]))
            else:
                self.arrivals(stories)
        elif not self.args.t or self.args.t[0] == 'cycles':
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
        ''' Chart arrival times in state
        '''
        arrivals = self.release.kanban().state_arrival_interval(state)
        dates = [a['date'] for a in arrivals]
        arrivals = [round(a['interval']/60./60., 1) for a in arrivals]
        average = numpy.average([arrivals])
        std = numpy.std([arrivals])
        nsul = []
        nsuw = []
        nsll = []
        nslw = []
        avg = []
        for x in arrivals:
            nsul.append(average + (std * 3))
            nsuw.append(average + (std * 2))
            nslw.append(average - (std * 2))
            nsll.append(average - (std * 3))
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

        for label, x, y in zip(labels, count[1:], alldata):
            if not y:
                continue
            if not self.args.l:
                if y < std * 3 + average:
                    continue
            pyplot.annotate(
            label,
            url='http://www.google.com',
            xy=(x, y), xytext=(-10,10),
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
                if y < std * 3:
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
