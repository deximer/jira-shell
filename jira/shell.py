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
        if not item:
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

