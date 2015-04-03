import numpy
from scipy import stats
import time
import datetime
import sets
from dateutil.rrule import DAILY, MO, TU, WE, TH, FR, SA, SU, rrule
from zope.interface import Interface, implements
from repoze.folder import Folder
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
from interfaces import IRelease, IStory, ILinks, IProject, IKanban, IIssues

def sort(stories, fields):
    def compare(a, b):
        if not a[0]:
            return -1
        if not b[0]:
            return 1
        return cmp(a, b)
    return [s for s in sorted(stories, key=lambda x:tuple([getattr(x, key)
        for key in fields]), cmp=compare)]

STORY_TYPE = '7'
BUG_TYPE = '1'
PRODUCTION_BUG_TYPE = '1'
TITLE = 'title'
KEY = 'key'
STATUS_OPEN = 1
STATUS_REOPENED = 4
STATUS_READY = 10024
STATUS_IN_PROGRESS = 10002
STATUS_PEER_REVIEW = 10004
STATUS_NEEDS_APPROVAL = 10014
STATUS_QA_ACTIVE = 10005
STATUS_QE_APPROVAL = 10127
STATUS_PO_APPROVAL = 10128
STATUS_RESOLVED = 5
STATUS_CLOSED = 6
KANBAN = [STATUS_OPEN, STATUS_READY, STATUS_REOPENED, STATUS_IN_PROGRESS,
    STATUS_PEER_REVIEW, STATUS_NEEDS_APPROVAL, STATUS_QA_ACTIVE, 
    STATUS_QE_APPROVAL, STATUS_PO_APPROVAL, STATUS_RESOLVED, STATUS_CLOSED]
HUMAN_STATUS = {
       1: 'New  ',
       5: 'Rslvd',
       6: 'Closd',
       10024: 'Ready',
       10002: 'Start',
       10004: 'PeerR',
       10014: 'NeedA',
       10005: 'Test ',
       10127: 'QeApp',
       10128: 'PoApp',}

def humanize(status):
    if HUMAN_STATUS.has_key(status):
        return HUMAN_STATUS[status]
    return str(status)


class Links(Folder):
    implements(ILinks)

    def __init__(self):
        super(Links, self).__init__()
        self['out'] = Folder()
        self['in'] = Folder()
        self['out'].key = 'out'
        self['in'].key = 'in'

    def has_link(self, key):
        for link in self.all:
            if link.key == key:
                return True
        return False

    def get_links(self, link_type=None, directions=['out', 'in']):
        results = []
        for direction in directions:
            for links in self[direction]:
                for issue in self[direction][links].values():
                    if not issue:
                        continue
                    if link_type and issue.type != link_type:
                        continue
                    results.append(issue)
        return results

    def _all(self):
        return self.get_links()

    def _outward(self):
        return self.get_links(directions=['out'])

    def _inward(self):
        return self.get_links(directions=['in'])

    all = property(_all)
    outward = property(_outward)
    inward = property(_inward)


