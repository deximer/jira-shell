import curses
from ..base import BaseCommand
from model import Release

class Command(BaseCommand):
    help = 'Export release data to csv files'
    usage = 'export'

    def run(self, jira, args):
        self.release = jira.cache.get_by_path(jira.cache.cwd)
        if not isinstance(self.release, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        kanban = self.release.kanban()
        stories = self.release.stories()
        stories.sort(key=lambda i:i.key)
        export_ct = open('export-ct.csv', 'w')
        export_ct.write(
            'Team, Key, Points, Started, Resolved, Cycle Time, NSUL, NSUW, Average CT, NSLW, NSLL\r\n')
        average_cycle_time = kanban.average_cycle_time()
        for story in stories:
            if not story.started or not story.resolved:
                continue
            export_ct.write(
                '%s, %s, %.2f, %s, %s, %d, %.2f, %.2f, %.2f, %.2f, %.2f\r\n' % (
                story.scrum_team,
                story.key,
                story.points or 0.0,
                story.started.strftime("%m/%d/%y"),
                story.resolved.strftime('%m/%d/%y'),
                story.cycle_time,
                average_cycle_time + (kanban.stdev_cycle_time() * 3),
                average_cycle_time + (kanban.stdev_cycle_time() * 2),
                average_cycle_time,
                average_cycle_time - (kanban.stdev_cycle_time() * 2),
                average_cycle_time - (kanban.stdev_cycle_time() * 3)))
        export_pt = open('export-pt.csv', 'w')
        export_pt.write(
            'Team, Key, Cycle Time, Started, Resolved, Points, NSUL, NSUW, Average Pts, NSLW, NSLL\r\n')
        average_story_size = self.release.average_story_size()
        for story in stories:
            if not story.started or not story.resolved:
                continue
            export_pt.write(
                '%s, %s, %d, %s, %s, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f\r\n' % (
                story.scrum_team,
                story.key,
                story.cycle_time,
                story.started.strftime("%m/%d/%y"),
                story.resolved.strftime('%m/%d/%y'),
                story.points or 0.0,
                average_story_size + (self.release.std_story_size() * 3),
                average_story_size + (self.release.std_story_size() * 2),
                average_story_size,
                average_story_size - (self.release.std_story_size() * 2),
                average_story_size - (self.release.std_story_size() * 3)))
        export_ratio = open('export-ratio.csv', 'w')
        export_ratio.write(
            'Team, Resolved, Key, Ratio, NSUL, NSUW, Average, NSLW, NSLL\r\n')
        average_story_size = self.release.average_story_size()
        for story in stories:
            if not story.started or not story.resolved:
                continue
            export_ratio.write(
                '%s, %s, %s, %d, %.2f, %.2f, %.2f, %.2f, %.2f\r\n' % (
                story.scrum_team,
                story.resolved.strftime('%m/%d/%y'),
                story.key,
                story.cycle_time/story.points if story.points else 0,
                average_cycle_time + (kanban.stdev_cycle_time() * 3),
                average_cycle_time + (kanban.stdev_cycle_time() * 2),
                average_cycle_time,
                average_cycle_time - (kanban.stdev_cycle_time() * 2),
                average_cycle_time - (kanban.stdev_cycle_time() * 3)))
        # Export Dev charts
        developers = {}
        for story in stories:
            if not story.developer or not story.resolved or not story.started:
                continue
            if not developers.has_key(story.developer):
                developers[story.developer] = [story]
            else:
                developers[story.developer].append(story)
        export_devs = open('export-devs.csv', 'w')
        export_devs.write('Developer, Points, Cycle Time, Story\r\n')
        for key in developers:
            for story in developers[key]:
                export_devs.write('%s, %s, %.2f, %d, %s\r\n'
                 % (story.scrum_team,
                    key,
                    story.points or 0.0,
                    story.cycle_time,
                    story.key))
