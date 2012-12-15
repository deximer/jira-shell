import numpy
import time
import datetime

NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
ITEMS = './/*/item'
STORY_POINTS = './/*[@id="customfield_10792"]/*/customfieldvalue'
IN_PROGRESS = './/*[@id="customfield_13434"]/*/customfieldvalue'
STATUS = 'status'
BUG_TYPE = '1'
STORY_TYPE = '72'
TITLE = 'title'
TYPE = 'type'
DESCRIPTION = 'description'
KEY = 'key'
RESOLVED = 'resolved'
COMPONENTS = 'component'
STATUS_OPEN = 1
STATUS_IN_PROGRESS = 3
STATUS_REOPENED = 4
STATUS_VERIFIED = 10036
STATUS_CLOSED = 6
STATUS_READY = 10089
STATUS_COMPLETED = 10090
STATUS_QA_ACTIVE = 10092
STATUS_QA_READY = 10104
KANBAN = [STATUS_OPEN, STATUS_READY, STATUS_IN_PROGRESS, STATUS_REOPENED,
    STATUS_QA_READY, STATUS_QA_ACTIVE, STATUS_COMPLETED, STATUS_VERIFIED,
    STATUS_CLOSED]

class Root(object):
    pass

class Story(object):
    def __init__(self, item=None):
        if item is None:
            return
        points = item.find(STORY_POINTS)
        if points is not None:
            self.points = float(points.text)
        else:
            self.points = None
        status = item.find(STATUS)
        if status is not None:
            self.status = int(status.attrib['id'])
        else:
            self.status = None
        self.components = []
        components = item.findall(COMPONENTS)
        for component in components:
            self.components.append(component.text)
        key = item.find(KEY)
        if key is not None:
            self.key = key.text
        else:
            self.key = None
        title = item.find(TITLE)
        if title is not None:
            self.title = title.text
        else:
            self.title = None
        issue_type = item.find(TYPE)
        if issue_type is not None:
            self.type = issue_type.attrib['id']
        else:
            self.type = None
        description = item.find(DESCRIPTION)
        if description is not None:
            self.description = description.text
        else:
            self.description = None
        resolved = item.find(RESOLVED)
        if resolved is not None:
            self.resolved = datetime.datetime.fromtimestamp(time.mktime(
                time.strptime(resolved.text[:-6], '%a, %d %b %Y %H:%M:%S')))
        else:
            self.resolved = None
        started = item.find(IN_PROGRESS)
        if started is not None:
            self.started = datetime.datetime.fromtimestamp(time.mktime(
                time.strptime(started.text[:-6], '%a, %d %b %Y %H:%M:%S')))
        else:
            self.started = None
        if self.started and self.resolved:
            self.cycle_time = self.resolved - self.started
        elif self.started and not self.resolved:
            self.cycle_time = datetime.datetime.today() - self.started
        else:
            self.cycle_time = None



class Kanban(object):
    def __init__(self):
        self.stories = []
        self.release = None
        self.grid = {}

    def add(self, story):
        self.stories.append(story)
        status = str(story.status)
        for component in story.components:
            if not self.grid.has_key(component):
                self.grid[component] = {status: {
                    'wip': story.points or 0.0,
                    'stories': [story],
                    'largest': story.points}}
            elif not self.grid[component].has_key(status):
                self.grid[component][status] = {
                    'wip': story.points or 0.0,
                    'stories': [story],
                    'largest': story.points}
            else:
                if story.points is not None:
                    self.grid[component][status]['wip'] += story.points
                self.grid[component][status]['stories'].append(story)
                if self.grid[component][status]['largest'] < story.points:
                    self.grid[component][status]['largest'] = story.points

    def add_release(self, release):
        self.release = release
        for story in release.data:
            self.add(story)

    def average_cycle_time(self, component=None):
        if not self.release.stories():
            return None
        deltas = []
        for story in self.release.stories():
            if component and component not in story.components:
                continue
            if not story.started or not story.resolved:
                continue
            started = story.started
            resolved = story.resolved
            deltas.append(resolved - started)
        result = sum(deltas, datetime.timedelta())
        return result.days/len(self.release.stories())

class Release(object):
    WIP = {'Open': 1, 'In Progress': 3, 'Reopened': 4, 'Ready': 10089,
           'QA Active': 10092, 'Ready for QA': 10104}

    def __init__(self):
        self.data = []

    def add(self, story):
        self.data.append(story)

    def get(self, key):
        for story in self.data:
            if story.key == key:
                return story
        return None

    def stories(self):
        return [story for story in self.data if story.type == STORY_TYPE]

    def bugs(self):
        return [story for story in self.data if story.type == BUG_TYPE]

    def only_groomed_stories(self):
        return [story for story in self.stories() if story.points]

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
        points = []
        for story in self.stories():
            if story.points:
                points.append(story.points)
        return numpy.std(numpy.array(points))

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
                for component in story.components:
                    if not tallies.has_key(component):
                        tallies[component] = {'wip': story.points, 'stories': 1,
                            'largest': story.points}
                    else:
                        tallies[component]['wip'] += story.points
                        tallies[component]['stories'] += 1
                        if tallies[component]['largest'] < story.points:
                            tallies[component]['largest'] = story.points
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

class Project(object):
    def __init__(self, name=None, key=None, owner=None):
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
