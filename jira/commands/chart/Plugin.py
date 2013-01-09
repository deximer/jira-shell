import spc
import argparse
import numpy
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from matplotlib import pyplot, gridspec
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Render various charts based on the data'
    usage = 'chart [team] [-t chart_type] [-d developer] [-s sort_by]' \
        ' [-p point]'
    options_help = '''    -t : specify chart type (default is cycle times)
    -d : chart for developer
    -p : chart for estimate value 
    -s : sorting criteria
    '''
    examples = '''    chart
    chart App
    chart -s scrum_team points'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('team', nargs='?')
        parser.add_argument('-t', nargs='*', required=False)
        parser.add_argument('-d', nargs='*', required=False)
        parser.add_argument('-p', nargs='*', required=False)
        parser.add_argument('-s', nargs='*', required=False)
        try:
            args = parser.parse_args(args)
        except:
            return
        self.refresh_data(jira, False)
        if args.team:
            self.release.data = [s for s in self.release.data
                if s.scrum_team and s.scrum_team[:len(args.team)] == args.team]
        if args.d:
            self.release.data = [s for s in self.release.data
                if s.developer and s.developer[:len(args.d[0])] == args.d[0]]
        if args.p:
            self.release.data = [s for s in self.release.data
                if s.points and s.points == float(args.p[0])]
        if not self.release.data:
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
        elif args.t == 'ratios':
            self.ratios(stories, sorting)
        else:
            print 'Unknown chart type: %s' % args.t[0]

    def cycles(self, stories, sorting):
        data = []
        wip = []
        estimates = []
        estimate_labels = []
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
            nsll.append(average - (std * 3))
            nslw.append(average - (std * 2))
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
        pyplot.grid(True)
        pyplot.subplot(gs[1])
        pyplot.plot(count[1:], estimates, 'o', linestyle='-', color='b')
        previous_label = ''
        for label, x, y in zip(estimate_labels, count[1:], estimates):
            if label == previous_label:
                continue
            previous_label = label
            pyplot.annotate(
            label,
            xy=(x, y), xytext=(-10,10),
            textcoords = 'offset points', ha='right', va='bottom', fontsize=7,
            bbox = dict(boxstyle = 'round,pad=0.3', fc='yellow', alpha=0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        pyplot.show()

    def ratios(self, stories):
        data = []
        for story in stories:
            if not story.started or not story.resolved:
                continue
            data.append(story.cycle_time/story.points if story.points else 0)
        chart = spc.Spc(data, spc.CHART_X_MR_X)
        chart.get_chart()
        pyplot.show()
