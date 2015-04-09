import curses
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release

class Command(BaseCommand):
    help = 'Display control panel of critical release data'
    usage = 'top'

    def run(self, jira, args):
        quit = False
        self.release = jira.cache.get_by_path(jira.cache.cwd)
        if not isinstance(self.release, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        window = curses.initscr()
        command = 'wip'
        c = 0
        while not quit:
            window.clear()
            if command == 'wip':
                self.top_wip(jira, window)
            else:
                self.top_issues(jira, window)
            window.refresh()
            c = window.getch()
            if chr(c) == 'q':
                quit = True
        curses.endwin()

    def top_wip(self, jira, window):
        count = 2
        graph = self.release.graph_kanban()
        window.addstr(1,77, graph)
        window.addstr(count,0, 'Key', curses.A_REVERSE)
        window.addstr(count,4, 'Team', curses.A_REVERSE)
        window.addstr(count,24, 'WIP', curses.A_REVERSE)
        window.addstr(count,30, '#', curses.A_REVERSE)
        window.addstr(count,34, 'S>s', curses.A_REVERSE)
        window.addstr(count,39, 'ACT', curses.A_REVERSE)
        lanes = self.release.wip_by_component()
        kanban = self.release.kanban()
        total_wip = 0
        total_stories = 0
        for lane in lanes:
            count += 1
            if count >= 23:
                break
            window.addstr(count, 0, chr(count + 94) + ':')
            window.addstr(count, 4, lane[:19])
            window.addstr(count, 24, str(round(lanes[lane]['wip'], 1)))
            window.addstr(count, 30, str(lanes[lane]['stories']))
            window.addstr(count, 34, str(round(lanes[lane]['largest'], 1)))
            window.addstr(count, 39, str(kanban.average_cycle_time(lane)))
            window.addstr(count, 77, self.release.graph_kanban(lane))
            total_stories += lanes[lane]['stories']
            total_wip += lanes[lane]['wip']
        window.addstr(0,0, 'Release 2.5, 8 days remaining')
        window.addstr(1, 3,
            '!=refresh, Total WIP: %s in %s stories, Done: %s, ACT %s'
            % (total_wip, total_stories, self.release.points_completed(),
            kanban.average_cycle_time()))
        window.addstr(1,0, '')
        window.refresh()
