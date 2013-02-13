import numpy
import transaction
import time
import datetime
from dateutil.rrule import DAILY, MO, TU, WE, TH, FR, rrule
from zope.interface import Interface, implements
from repoze.folder import Folder
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
from interfaces import IRelease, IStory, IProject, IKanban

NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
ITEMS = './/*/item'
STORY_POINTS = './/*[@id="customfield_10792"]/*/customfieldvalue'
IN_PROGRESS = './/*[@id="customfield_13434"]/*/customfieldvalue'
DEVELOPER = './/*[@id="customfield_13435"]/*/customfieldvalue'
STATUS = 'status'
BUG_TYPE = '1'
PRODUCTION_BUG_TYPE = '78'
STORY_TYPE = '72'
TITLE = 'title'
ASSIGNEE = 'assignee'
TYPE = 'type'
DESCRIPTION = 'description'
KEY = 'key'
RESOLVED = 'resolved'
CREATED = 'created'
COMPONENTS = 'component'
SCRUM_TEAM = './/*[@id="customfield_11261"]/*/customfieldvalue'
STATUS_OPEN = 1
STATUS_READY = 10089
STATUS_IN_PROGRESS = 3
STATUS_REOPENED = 4
STATUS_COMPLETED = 10090
STATUS_QA_READY = 10104
STATUS_QA_ACTIVE = 10092
STATUS_READY_FOR_PO = 10036
STATUS_VERIFIED = 10036
STATUS_CLOSED = 6
KANBAN = [STATUS_OPEN, STATUS_READY, STATUS_REOPENED, STATUS_IN_PROGRESS,
    STATUS_COMPLETED, STATUS_QA_READY, STATUS_QA_ACTIVE, STATUS_VERIFIED,
    STATUS_CLOSED]

class Link(Folder):
    def __init__(self, story, type):
        super(Link, self).__init__()
        self.target = story
        self.type = type


class Links(Folder):
    def __init__(self):
        super(Links, self).__init__()
        self.data = PersistentList()

    def has_link(self, key):
        for link in self.data:
            if link.key == key:
                return True
        return False

    def get_links(self, link_type):
        results = []
        for link in self.data:
            if link.type == link_type:
                results.append(link)
        return results


class History(Folder):
    def __init__(self, obj=None):
        super(History, self).__init__()
        self.data = []
        if not obj:
            return
        self.start_at = obj['startAt']
        previous_date = days = None
        for transaction in obj['histories']:
            for transition in transaction['items']:
                if transition['field'] == 'status':
                    created = datetime.datetime.fromtimestamp(time.mktime(
                        time.strptime(transaction['created'][:23],
                        '%Y-%m-%dT%H:%M:%S.%f')))
                    if previous_date:
                        days = (created - previous_date).days
                    self.data.append((created,
                                      int(transition['from']),
                                      int(transition['to']),
                                      days))
                    previous_date = created

    def get_transition(self, state):
        results = []
        for transition in self.data:
            if transition[2] == state:
                results.append(transition[0])
        return results

    def _get_started(self):
        start_dates = self.get_transition(3)
        open_dates = self.get_transition(1)
        if start_dates:
            if open_dates and (open_dates[-1] - start_dates[-1]).days > 0:
                return None
            return start_dates[-1]
        return None

    def _get_resolved(self):
        dates = self.get_transition(6)
        if dates:
            return dates [-1]
        return None

    def _get_backflow(self):
        previous = None
        for date, begin, end, days in self.data:
            if previous:
                if (date - previous).total_seconds() <= 300:
                    continue
            try:
                if KANBAN.index(begin) > KANBAN.index(end):
                    return True
            except ValueError:
                pass # Likely a state not in the KANBAN maybe from another
                     # project, e.g. MTQA
            previous = date
        return False


    started = property(_get_started)
    resolved = property(_get_resolved)
    backflow = property(_get_backflow)

class Story(Folder):
    implements(IStory)

    def __init__(self, key=None):
        super(Story, self).__init__()
        self.links = Links()
        self.key = key

    def _get_cycle_time_with_weekends(self):
        if self.started and self.resolved:
            delta = self.resolved - self.started
            return delta.days
        elif self.started and not self.resolved:
            delta = datetime.datetime.today() - self.started
            return delta.days
        return None

    def _get_cycle_time(self):
        if self.started and self.resolved:
            resolved = self.resolved
        elif self.started:
            resolved = datetime.datetime.today()
        else:
            return None
        cycle_time = rrule(DAILY, dtstart=self.started, until=resolved,
            byweekday=(MO, TU, WE, TH, FR)).count() - 1
        if cycle_time < 0:
            return 0
        return cycle_time

    def _get_lead_time(self):
        if self.created and self.resolved:
            resolved = self.resolved
        elif self.created:
            resolved = datetime.datetime.today()
        else:
            return None
        return rrule(DAILY, dtstart=self.created, until=resolved,
            byweekday=(MO, TU, WE, TH, FR)).count() - 1

    def _get_started(self):
        return self.history.started

    def _get_resolved(self):
        return self.history.resolved

    def _get_backflow(self):
        return self.history.backflow

    cycle_time = property(_get_cycle_time)
    cycle_time_with_weekends = property(_get_cycle_time_with_weekends)
    lead_time = property(_get_lead_time)
    started = property(_get_started)
    resolved = property(_get_resolved)
    backflow = property(_get_backflow)


