import spc
import argparse
import numpy
from matplotlib import pyplot, gridspec
from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Render various charts based on the data'
    usage = 'chart [chart_type]'
    options_help = '''    ratios : chart ratio of estimates to cycle time
    cycles : chart cycle time
    '''
    examples = '    chart ratios'

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('chart')
        try:
            args = parser.parse_args(args)
        except:
            return
        self.refresh_data(jira, False)
        kanban = self.release.kanban()
        stories = self.release.stories(type='72')
        stories.sort(key=lambda i:i.key)
        if not args.chart or args.chart == 'cycles':
            self.cycles(stories)
        elif args.chart == 'ratios':
            self.ratios(stories)
        else:
            print 'Unknown chart type: %s' % args[0]

    def cycles(self, stories):
        data = []
        wip = []
        estimates = []
        alldata = []
        labels = []
        ratios = []
        count = [0]
        stories = [s for s in stories if s.started and s.scrum_team
           and s.scrum_team != 'Continuous Improvement ']
        stories.sort(key=lambda x:(x.points, x.cycle_time))
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
            count.append(count[-1] + 1)

        std = numpy.std([d for d in data if d])
        average = numpy.average([d for d in data if d])
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
        pyplot.plot(count[1:], nslw, '.', linestyle='-', color='y')
        pyplot.plot(count[1:], nsll, 'o', linestyle=':', color='r')
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
        pyplot.plot(count[1:], estimates, '*', linestyle='-', color='b')
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
