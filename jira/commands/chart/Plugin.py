import getopt
import curses
import spc
from matplotlib import pyplot
from commands.base import BaseCommand

class Command(BaseCommand):
    help = 'Render various charts based on the data'
    usage = 'chart [chart_type]'
    options_help = '''    ratios : chart ratio of estimates to cycle time
    cycles : chart cycle time
    '''
    examples = '    chart ratios'

    def run(self, jira, args):
        opts, args = getopt.getopt(args, '1:', ())
        args = args.split()
        self.refresh_data(jira, False)
        kanban = self.release.kanban()
        stories = self.release.stories()
        stories.sort(key=lambda i:i.key)
        if not args or args[0] == 'cycles':
            self.cycles(stories)
        elif args[0] == 'ratios':
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
