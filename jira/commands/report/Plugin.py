from ..base import BaseCommand

class Command(BaseCommand):
    help = 'Report on the current release'
    usage = 'report'

    def run(self, jira, args):
        self.refresh_data(jira, False)
        release = self.release
        kanban = self.release.kanban()
        print 'Stories          :', release.total_stories()
        print 'Bugs             :', len(release.bugs())
        print 'Average Size     :', round(release.average_story_size(), 1)
        print 'Std Dev          :', round(release.std_story_size(), 1)
        print 'Smallest Story   :', release.sort_by_size()[-1].points
        print 'Largest Story    :', release.sort_by_size()[0].points
        print 'Avg Cycle Time   :', kanban.average_cycle_time()
        print 'Points in scope  :', round(release.total_points(), 1)
        print 'Points completed :', round(release.points_completed(), 1)
        print 'Stories IP       :', release.stories_in_process()
        print 'Total WIP        :', round(release.wip(), 1)
        print
        print 'WIP by Status:'
        wip = release.wip_by_status()
        for key in wip:
            print key.ljust(16), ':', str(wip[key]['wip']).ljust(6), \
                wip[key]['stories']
        print
        print 'WIP by Swim Lane:'
        wip = release.wip_by_component()
        for key in wip:
            print key.ljust(16), ':',  str(wip[key]['wip']).ljust(6), \
                str(wip[key]['stories']).ljust(3), wip[key]['largest']

    def refresh_data(self, jira, refresh):
        self.release = jira.get_release(refresh)
