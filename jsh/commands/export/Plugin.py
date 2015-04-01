import curses
from ..base import BaseCommand
from model import Release, humanize

class Command(BaseCommand):
    help = 'Export release data to csv files'
    usage = 'export'

    def run(self, jira, args):
        self.release = jira.cache.get_by_path(jira.cache.cwd)
        if not isinstance(self.release, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        kanban = self.release.kanban()
        stories = [s for s in self.release.stories()]
        def compare(a, b):
            if not a[0]:
                return -1
            if not b[0]:
                return 1
            return cmp(a, b)
        stories = sorted(stories, key=lambda x:tuple([getattr(x, key) for key in ['status', 'rank']]), cmp=compare)
        export_ct = open('export-ct.csv', 'w')
        export_ct.write(
            'Status, Rank, Key, Points, Started, Resolved, Cycle Time, NSUL, NSUW, Average CT, NSLW, NSLL, Title, Labels\r\n')
        act = kanban.average_cycle_time()
        stdev = kanban.stdev_cycle_time()
        usl = act + stdev * 3
        usw = act + stdev * 2
        lsl = act - stdev * 3
        lsw = act - stdev * 2
        for story in stories:
            started = ''
            resolved = ''
            if story.started:
                started = story.started.strftime("%m/%d/%y")
            if story.resolved:
                started = story.resolved.strftime("%m/%d/%y")
            cycle_time = ''
            if story.cycle_time:
                cycle_time = str(story.cycle_time)
            #if not story.started or not story.resolved:
            #    continue
            print story.key, story.title
            export_ct.write(
                '%s, %d, %s, %.2f, %s, %s, %s, %.2f, %.2f, %.2f, %.2f, %.2f, %s, %s\r\n' % (
                humanize(story.status),
                kanban.rank_depth(story),
                story.key,
                story.points or 0.0,
                started,
                resolved,
                cycle_time,
                usl,
                usw,
                act,
                lsw,
                lsl,
                story.title.encode('ascii', 'ignore').encode('string-escape'),
                '; '.join(story.labels)))
