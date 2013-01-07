import spc
import argparse
from matplotlib import pyplot
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
        stories = self.release.stories()
        stories.sort(key=lambda i:i.key)
        if not args.chart or args.chart == 'cycles':
            self.cycles(stories)
        elif args.chart == 'ratios':
            self.ratios(stories)
        else:
            print 'Unknown chart type: %s' % args[0]

    def cycles(self, stories):
        data = []
        for story in stories:
            if not story.started or not story.resolved:
                continue
            data.append(story.cycle_time)
        chart = spc.Spc(data, spc.CHART_X_MR_X)
        chart.get_chart()
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