class History(Folder):
    def __init__(self, obj=None):
        super(History, self).__init__()
        self.data = PersistentList()
        if not obj:
            return
        self.start_at = obj.startAt
        for transaction in obj.histories:
            for transition in transaction.items:
                if transition.field == 'status':
                    created = datetime.datetime.fromtimestamp(time.mktime(
                        time.strptime(transaction.created[:23],
                        '%Y-%m-%dT%H:%M:%S.%f')))
                    name = ''
                    author = ''
                    if hasattr(transaction, 'author'):
                        author = transaction.author.displayName
                    self.data.append((created
                        , int(getattr(transition, 'from'))
                        , int(transition.to)
                        , author))
                    previous_date = created

    def get_transition_from(self, state):
        results = []
        for transition in self.data:
            if transition[1] == state:
                results.append(transition[0])
        return results

    def get_transition_to(self, state):
        results = []
        for transition in self.data:
            if transition[2] == state:
                results.append(transition[0])
        return results

    def get_takt_time(self, start, end):
        ''' This method needs to locate the first attempt and connect it
            with a finish, or handle a backflow condition, skip ahead condition
            etc. It then needs to return as many takt completions. partial
            attempts, etc. How we measure takt time needs to be decided
        '''
        start_date = self.get_transition_to(start)
        if not start_date:
            return None
        end_date = self.get_transition_to(end)
        if not end_date:
            return None
        return None # Not implemented

    def _get_started(self):
        start_dates = self.get_transition_to(STATUS_IN_PROGRESS)
        open_dates = self.get_transition_to(STATUS_OPEN)
        if start_dates:
            if open_dates and (open_dates[-1] - start_dates[-1]).days > 0:
                return None
            return start_dates[-1]
        return None

    def _get_resolved(self):
        dates = self.get_transition_to(STATUS_CLOSED)
        if dates:
            return dates[-1]
        return None

    def _get_first_started(self):
        start_dates = self.get_transition_to(STATUS_IN_PROGRESS)
        if start_dates:
            return start_dates[0]
        return None

    def _get_backflow(self):
        previous = None
        for date, begin, end, days, name in self.all:
            if previous:
                if (date - previous).total_seconds() <= 300:
                    continue
            try:
                if KANBAN.index(begin) > KANBAN.index(end):
                    return True
            except ValueError:
                pass # Likely a state not in the KANBAN maybe from another
                     # project, e.g. MTQA <- Ok, so check it knucklehead
            previous = date
        return False

    def _get_skipped(self):
        previous = None
        steps = 0
        for date, begin, end, days, name in self.all:
            try:
                steps = KANBAN.index(end) - KANBAN.index(begin)
            except ValueError:
                pass # Likely a state not in the KANBAN maybe from another
                     # project, e.g. MTQA <- Ok, so check it knucklehead
            if steps == 2 and begin == STATUS_READY:
                return False
            elif steps > 1:
                return True
        return False

    def _all(self):
        results = []
        previous_date = None
        days = None
        for transition in self.data:
            if previous_date:
                days = rrule(DAILY, dtstart=previous_date, until=transition[0],
                            byweekday=(MO, TU, WE, TH, FR)).count() - 1
            results.append((transition[0], transition[1], transition[2], days,
                transition[3]))
            previous_date = transition[0]
        if results and results[-1][2] != 6:
            last = results[-1]
            del results[-1]
            days = rrule(DAILY, dtstart=previous_date,
                until=datetime.datetime.now(), byweekday=(
                MO, TU, WE, TH, FR)).count() - 1
            results.append((last[0], last[1], last[2], days, last[4]))
        return results

    started = property(_get_started)
    resolved = property(_get_resolved)
    first_started = property(_get_first_started)
    backflow = property(_get_backflow)
    skipped = property(_get_skipped)
    all = property(_all)

