NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
ITEMS = './/*/item'
STORY_POINTS = './/*[@id="customfield_10792"]/*/customfieldvalue'
STATUS = 'status'
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

class Release(object):
    WIP = {'Open': 1, 'In Progress': 3, 'Reopened': 4, 'Ready': 10089,
           'QA Active': 10092, 'Ready for QA': 10104}

    def __init__(self):
        self.data = []

    def add(self, story):
        self.data.append(story)

    def total_points(self):
        return sum([story.points for story in self.data if story.points])

    def points_completed(self):
        points = 0
        for story in self.data:
            if story.status == 6 and story.points:
                points += story.points
        return points

    def wip(self):
        points = 0
        for story in self.data:
            if story.status in self.WIP.values() and story.points:
                points += story.points
        return points

    def wip_by_status(self):
        tallies = {}
        for value in self.WIP.values():
            tallies[str(value)] = 0
        for story in self.data:
            if story.status in self.WIP.values() and story.points:
                tallies[str(story.status)] += story.points
        return tallies

    def wip_by_component(self):
        tallies = {}
        for story in self.data:
            if story.status in self.WIP.values() and story.points:
                for component in story.components:
                    if not tallies.has_key(component):
                        tallies[component] = story.points
                    else:
                        tallies[component] += story.points
        return tallies

