import numpy

NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
ITEMS = './/*/item'
STORY_POINTS = './/*[@id="customfield_10792"]/*/customfieldvalue'
STATUS = 'status'
TITLE = 'title'
DESCRIPTION = 'description'
KEY = 'key'
COMPONENTS = 'component'
STATUS_OPEN = 1
STATUS_IN_PROGRESS = 3
STATUS_REOPENED = 4
STATUS_CLOSED = 6
STATUS_READY = 10089
STATUS_COMPLETED = 10090
STATUS_QA_ACTIVE = 10092
STATUS_QA_READY = 10104
KANBAN = [1, 10089, 3, 4, 10104, 10092, 6]

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
        description = item.find(DESCRIPTION)
        if description is not None:
            self.description = description.text
        else:
            self.description = None

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

    def only_groomed_stories(self):
        return [story for story in self.data if story.points]

    def total_stories(self):
        return len(self.data)

    def total_points(self):
        return sum([story.points for story in self.data if story.points])

    def points_completed(self):
        points = 0
        for story in self.data:
            if story.status == 6 and story.points:
                points += story.points
        return points

    def average_story_size(self):
        points = []
        for story in self.data:
            if story.points:
                points.append(story.points)
        return numpy.average(numpy.array(points))

    def std_story_size(self):
        points = []
        for story in self.data:
            if story.points:
                points.append(story.points)
        return numpy.std(numpy.array(points))

    def sort_by_size(self):
        return sorted(self.only_groomed_stories(),
            key=lambda x: x.points, reverse=True)

    def stories_in_process(self):
        stories = 0
        for story in self.data:
            if story.status in self.WIP.values() and story.points:
                stories += 1
        return stories

    def wip(self):
        points = 0
        for story in self.data:
            if story.status in self.WIP.values() and story.points:
                points += story.points
        return points

    def wip_by_status(self):
        tallies = {}
        for story in self.data:
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
        for story in self.data:
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
        kanban = {}
        for story in self.data:
            status = str(story.status)
            for component in story.components:
                if not kanban.has_key(component):
                    kanban[component] = {status: {
                        'wip': story.points or 0.0,
                        'stories': 1,
                        'largest': story.points}}
                elif not kanban[component].has_key(status):
                    kanban[component][status] = {
                        'wip': story.points or 0.0,
                        'stories': 1,
                        'largest': story.points}
                else:
                    if story.points is not None:
                        kanban[component][status]['wip'] += story.points
                    kanban[component][status]['stories'] += 1
                    if kanban[component][status]['largest'] < story.points:
                        kanban[component][status]['largest'] = story.points
        return kanban

    def graph_kanban(self, swimlane=None):
        kanban = self.kanban()
        points = []
        wip = {'1': 0.0, '10104': 0.0, '3': 0.0, '10092': 0.0, '4': 0.0,
            '10036': 0.0, '10090': 0.0, '10089': 0.0}
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
            elif value <= 0.15:
                points.append('.')
            elif value > 0.15 and value <= 0.5:
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
