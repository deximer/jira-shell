import getopt
import curses
import spc
from matplotlib import pyplot
from commands.base import BaseCommand

class Command(BaseCommand):
    help = 'Render various charts based on the data'
    usage = 'chart [chart_type]'
    options_help = '''    ratio : chart ratio of estimates to cycle time
    cycle : chart cycle time
    '''
    examples = '    chart ratio'

    def run(self, jira, args):
        opts, args = getopt.getopt(args, '1:', ())
        args = args.split()
        self.refresh_data(jira, False)
        kanban = self.release.kanban()
        stories = self.release.stories()
        stories.sort(key=lambda i:i.key)
        if not args or args[0] == 'cycle_time':
            self.cycle_time(stories)
        elif args[0] == 'ratio':
            self.ratio(stories)

    def cycle_time(self, stories):
        data = []
        for story in stories:
            if not story.started or not story.resolved:
                continue
            data.append(story.cycle_time)
        chart = spc.Spc(data, spc.CHART_X_MR_X)
        chart.get_chart()
        pyplot.show()

    def ratio(self, stories):
        data = []
        for story in stories:
            if not story.started or not story.resolved:
                continue
            data.append(story.cycle_time/story.points if story.points else 0)
        chart = spc.Spc(data, spc.CHART_X_MR_X)
        chart.get_chart()
        pyplot.show()
