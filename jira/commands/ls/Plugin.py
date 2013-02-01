import getopt
import argparse
from zope.interface import Interface, implements
from zope.component import adapts
from zope.component import getGlobalSiteManager
from ..base import BaseCommand
from interfaces import IRelease, IStory

gsm = getGlobalSiteManager()

class Command(BaseCommand):
    help = 'List issues in a release.'
    usage = 'ls [[!]team] [-s status [status...]] [-t issue_type [issue_type...]] [-p [point]]'
    options_help = '''    -s : Show only issues with the specified status ("!" for exclusion)
    -t : Show only issues of the specified type ("!" for exclusion)
    -p : Show issues with the specified point estimates
    -b : Show issues with backflow
    '''
    examples = '''    ls
    ls App 
    ls !App 
    ls Math -s !6 -t 72'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', nargs='*', required=False)
        parser.add_argument('-t', nargs='*', required=False)
        parser.add_argument('-p', nargs='*', required=False)
        parser.add_argument('-b', action='store_true', required=False)
        parser.add_argument('team', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        #self.refresh_data(jira, False)
        print 'Key'.ljust(10), \
              'Team:'.ljust(18), \
              'Pts:'.ljust(5), \
              'Stat:'.ljust(5), \
              'CT:'.ljust(5), \
              'Type:'.ljust(5), \
              'Bugs:'.ljust(5), \
              'Title:'
        issues = 0
        points = 0
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
        for story in container.values():
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
                cycle_time = 'None'
            elif not story.resolved:
                cycle_time = str(story.cycle_time) + '>'
            else:
                cycle_time = str(story.cycle_time)
            if story.backflow:
                cycle_time = '<' + cycle_time
            print story.key[:10].ljust(10), \
                  team[:18].ljust(18), \
                  str(story.points).ljust(5), \
                  str(story.status).ljust(5), \
                  cycle_time.ljust(5), str(story.type).ljust(5), \
                  str(len(story.links.get_links('1'))).ljust(5), \
                  story.title[:20]
            if IStory.providedBy(story):
                issues += 1
            if story.points:
                points += story.points
        print 'Total Issues: %d, Total Points: %d' % (issues, points)


class IDirectoryListItem(Interface):
    pass


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


gsm.registerAdapter(ReleaseAdapter)