class Kanban(object):
    implements(IKanban)

    def __init__(self):
        self.stories = []
        self.release = None
        self.grid = {}

    def add(self, story):
        self.stories.append(story)
        status = str(story.status)
        team = 'Everything Else'
        if hasattr(story, 'scrum_team'):
            team = story.scrum_team
        if not self.grid.has_key(team):
            self.grid[team] = {status: {
                'wip': story.points or 0.0,
                'stories': [story],
                'largest': story.points}}
        elif not self.grid[team].has_key(status):
            self.grid[team][status] = {
                'wip': story.points or 0.0,
                'stories': [story],
                'largest': story.points}
        else:
            if story.points is not None:
                self.grid[team][status]['wip'] += story.points
            self.grid[team][status]['stories'].append(story)
            if self.grid[team][status]['largest'] < story.points:
                self.grid[team][status]['largest'] = story.points

    def add_release(self, release):
        self.release = release
        for story in release.values():
            self.add(story)

    def average_lead_time(self, component=None, type=['72']):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        days = []
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if not story.created or not story.resolved:
                continue
            delta = story.resolved - story.created
            days.append(delta.days)
        if not days:
            return None
        return round(numpy.average(numpy.array(days)), 1)

    def average_cycle_time(self, component=None, type=['72']):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        days = []
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if not story.started or not story.resolved:
                continue
            delta = story.resolved - story.started
            days.append(delta.days)
        if not days:
            return None
        return round(numpy.average(numpy.array(days)), 1)

    def median_lead_time(self, component=None, type=['72']):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        days = []
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if not story.created or not story.resolved:
                continue
            delta = story.resolved - story.created
            days.append(delta.days)
        if not days:
            return None
        return numpy.median(numpy.array(days))

    def median_cycle_time(self, component=None, type=['72']):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        days = []
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if not story.started or not story.resolved:
                continue
            delta = story.resolved - story.started
            days.append(delta.days)
        if not days:
            return None
        return numpy.median(numpy.array(days))

    def stdev_lead_time(self, component=None, type=['72']):
        ''' Uses ddof=1 to sync std calc with excel's
        '''
        stories = self.release.stories(type)
        if not stories:
            return None
        cycle_times = []
        for story in stories:
            if component and component not in story.components:
                continue
            if not story.type in type:
                continue
            if not story.created or not story.resolved:
                continue
            delta = story.resolved - story.created
            cycle_times.append(delta.days)
        return round(numpy.std(numpy.array(cycle_times), ddof=1), 1)

    def stdev_cycle_time(self, component=None):
        ''' Uses ddof=1 to sync std calc with excel's
        '''
        if not self.release.stories():
            return None
        cycle_times = []
        for story in self.release.stories():
            if component and component not in story.components:
                continue
            if not story.started or not story.resolved:
                continue
            delta = story.resolved - story.started
            cycle_times.append(delta.days)
        return round(numpy.std(numpy.array(cycle_times), ddof=1), 1)

    def variance_cycle_time(self, component=None):
        if not self.release.stories():
            return None
        cycle_times = []
        for story in self.release.stories():
            if component and component not in story.components:
                continue
            if not story.started or not story.resolved:
                continue
            cycle_times.append(story.cycle_time)
        return round(numpy.var(cycle_times), 1)

    def squared_cycle_times(self, component=None):
        if not self.release.stories():
            return None
        cycle_times = []
        average_cycle_time = self.average_cycle_time()
        for story in self.release.stories():
            if component and component not in story.components:
                continue
            if not story.started or not story.resolved:
                continue
            cycle_times.append(story.cycle_time - average_cycle_time)
        return round(sum([c*c for c in cycle_times]), 4)


    def cycle_time_per_point(self, component=None):
        ''' Note that this method does not just add up the cycle times
            and the points and divide the former by the later (ct/pts). It
            first calculates the cycle per point per story, then divides
            the total by the number of stories. This makes results here
            consistent with other results that report cycle times for
            individual stories. It also keeps the calulation of cycle time
            per story point close to the actual work. i.e. a 2 point story
            with a 50 day cycle time will have a greater impact on the average
            using this method. This better surfaces variance.
        '''
        if not self.release.stories():
            return None
        days = []
        for story in self.release.stories():
            if component and component not in story.components:
                continue
            if not story.started or not story.resolved or not story.points:
                continue
            delta = story.resolved - story.started
            days.append(delta.days/story.points)
        return numpy.average(numpy.array(days))

    def stdev_cycle_time_per_point(self, component=None):
        ''' See doc string for cycle_time_per_point re: calculations
            Uses ddof=1 to sync std calc with excel's
        '''
        if not self.release.stories():
            return None
        days = []
        for story in self.release.stories():
            if component and component not in story.components:
                continue
            if not story.started or not story.resolved or not story.points:
                continue
            delta = story.resolved - story.started
            days.append(delta.days/story.points)
        return numpy.std(numpy.array(days), ddof=1)

    def average_cycle_time_for_estimate(self, estimate):
        grid = self.release.stories_by_estimate()
        days = []
        if not grid.has_key(estimate):
            return None
        for story in grid[estimate]:
            if story.cycle_time:
                days.append(story.cycle_time)
        if not days:
            return None
        return numpy.average(numpy.array(days))

    def stdev_cycle_time_for_estimate(self, estimate):
        grid = self.release.stories_by_estimate()
        days = []
        if not grid.has_key(estimate):
            return None
        for story in grid[estimate]:
            if not story.started or not story.resolved or not story.points:
                continue
            delta = story.resolved - story.started
            days.append(delta.days)
        return numpy.std(numpy.array(days))

    def minimum_atp(self, estimate):
        grid = self.release.stories_by_estimate()
        days = []
        if not grid.has_key(estimate):
            return None
        for story in grid[estimate]:
            if not story.started or not story.resolved or not story.points:
                continue
            delta = story.resolved - story.started
            days.append(delta.days)
        if not days:
            return None
        return round(numpy.min(numpy.array(days)), 1)

    def contingency_average(self, key):
        story = self.release.get(key)
        average = self.average_cycle_time_for_estimate(str(story.points))
        if not average:
            return None
        if story.cycle_time:
            return round(average - story.cycle_time, 1)
        return round(average, 1)

    def contingency_inside(self, key):
        story = self.release.get(key)
        average = self.average_cycle_time_for_estimate(str(story.points))
        if not average:
            return None
        std2 = self.stdev_cycle_time_for_estimate(str(story.points))
        if not std2:
            return None
        inside = average - (std2 * 2)
        min_atp = self.minimum_atp(str(story.points))
        if inside < min_atp:
            inside = min_atp
        if story.cycle_time:
            inside = inside - story.cycle_time
        return round(inside, 1)

    def contingency_outside(self, key):
        story = self.release.get(key)
        average = self.average_cycle_time_for_estimate(str(story.points))
        if not average:
            return None
        std = self.stdev_cycle_time_for_estimate(str(story.points))
        if not std:
            return None
        outside = average + (std * 2)
        if story.cycle_time:
            return round(outside - story.cycle_time, 1)
        return round(outside, 1)


