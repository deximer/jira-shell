

class Story(object):
    def __init__(self, item):
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

