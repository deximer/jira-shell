import getopt
import curses

class Command(object):
    def run(self, jira, args):
        opts, args = getopt.getopt(args, '1:', ())
        window = curses.initscr()
        quit = False
        print 'Retrieving data...'
        self.refresh_data(jira, False)
        command = 'swimlanes'
        c = 0
        while not quit:
            window.clear()
            if command == 'swimlanes':
                self.top_swimlanes(jira, window)
            else:
                self.top_issues(jira, window)
            window.refresh()
            c = window.getch()
            if chr(c) == '!':
                window.clear()
                window.addstr(1,0, 'Retriving data...                         ')
                window.refresh()
                self.refresh_data(jira, True)
                continue
            elif chr(c) == 'l':
                command = 'swimlanes'
            elif chr(c) == 'i':
                 command = 'issues'
            else:
                quit = True
        curses.endwin()

    def top_issues(self, jira, window):
        count = 2
        window.addstr(count,0, 'ID', curses.A_REVERSE)
        window.addstr(count,10, 'Pts', curses.A_REVERSE)
        window.addstr(count,16, 'Sta', curses.A_REVERSE)
        window.addstr(count,22, 'Components', curses.A_REVERSE)
        for story in self.release.data[:20]:
            count += 1
            window.addstr(count,0, story.key)
            window.addstr(count,10, str(story.points))
            window.addstr(count,16, str(story.status))
            window.addstr(count,22, ' '.join(story.components))
        window.addstr(0,0, 'Release 2.5, 8 days remaining')
        window.addstr(1,3, '!=refresh')
        window.addstr(1,0, '?  ')
        window.addstr(1,0, '')
        window.refresh()

    def top_swimlanes(self, jira, window):
        count = 2
        graph = self.release.graph_kanban()
        window.addstr(1,77, graph)
        window.addstr(count,0, 'Key', curses.A_REVERSE)
        window.addstr(count,4, 'Lane', curses.A_REVERSE)
        window.addstr(count,24, 'WIP', curses.A_REVERSE)
        window.addstr(count,30, '#', curses.A_REVERSE)
        window.addstr(count,34, 'S>s', curses.A_REVERSE)
        lanes = self.release.wip_by_component()
        total_wip = 0
        total_stories = 0
        for lane in lanes:
            count += 1
            window.addstr(count, 0, chr(count + 94) + ':')
            window.addstr(count, 4, lane)
            window.addstr(count, 24, str(lanes[lane]['wip']))
            window.addstr(count, 30, str(lanes[lane]['stories']))
            window.addstr(count, 34, str(lanes[lane]['largest']))
            window.addstr(count, 77, self.release.graph_kanban(lane))
            total_stories += lanes[lane]['stories']
            total_wip += lanes[lane]['wip']
        window.addstr(0,0, 'Release 2.5, 8 days remaining')
        window.addstr(1,3, '!=refresh, Total WIP: %s in %s stories'
            % (total_wip, total_stories))
        window.addstr(1,0, '')
        window.refresh()
        

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