class Release(Folder):
    implements(IRelease)

    WIP = {'In Progress': 3, 'Complete': 10090, 'QA Active': 10092,
           'Ready for QA': 10104, 'Ready for PO': 10036}

    def __init__(self, version=None):
        super(Release, self).__init__()
        self.version = version

    def __key(self):
        return (self.version)

    def __eq__(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def has_key(self, key):
        if key in self.keys():
            return True
        return False

    def process_raw_key(self, key):
        if key.isdigit():
            key = 'NG-%s' % key
        return key.strip()

    def add_story(self, story):
        if story.key in self.keys():
            del self[story.key]
        self.add(story.key, story)

    def get(self, key):
        key = self.process_raw_key(key)
        if self.has_key(key):
            return self[key]
        return None

    def tasked_teams(self):
        teams = {}
        for story in self.stories():
            team = story.scrum_team if story.scrum_team else 'Everything Else'
            if team not in teams:
                teams[team] = 1
            else:
                teams[team] += 1
        return teams

    def developers(self):
        developers = {}
        for story in self.stories():
            if story.developer not in developers:
                developers[story.developer] = 1
            else:
                developers[story.developer] += 1
        return developers

    def stories(self, type=['72']):
        return [story for story in self.values() if story.type in type]

    def started_stories(self, type=['72']):
        return [story for story in self.stories(type) if story.started]

    def resolved_stories(self, type=['72']):
        return [story for story in self.stories(type) if story.resolved]

    def bugs(self):
        return [story for story in self.stories([BUG_TYPE,PRODUCTION_BUG_TYPE])]

    def only_groomed_stories(self):
        return [story for story in self.stories() if story.points]

    def stories_by_estimate(self, estimate=None):
        result = {}
        for story in self.stories():
            if not story.points:
                continue
            points = str(story.points)
            if result.has_key(points):
                result[points].append(story)
            else:
                result[points] = [story]
        return result

    def stories_by_status(self):
        result = {}
        for story in self.stories():
            if not story.status:
                continue
            status = str(story.status)
            if result.has_key(status):
                result[status].append(story)
            else:
                result[status] = [story]
        return result

    def total_stories(self):
        return len(self.stories())

    def total_points(self):
        return sum([story.points for story in self.stories()
            if story.points])

    def points_completed(self):
        points = 0
        for story in self.stories():
            if story.status == 6 and story.points:
                points += story.points
        return points

    def average_story_size(self):
        points = []
        for story in self.stories():
            if story.points:
                points.append(story.points)
        return numpy.average(numpy.array(points))

    def std_story_size(self):
        ''' Uses ddof=1 to sync std calc with excel's
        '''
        points = []
        for story in self.stories():
            if story.points:
                points.append(story.points)
        return numpy.std(numpy.array(points), ddof=1)

    def sort_by_size(self):
        return sorted(self.only_groomed_stories(),
            key=lambda x: x.points, reverse=True)

    def stories_in_process(self):
        stories = 0
        for story in self.stories():
            if story.status in self.WIP.values() and story.points:
                stories += 1
        return stories

    def wip(self):
        points = 0
        for story in self.stories():
            if story.status in self.WIP.values() and story.points:
                points += story.points
        return points

    def wip_by_status(self):
        tallies = {}
        for story in self.stories():
            if story.status in self.WIP.values() and story.points:
                if str(story.status) not in tallies:
                    tallies[str(story.status)] = \
                        {'wip': story.points, 'stories': 1}
                else:
                    tallies[str(story.status)]['wip'] += story.points
                    tallies[str(story.status)]['stories'] += 1
        return tallies

    def wip_by_component(self):
        tallies = {}
        for story in self.stories():
            if story.status in self.WIP.values() and story.points:
                team = story.scrum_team
                if not team:
                    team = 'Everything Else'
                if not tallies.has_key(team):
                    tallies[team] = {'wip': story.points, 'stories': 1,
                        'largest': story.points}
                else:
                    tallies[team]['wip'] += story.points
                    tallies[team]['stories'] += 1
                    if tallies[team]['largest'] < story.points:
                        tallies[team]['largest'] = story.points
        return tallies

    def kanban(self):
        kanban = Kanban()
        kanban.add_release(self)
        return kanban

    def graph_kanban(self, swimlane=None):
        kanban = self.kanban().grid
        points = []
        wip = {}
        for status in KANBAN:
            wip[str(status)] = 0.0
        total = 0.0
        for component in kanban:
            if swimlane and swimlane != component:
                continue
            for status in kanban[component]:
                if not wip.has_key(str(status)):
                    wip[str(status)] = kanban[component][status]['wip']
                else:
                    wip[str(status)] += kanban[component][status]['wip']
                if kanban[component][status]['wip'] is not None:
                    total += kanban[component][status]['wip']

        short_wip = {}
        short_wip['start'] = wip['1'] + wip['10104']
        short_wip['middle'] = wip['3'] + wip['10092'] + wip['4'] \
            + wip['10036'] + wip['10090'] + wip['10089']
        short_wip['done'] = wip['6']
        for status in ['start', 'middle', 'done']:
            if total == 0.0:
                points.append('_')
                continue
            value = short_wip[status]/total
            if value == 0.0:
                points.append('_')
            elif value <= 0.25:
                points.append('.')
            elif value > 0.25 and value <= 0.5:
                points.append('o')
            elif value > 0.5:
                points.append('O')
        return ''.join(points)

    def upper_percentiles(self, percentile, type):
        stories = self.stories(type)
        if not stories:
            []
        stories.sort(key=lambda x:x.cycle_time if x.type !='1' else x.lead_time)
        index = int(round(percentile * len(stories) + 0.5))
        if index > 1:
            return [s for s in stories[index-1:]]
        return []


class Project(Folder):
    implements(IProject)

    def __init__(self, key=None, name=None, owner=None):
        super(Project, self).__init__()
        self.name = name
        self.key = key
        self.owner = owner

class Projects(object):
    def __init__(self):
        self.data = []

    def add(self, project):
        self.data.append(project)

    def all_projects(self):
        return self.data