class Story(Folder):
    implements(IStory)

    def __init__(self, issue=None):
        super(Story, self).__init__()
        self['links'] = Links()
        self.updated = None
        if issue:
            self.initialize(issue)

    def initialize(self, issue):
        self.jid = getattr(issue, 'id')
        self.key = issue.key
        self.labels = PersistentList(issue.fields.labels)
        self.updated = datetime.datetime.fromtimestamp(
                time.mktime(time.strptime(
                issue.fields.updated[:23], '%Y-%m-%dT%H:%M:%S.%f')))
        self.reporter = None
        if issue.fields.reporter:
            self.reporter = issue.fields.reporter.displayName
        self.priority = None
        if issue.fields.priority:
            self.priority = issue.fields.priority.name
        self.history = History(issue.changelog)
        self.resolution = None
        if issue.fields.resolution:
            self.resolution = issue.fields.resolution.name
        self.url = issue.self
        self.title = issue.fields.summary
        self.fix_versions = PersistentList()
        for version in issue.fields.fixVersions:
            self.fix_versions.append(version.id)
        self.points = issue.fields.customfield_10003
        if not self.points:
            self.points = 0.0
        self.created = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(issue.fields.created[:23], '%Y-%m-%dT%H:%M:%S.%f')))
        self.type = issue.fields.issuetype.id
        self.type_name = issue.fields.issuetype.name
        if not issue.fields.assignee:
            self.assignee = None
            self.developer = None
        else:
            self.assignee = issue.fields.assignee.name
            self.developer = self.assignee
        self.rank = int(issue.fields.customfield_10600)
        self.root_cause = ''
        self.root_cause_details = ''
        self.scrum_team = '' # custom legacy
        self.status = int(issue.fields.status.id)
        self.project = issue.fields.project.key

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

    def _get_aggregate_cycle_time(self):
        if self.first_started and self.resolved:
            resolved = self.resolved
        elif self.first_started:
            resolved = datetime.datetime.today()
        else:
            return None
        cycle_time = rrule(DAILY, dtstart=self.first_started, until=resolved,
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

    def _get_first_started(self):
        return self.history.first_started

    def _get_resolved(self):
        return self.history.resolved

    def _get_backflow(self):
        return self.history.backflow

    cycle_time = property(_get_cycle_time)
    aggregate_cycle_time = property(_get_aggregate_cycle_time)
    cycle_time_with_weekends = property(_get_cycle_time_with_weekends)
    lead_time = property(_get_lead_time)
    started = property(_get_started)
    resolved = property(_get_resolved)
    first_started = property(_get_first_started)
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

    def average_lead_time(self, component=None, type=['7']):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        days = []
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if not story.cycle_time:
                continue
            days.append(story.cycle_time)
        if not days:
            return None
        return round(numpy.average(numpy.array(days)), 1)

    def average_cycle_times_by_type(self, type=[]):
        if hasattr(self, '__actbt'):
            return self._actbt
        stories = self.release.stories(type=type)
        if not stories:
            return {}
        result = {}
        for story in stories:
            ct = story.cycle_time
            if not ct:
                ct = 0
            if not story.type in result.keys():
                result[story.type] = [ct]
            else:
                result[story.type].append(ct)
        for key in result.keys():
            values = [v for v in result[key] if v]
            if not values:
                result[key] = 0
                continue
            result[key] = sum(values) / len(values)
        if not hasattr(self, '__actbt'):
            self._actbt = result
        return result

    def cycle_times_in_status(self, component=None, type=[], points=[]):
        stories = self.release.stories(type=type)
        if not stories:
            return {}
        result = {}
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if points and story.points not in points:
                continue
            for transition in story.history.all:
                if not transition[3]: # days
                    continue
                if not transition[1] in result.keys():
                    result[transition[1]] = transition[3]
                else:
                    result[transition[1]] += transition[3]
        return result

    def average_times_in_status(self, component=None, type=['7'], points=[]):
        stories = self.release.stories(type=type)
        if not stories:
            return {}
        result = {}
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if points and story.points not in points:
                continue
            for transition in story.history.all:
                if not transition[3]: # days
                    continue
                if not transition[1] in result.keys():
                    result[transition[1]] = [transition[3]]
                else:
                    result[transition[1]].append(transition[3])
        averages = {}
        for key in result.keys():
            averages[key] = round(numpy.average(result[key]), 1)
        return averages

    def std_times_in_status(self, component=None, type=['7'], points=[]):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        result = {}
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if points and story.points not in points:
                continue
            for transition in story.history.all:
                if not transition[3]: # days
                    continue
                if not transition[1] in result.keys():
                    result[transition[1]] = [transition[3]]
                else:
                    result[transition[1]].append(transition[3])
        averages = {}
        for key in result.keys():
            averages[key] = round(numpy.std(result[key]), 1)
        return averages

    def average_arrival_for_status(self, component=None, type=['7'],
        points=[]):
        stories = self.release.stories(type=type)
        if not stories:
            return {}
        result = {}
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if points and story.points not in points:
                continue
            for transition in story.history.all:
                if not transition[3]: # days
                    continue
                if not transition[2] in result.keys():
                    result[transition[2]] = [transition[3]]
                else:
                    result[transition[2]].append(transition[3])
        averages = {}
        for key in result.keys():
            averages[key] = round(numpy.average(result[key]), 1)
        return averages

    def std_arrival_for_status(self, component=None, type=['7'], points=[]):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        result = {}
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if points and story.points not in points:
                continue
            for transition in story.history.all:
                if not transition[3]: # days
                    continue
                if not transition[2] in result.keys():
                    result[transition[2]] = [transition[3]]
                else:
                    result[transition[2]].append(transition[3])
        averages = {}
        for key in result.keys():
            averages[key] = round(numpy.std(result[key]), 1)
        return averages

    def state_arrival_interval(self, state):
        ''' Create a plot point for every arrival into state
        '''
        dates = []
        for story in self.release.stories():
            dates.extend([d for d in story.history.get_transition_to(state)])
        if not dates:
            return []
        dates.sort()
        deltas = [{'date': dates[0], 'interval': 0}]
        previous = dates[0]
        for date in dates[1:]:
            deltas.append({'date': date,
                           'interval': (date - previous).total_seconds()})
            previous = date
        return deltas

    def all_state_arrival_intervals(self):
        result = {}
        for state in KANBAN:
            deltas = self.state_arrival_interval(state)
            result[state] = {'deltas': deltas,
                             'average': round(numpy.average(
                                 [d['interval'] for d in deltas])/60./60., 1),
                             'std': round(numpy.std(
                                 [d['interval'] for d in deltas])/60./60., 1)}
        return result

    def average_cycle_time(self, component=None, type=['7']):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        days = []
        for story in stories:
            if not story.started or not story.resolved:
                continue
            days.append(story.cycle_time)
        if not days:
            return None
        return round(numpy.average(numpy.array(days)), 1)

    def median_lead_time(self, component=None, type=['7']):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        days = []
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if not story.created or not story.resolved:
                continue
            days.append(story.lead_time)
        if not days:
            return None
        return numpy.median(numpy.array(days))

    def median_cycle_time(self, component=None, type=['7']):
        stories = self.release.stories(type=type)
        if not stories:
            return None
        days = []
        for story in stories:
            if component and component != story.scrum_team:
                continue
            if not story.started or not story.resolved:
                continue
            days.append(story.cycle_time)
        if not days:
            return None
        return numpy.median(numpy.array(days))

    def stdev_lead_time(self, component=None, type=['7']):
        ''' Uses ddof=0 because that is right and excel is wrong
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
            if not story.cycle_time:
                continue
            cycle_times.append(story.cycle_time)
        return round(numpy.std(numpy.array(cycle_times), ddof=0), 1)

    def stdev_cycle_time(self, component=None):
        ''' Uses ddof=0 because that is right and excel is wrong
        '''
        if not self.release.stories():
            return None
        cycle_times = []
        for story in self.release.stories():
            if not story.started or not story.resolved:
                continue
            cycle_times.append(story.cycle_time)
        return round(numpy.std(numpy.array(cycle_times), ddof=0), 1)

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
            days.append(story.cycle_time/story.points)
        return numpy.average(numpy.array(days))

    def stdev_cycle_time_per_point(self, component=None):
        ''' See doc string for cycle_time_per_point re: calculations
            Use ddof=0 becasue that is right and excel is wrong
        '''
        if not self.release.stories():
            return None
        days = []
        for story in self.release.stories():
            if component and component not in story.components:
                continue
            if not story.started or not story.resolved or not story.points:
                continue
            days.append(story.cycle_time/story.points)
        return numpy.std(numpy.array(days), ddof=0)

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
            if not story.cycle_time or not story.points:
                continue
            days.append(story.cycle_time)
        return numpy.std(numpy.array(days))

    def state_transition_probabilities(self):
        stories = self.release.stories()
        result = {}
        for story in stories:
            for transition in story.history.all:
                if not transition[3]:
                    continue
                if not result.has_key(transition[1]):
                    result[transition[1]] = {transition[2]: {
                        'days': [transition[3]]}}
                elif not result[transition[1]].has_key(transition[2]):
                    result[transition[1]][transition[2]] = {
                        'days': [transition[3]]}
                else:
                    result[transition[1]][transition[2]]['days'].append(
                        transition[3])
        for transition in result.values():
            for t in transition.values():
                t['average'] = round(numpy.average(t['days']), 1)
                t['std'] = round(numpy.std(t['days']), 1)

        return result

    def cycle_times_for_estimates(self, estimates=None):
        grid = self.release.stories_by_estimate()
        days = []
        if not estimates:
            estimates = grid.keys()
        for estimate in estimates:
            for story in grid[estimate]:
                if not story.started or not story.resolved:
                    continue
                days.append(story.cycle_time)
        return days

    def rank_depth(self, story):
        if story.status in [5, 6]:
            return None
        stories = self.release.stories_by_status()
        if not str(story.status) in stories.keys():
            return None
        stories = stories[str(story.status)]
        depth = 1
        for s in sort(stories, ['rank']):
            if s.key == story.key:
                return depth
            depth = depth + 1
        return None

    def stories_in_front(self, story):
        stories_by_status = self.release.stories_by_status()
        if not str(story.status) in stories_by_status.keys():
            return None
        result = []
        if not story.status in KANBAN:
            return None
        columns = KANBAN[KANBAN.index(story.status):-2]
        found = False
        for column in columns:
            if not str(column) in stories_by_status.keys():
                continue
            stories = stories_by_status[str(column)]
            for s in sort(stories_by_status[str(column)], ['rank']):
                if s.key == story.key:
                    found = True
                    break
                result.append(s)
        if not found:
            return None
        return result

    def time_remaining(self, stories):
        cycle_times = self.average_cycle_times_by_type()
        results = 0
        for story in stories:
            results += cycle_times[story.type]
            if story.status and story.cycle_time and \
                humanize(story.status) in self.release.WIP.keys():
                results = results - story.cycle_time
        return results

    def atp(self, story):
        cycle_times = self.average_cycle_times_by_type()
        days = cycle_times[story.type]
        if story.cycle_time:
            days = days - story.cycle_time
        in_front = self.stories_in_front(story)
        if in_front is None:
            return self.add_weekends(days)
        days += self.time_remaining(in_front)
        return self.add_weekends(days)

    def add_weekends(self, days):
        now = datetime.datetime.now()
        then = now + datetime.timedelta(days)
        days += len(list(rrule(DAILY, dtstart=now, until=then,
            byweekday=(SA, SU))))
        then = now + datetime.timedelta(days)
        if then.weekday() >= 5:
            days += 7 - then.weekday()
        return days

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
        min_atp = self.atp(story)
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
        outside = average + (std * 3)
        if story.cycle_time:
            return round(outside - story.cycle_time, 1)
        return round(outside, 1)

    def process_cycle_efficiency(self, component=None, types=['7'], points=[]):
        cycle_times = self.cycle_times_in_status(component, types, points)
        value = nonvalue = 0
        for status in cycle_times:
            if status in (10004, 10002):
                value += cycle_times[status]
            elif status in (1, STATUS_READY, 6): # ignore 'open' and 'ready'
                continue
            else:
                nonvalue += cycle_times[status]
        if not value + nonvalue:
            return 0
        return round(value/float((value + nonvalue)), 2) * 100


class Release(Folder):
    implements(IRelease)

    WIP = {'Start': 10002,
           'PeerR': 10004,
           'NeedA': 10014,
           'Test ': 10005,
           'QeApp': 10127,
           'PoApp': 10128,}

    def __init__(self, version=None):
        super(Release, self).__init__()
        self.key = version
        self.version = version

    def __key__(self):
        return (self.version)

    def __eq__(x, y):
        if not isinstance(x, Release) or not isinstance(y, Release):
            return False
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

    def unique_labels(self):
        labels = []
        for story in self.stories():
            if not hasattr(story, 'labels'):
                continue
            labels.extend(story.labels)
        return [l for l in sets.Set(labels)]

    def label_report(self):
        labels = []
        for story in self.stories():
            if not hasattr(story, 'labels'):
                continue
            labels.extend(story.labels)
        return [l for l in sets.Set(labels)]

    def stories_for_labels(self, labels):
        labels = sets.Set(labels)
        stories = []
        for story in self.stories():
            if not hasattr(story, 'labels'):
                continue
            if labels.intersection(sets.Set(story.labels)):
                stories.append(story)
        return stories

    def cycle_time_for_label(self, label):
        stories = self.stories_for_labels([label])
        start = None
        end = None
        for story in stories:
            if not start or (story.started and story.started < start):
                start = story.started
            if not end or (story.resolved and story.resolved > end):
                end = story.resolved
        if not start:
            return None
        if not end:
            end = datetime.datetime.now()
        days = end - start
        return days.days

    def developers(self):
        developers = {}
        for story in self.stories():
            if story.developer not in developers:
                developers[story.developer] = [story]
            else:
                developers[story.developer].append(story)
        return developers

    def aggregate_developer_cycle_time(self):
        developers = self.developers()
        total = 0
        for developer in developers:
            total += sum([
                s.cycle_time for s in developers[developer] if s.cycle_time])
        return total

    def average_developer_cycle_time(self):
        developers = self.developers()
        total = self.aggregate_developer_cycle_time()
        devs = len(developers.keys())
        if not devs:
            return 0
        return round(total/float(devs), 1)

    def stdev_developer_cycle_time(self):
        developers = self.developers()
        cycle_times = []
        for developer in developers:
            cycle_times.append(sum([s.cycle_time for s in developers[developer]
                if s.cycle_time]))
        return round(numpy.std(cycle_times), 1)

    def stories(self, type=[]):
        if type:
            return [story for story in self.values() if story.type in type]
        return self.values()

    def started_stories(self, type=['7']):
        return [story for story in self.stories(type) if story.started]

    def resolved_stories(self, type=['7']):
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
            status = story.status
            if not story.status:
                status = -1
            status = str(status)
            if result.has_key(status):
                result[status].append(story)
            else:
                result[status] = [story]
        return result

    def total_stories(self):
        return len(self.stories())

    def total_points(self):
        return sum([story.points for story in self.stories(type=['7'])
            if story.points])

    def points_completed(self):
        points = 0
        for story in self.stories():
            if story.status == 6 and story.points:
                points += story.points
        return points

    def skew_cycle_time(self):
        ''' Skewness of the bell curve
            Positive skew is to the left, negative skew to the right
            e.g. for cycle times positive skew is towards shorter cycles
        '''
        points = []
        for story in self.stories():
            if story.cycle_time:
                points.append(story.cycle_time)
        return round(stats.skew(points), 1)

    def average_story_size(self):
        points = []
        for story in self.stories():
            if story.points:
                points.append(story.points)
        return numpy.average(numpy.array(points))

    def std_story_size(self):
        ''' Uses ddof=0 because that is right and excel is wrong
        '''
        points = []
        for story in self.stories():
            if story.points:
                points.append(story.points)
        return numpy.std(numpy.array(points), ddof=0)

    def sort_by_size(self):
        return sorted(self.only_groomed_stories(),
            key=lambda x: x.points, reverse=True)

    def stories_in_process(self):
        stories = 0
        for story in self.stories(type=['7']):
            if story.status in self.WIP.values():
                stories += 1
        return stories

    def wip(self):
        stories = 0
        for story in self.stories():
            if story.status in self.WIP.values():
                stories += 1
        return stories

    def wip_by_status(self):
        tallies = {}
        for story in self.stories():
            if story.status in self.WIP.values():
                if str(story.status) not in tallies:
                    tallies[str(story.status)] = {'wip': 1}
                else:
                    tallies[str(story.status)]['wip'] += 1
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
        short_wip['start'] = wip['10024']
        short_wip['middle'] = wip['10002'] + wip['10004'] + wip['10004'] \
            + wip['10014'] + wip['10005'] + wip['10127'] + wip['10128']
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
        stories.sort(key=lambda x:x.cycle_time if x.type !='7' else x.lead_time)
        index = int(round(percentile * len(stories) + 0.5))
        if index > 1:
            return [s for s in stories[index-1:]]
        return []


class Project(Folder):
    implements(IProject)

    def __init__(self, key=None, name=None, owner=None, process=None,
            query=None):
        super(Project, self).__init__()
        self.name = name
        self.key = key
        self.owner = owner
        self.process = process
        self.query = query

class Projects(object):
    def __init__(self):
        self.data = []

    def add(self, project):
        self.data.append(project)

    def all_projects(self):
        return self.data


class Issues(Release):
    implements(IIssues)
    def __init__(self):
        super(Issues, self).__init__('issues')
        self.name = 'Issues'
        self.process = ''
        self.last_updated = datetime.datetime(1901, 1, 1)
