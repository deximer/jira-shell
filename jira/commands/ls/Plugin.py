import getopt
import argparse
from zope.interface import Interface, implements
from zope.component import adapts
from zope.component import getGlobalSiteManager
from ..base import BaseCommand
from interfaces import IRelease, IStory, IProject
from model import Story

gsm = getGlobalSiteManager()

class Command(BaseCommand):
    help = 'List issues in a release.'
    usage = 'ls [[!]team] [-s status [...]] [-t issue_type [...]] [-p point] [-d dev [...]]'
    options_help = '''    -s : Show only issues with the specified status ("!" for exclusion)
    -t : Show only issues of the specified type ("!" for exclusion)
    -d : Show issues for only the specified developers
    -o : Order (sort) results by
    -p : Show issues with the specified point estimates
    -b : Show issues with backflow (5 minute grace period)
    '''
    examples = '''    ls
    ls Appif 
    ls !Appif 
    ls Core -d joe bill -t 78 1
    ls Math -s !6 -t 72'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', nargs='*', required=False,
            help='show only issues with the specified status (! for exclusion)')
        parser.add_argument('-t', nargs='*', required=False,
            help='show only issues of the specified type (! for exclusion)')
        parser.add_argument('-o', nargs='*', required=False,
            help='Sorting criteria')
        parser.add_argument('-p', nargs='*', required=False,
            help='show issues with the specified point estimates')
        parser.add_argument('-d', nargs='*', required=False,
            help='show issues for only the specified developers')
        parser.add_argument('-b', action='store_true', required=False,
            help='show issues with backflow (5 minute grace period)')
        parser.add_argument('team', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        print 'Key'.ljust(10), \
              'Team:'.ljust(18), \
              'Pts:'.ljust(5), \
              'Stat:'.ljust(5), \
              'CT:'.ljust(5), \
              'Type:'.ljust(5), \
              'Bugs:'.ljust(5), \
              'Cont:'.ljust(5), \
              'Title:'
        issues = 0
        points = 0
        epic_points = 0
        query_points = []
        if args.p:
            query_points = [float(p) for p in args.p]
        hide_status = []
        show_status = []
        if args.s:
            for arg in args.s:
                if arg[:1] == '!':
                    hide_status.append(int(arg[1:]))
                else:
                    show_status.append(int(arg))
        hide_type = []
        show_type = []
        if args.t:
            for arg in args.t:
                if arg[:1] == '!':
                    hide_type.append(arg[1:])
                else:
                    show_type.append(arg)
        container = jira.cache.get_by_path(jira.cache.cwd)
        stories = [IDirectoryListItem(s) for s in container.values()]
        sorting = []
        if stories and args.o:
            for field in args.o:
                if hasattr(stories[0], field):
                    sorting.append(field)
        if not sorting:
            sorting = ['scrum_team']
        for story in sorted(stories, key=lambda x:tuple([getattr(x, key) for key in sorting])):
            try:
                story = IDirectoryListItem(story)
            except TypeError:
                pass
            if show_status and story.status not in show_status:
                continue
            if hide_status and story.status in hide_status:
                continue
            if show_type and story.type not in show_type:
                continue
            if hide_type and story.type in hide_type:
                continue
            if args.p and story.points not in query_points:
                continue
            if args.d:
                if not story.developer:
                    continue
                skip = False
                for dev in args.d:
                    if story.developer[:len(dev)] not in args.d:
                         skip = True
                         break
                if skip:
                    continue
            if args.b and not story.backflow:
                continue
            if not story.scrum_team:
                story.scrum_team = 'Everything Else'
            if args.team:
                if args.team[0] == '!':
                    if story.scrum_team[:len(args.team[1:])]==args.team[1:]:
                        continue
                else:
                    if story.scrum_team[:len(args.team)] != args.team:
                        continue

            team = story.scrum_team
            if not team:
                team = 'Everything Else'
            if not story.cycle_time:
                cycle_time = ''
            elif not story.resolved:
                cycle_time = str(story.cycle_time).ljust(3, '-') + '>'
            else:
                cycle_time = str(story.cycle_time)
            if story.backflow:
                cycle_time = '<' + cycle_time
            else:
                cycle_time = ' ' + cycle_time
            rework = str(len(story.links.get_links('1')))
            if rework == '0':
                rework = ''
            if story.status == 6:
                contingency = ''
            elif getattr(container, 'kanban', None):
                contingency = container.kanban().contingency_average(story.key)
                if not contingency:
                    contingency = ''
            else:
                contingency = ''
            print story.key[:10].ljust(10), \
                  team[:18].ljust(18), \
                  str(story.points).ljust(5) if story.points else ''.ljust(5), \
                  str(story.status).ljust(5), \
                  cycle_time.ljust(5), \
                  str(story.type).ljust(5), \
                  rework.ljust(5), \
                  str(contingency).ljust(5), \
                  story.title[:14]
            issues += story.stories()
            if story.points and (story.type=='72' or story.type=='N/A'):
                points += story.points
            if story.points and story.type=='71':
                epic_points += story.points
        if epic_points:
            print 'Total Issues: %d, Epic Points %d, Story Points: %d' \
                % (issues, epic_points, points)
        else:
            print 'Total Issues: %d, Story Points: %d' % (issues, points)


class IDirectoryListItem(Interface):
    pass


class ProjectAdapter(object):
    implements(IDirectoryListItem)
    adapts(IProject)

    def __init__(self, project):
        self.project = project
        self.key = project.key
        self.scrum_team = 'N/A'
        self.cycle_time = 'N/A'
        self.started = 'N/A'
        self.resolved = 'N/A'
        self.points = None
        self.status = None
        self.type = 'N/A'
        self.title = 'Project %s' % self.key
        self.backflow = False
        class FakeLinks:
            def __init__(self, project):
                self.project = project

            def get_links(self, link_type):
                result = []
                return result
        self.links = FakeLinks(self.project)

    def stories(self):
        return 0


class ReleaseAdapter(object):
    implements(IDirectoryListItem)
    adapts(IRelease)

    def __init__(self, release):
        self.release = release
        self.key = release.version
        self.scrum_team = 'N/A'
        self.cycle_time = self.release.kanban().average_cycle_time()
        self.started = 'N/A'
        self.resolved = 'N/A'
        self.points = self.release.total_points()
        self.status = self.release.graph_kanban()
        self.type = 'N/A'
        self.title = 'Release %s' % self.key
        self.backflow = False
        class FakeLinks:
            def __init__(self, release):
                self.release = release

            def get_links(self, link_type):
                result = []
                for s in self.release.stories():
                    result.append(s.links.get_links(link_type))
                return result
        self.links = FakeLinks(self.release)

    def stories(self):
        return len(self.release.stories())


class StoryAdapter(object):
    implements(IDirectoryListItem)
    adapts(IStory)

    def __init__(self, story):
        self.story = story

    def __getattr__(self, attr):
        return getattr(self.story, attr)

    def stories(self):
        return 1


gsm.registerAdapter(ReleaseAdapter)
gsm.registerAdapter(ProjectAdapter)
gsm.registerAdapter(StoryAdapter)
