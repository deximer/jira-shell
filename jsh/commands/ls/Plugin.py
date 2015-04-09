import getopt
import argparse
import sets
import datetime
from zope.interface import Interface, implements
from zope.component import adapts
from zope.component import getGlobalSiteManager
from repoze.folder.interfaces import IFolder
from persistent.list import PersistentList
from ..base import BaseCommand
try:
    from ...interfaces import IRelease, IStory, IProject, ILinks, IIssues
except:
    from interfaces import IRelease, IStory, IProject, ILinks, IIssues
try:
    from ...model import humanize
except:
    from model import humanize

gsm = getGlobalSiteManager()

class Command(BaseCommand):
    help = 'List issues in a release.'
    usage = 'ls [[!]team] [-s status [...]] [-t issue_type [...]] [-p point] [-d dev [...]] -c [cycle_time] [-l [label] [...]]'
    options_help = '''    -s : Show only issues with the specified status ("!" for exclusion)
    -t : Show only issues of the specified type ("!" for exclusion)
    -d : Show issues for only the specified developers
    -o : Order (sort) results by
    -p : Show issues with the specified point estimates
    -b : Show issues with backflow (5 minute grace period)
    -c : Show issues with cycle times over the specified amount
    -l : Show issues with specifid label(s)
    '''
    examples = '''    ls
    ls Appif 
    ls !Appif 
    ls Core -d joe bill -t 78 1
    ls Math -s !6 -t 72 -c 12'''

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
        parser.add_argument('-c', nargs='*', required=False,
            help='show issues with cycle times over the specified amount')
        parser.add_argument('-l', nargs='*', required=False,
            help='show issues with specified labels')
        parser.add_argument('team', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        issues = 0
        points = 0
        epic_points = 0
        query_points = []
        now = datetime.datetime.now()
        if args.p:
            query_points = [float(p) for p in args.p]
        hide_status = []
        show_status = []
        if args.s:
            for arg in args.s:
                try:
                    if arg[:1] == '!':
                        hide_status.append(int(arg[1:]))
                    else:
                        show_status.append(int(arg))
                except ValueError:
                    if arg[:1] == '!':
                        arg = arg[1:]
                    print 'Error: %s is an invalid status' % arg
                    return
        print 'Key'.ljust(10), \
              'ATP Date:'.ljust(10), \
              'Rank:'.ljust(6), \
              'Pts:'.ljust(5), \
              'Stat:'.ljust(5), \
              'CT:'.ljust(4), \
              'Type:'.ljust(5), \
              'Bugs:'.ljust(5), \
              'ATP:'.ljust(5), \
              'Title:'
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
        if args.c:
            limit = int(args.c[0])
            stories = [s for s in stories if s.cycle_time > limit]
        if args.l:
            labels = sets.Set(args.l)
            stories =[s for s in stories if labels.issubset(sets.Set(s.labels))]
        sorting = []
        if stories and args.o:
            for field in args.o:
                if hasattr(stories[0], field):
                    sorting.append(field)
        if not sorting:
            sorting = ['scrum_team']
        def compare(a, b):
            if not a[0]:
                return -1
            if not b[0]:
                return 1
            return cmp(a, b)

        kanban = None
        if getattr(container, 'kanban', None):
            kanban = container.kanban()
        for story in sorted(stories, key=lambda x:tuple([getattr(x, key) \
            for key in sorting]), cmp=compare):
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
                cycle_time = str(story.cycle_time).ljust(3, '-')
                if story.history.skipped:
                    cycle_time += '}'
                else:
                    cycle_time += '>'
            else:
                cycle_time = str(story.cycle_time)
            if story.backflow:
                cycle_time = '<' + cycle_time
            else:
                cycle_time = ' ' + cycle_time
            rework = str(len(story['links'].get_links('1')))
            if rework == '0':
                rework = ''
            atp = ''
            if story.status in [5, 6]:
                days = 0 
            elif kanban:
                days = int(kanban.atp(story))
                if not days:
                    days = 0
                atp = now + datetime.timedelta(days)
            else:
                days = 0
            if days == 0:
                days = ''
            rank = ''
            if kanban:
                rank = kanban.rank_depth(story)
            rank = str(rank)
            print story.key[:10].ljust(10), \
                  str(atp)[:10].ljust(10), \
                  rank.ljust(6), \
                  str(story.points).ljust(5) if story.points else ''.ljust(5), \
                  humanize(story.status).ljust(5), \
                  cycle_time.ljust(5), \
                  str(story.get_cycle_time_from(10005)).ljust(5), \
                  rework.ljust(4), \
                  str(days).ljust(5), \
                  story.title[:16]
            issues += story.stories()
            if story.points and (story.type=='7' or story.type=='N/A'):
                points += story.points
            if story.points and story.type=='71':
                epic_points += story.points
        if epic_points:
            print 'Total Issues: %d, Epic Points: %d, Story Points: %d' \
                % (issues, epic_points, points)
        else:
            print 'Total Issues: %d, Story Points: %d' % (issues, points)


class IDirectoryListItem(Interface):
    pass


class IssuesAdapter(dict):
    implements(IDirectoryListItem)
    adapts(IIssues)

    def __init__(self, issues):
        self.issues = issues
        self.key = issues.key
        self.scrum_team = 'N/A'
        self.cycle_time = 'N/A'
        self.started = 'N/A'
        self.resolved = 'N/A'
        self.points = None
        self.status = ''
        self.type = 'DB'
        self.title = 'Issues DB'
        self.backflow = False
        class FakeLinks:
            def __init__(self, issues):
                self.issues = issues

            def get_links(self, link_type):
                result = []
                return result
        self['links'] = FakeLinks(self.issues)

    def stories(self):
        return 0


class ProjectAdapter(dict):
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
        self.status = ''
        self.type = project.process[:5]
        if hasattr(project, 'name'):
            self.title = project.name
        else:
            self.title = 'Project %s' % self.key
        self.backflow = False
        class FakeLinks:
            def __init__(self, project):
                self.project = project

            def get_links(self, link_type):
                result = []
                return result
        self['links'] = FakeLinks(self.project)

    def stories(self):
        return 0


class ReleaseAdapter(dict):
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
        self.title = self.release.name
        self.backflow = False
        class FakeLinks:
            def __init__(self, release):
                self.release = release

            def get_links(self, link_type):
                result = []
                for s in self.release.stories():
                    result.append(s['links'].get_links(link_type))
                return result
        self['links'] = FakeLinks(self.release)

    def stories(self):
        return len(self.release.stories())


class StoryAdapter(dict):
    implements(IDirectoryListItem)
    adapts(IStory)

    def __init__(self, story):
        self.story = story
        self['links'] = story['links']
        if not hasattr(story, 'labels'):
            self.story.labels = PersistentList()

    def __getattr__(self, attr):
        return getattr(self.story, attr)

    def stories(self):
        return 1


class LinksAdapter(dict):
    implements(IDirectoryListItem)
    adapts(ILinks)

    def __init__(self, links):
        self.project = links
        self.key = 'links'
        self.scrum_team = 'N/A'
        self.cycle_time = 'N/A'
        self.started = 'N/A'
        self.resolved = 'N/A'
        self.points = None
        self.status = None
        self.type = 'N/A'
        self.title = 'Links'
        self.backflow = False
        class FakeLinks:
            def __init__(self, project):
                self.project = project

            def get_links(self, link_type):
                result = []
                return result
        self['links'] = FakeLinks(self.project)

    def stories(self):
        return 0


class FolderAdapter(dict):
    implements(IDirectoryListItem)
    adapts(IFolder)

    def __init__(self, folder):
        self.folder = folder
        self.key = folder.key
        self.scrum_team = 'N/A'
        self.cycle_time = 'N/A'
        self.started = 'N/A'
        self.resolved = 'N/A'
        self.points = None
        self.status = None
        self.type = 'N/A'
        self.title = 'Links out'
        self.backflow = False
        class FakeLinks:
            def __init__(self, folder):
                self.folder = folder

            def get_links(self, link_type):
                result = []
                return result
        self['links'] = FakeLinks(self.folder)

    def stories(self):
        return 0


gsm.registerAdapter(IssuesAdapter)
gsm.registerAdapter(ReleaseAdapter)
gsm.registerAdapter(ProjectAdapter)
gsm.registerAdapter(StoryAdapter)
gsm.registerAdapter(LinksAdapter)
gsm.registerAdapter(FolderAdapter)
