import urllib
import json
import datetime
import time
import transaction
from ZODB.DB import DB
from ZODB.FileStorage import FileStorage
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from xml.etree import ElementTree as ET
from BeautifulSoup import BeautifulSoup as BS
from model import Projects, Project, Release, Story

MT_USER = 'mindtap.user'
MT_PASS = 'm1ndtap'

JIRA_API = 'http://%s:%s@jira.cengage.com/rest/api/2/issue/%s'

connection = DB(FileStorage('db/cache.fs')).open()

class LocalDB(object):
    def __init__(self, connection):
        self.data = connection
        self.cwd = ['/']

    def keys(self, obj=None, results=[]):
        if not obj:
            obj = self.data.root()
        for key in obj:
            if not key in results:
                results.append(key)
            if hasattr(obj[key], 'has_key'):
                self.keys(obj[key], results)
        return results

    def get(self, key, obj=None):
        if not obj:
            obj = self.data.root()
        result = None
        for k in obj:
            if k == key:
                return obj[k]
            if hasattr(obj[k], 'has_key'):
                result = self.get(key, obj[k])
        return result

    def cwd_contents(self):
        if self.cwd[-1] == '/':
            return tuple(sorted([key for key in self.data.root()]))
        contents = []
        obj = self.get_by_path(self.cwd)
        for key in obj:
            contents.append(key)
        return tuple(contents)

    def get_by_path(self, path):
        import copy
        path = copy.copy(path)
        if isinstance(path, type('')):
            path = path.split('/')
            if not path[0]:
                path[0] = '/'
        if path[0] == '/':
            obj = self.data.root()
            del path[0]
        else:
            obj = self.get_by_path(self.cwd)
        for dir in path:
            obj = obj[dir]
        return obj


class Jira(object):
    cache = LocalDB(connection)

    def __init__(self, server=None, auth=None):
        self.server = server
        self.auth = auth
        self.cwd = ['/']

    def cwd_contents(self):
        if self.cwd[-1] == '/':
            contents = []
            for key in self.cache.root().keys():
                contents.append(self.cache.root()[key])
            return {'releases': contents}

    def format_request(self, path):
        return 'http://%s@%s/%s' % (self.auth, self.server, path)

    def request_page(self, path, refresh=True):
        try:
            if not refresh:
                cache = open('cache.xml', 'r')
                return cache.read()
        except:
            pass
        page = urllib.urlopen(self.format_request(path)).read()
        cache = open('cache.xml', 'w')
        cache.write(page)
        cache.close()
        return page

    def get_projects(self):
        page = self.request_page('secure/BrowseProjects.jspa#all')
        soup = BS(page)
        names = soup.find('tbody', {'class' : 'projects-list'}).findAll(
            'td')[::4]
        codes = soup.find('tbody', {'class' : 'projects-list'}).findAll(
            'td')[1::4]
        owner = soup.find('tbody', {'class' : 'projects-list'}).findAll(
            'td')[2::4]
        projects = Projects()
        for count in range(0, len(names)):
            projects.add(Project(names[count].text, codes[count].text,
                owner[count].text))
        return projects

    def all_projects(self):
        return self.get_projects()

    def get_release(self, version=None):
        if not version:
            version = self.cwd[-1]
        for key in self.cache.data.root().keys():
            if key == version:
                return self.cache.data.root()[key]
        return None

    def refresh_cache(self):
        page = self.request_page('sr/jira.issueviews:searchrequest-xml/24619/' \
            'SearchRequest-24619.xml?tempMax=10000')
        tree = ET.fromstring(page)
        for key in self.get_release_keys():
            self.get_story(key, True)

    def get_release_keys(self, refresh=False):
        page = self.request_page('sr/jira.issueviews:searchrequest-xml/24619/' \
            'SearchRequest-24619.xml?tempMax=10000', refresh)
        tree = ET.fromstring(page)
        keys = []
        for key in tree.findall('.//*/item/key'):
            keys.append(key.text)
        return keys

    def get_story(self, key, refresh=False):
        story = self.cache.get(key)
        if not refresh and story:
            return story
        story = Story(key)
        data = self.call_rest(key, expand=['changelog'])
        story.title = data['fields']['summary']
        story.fix_versions = PersistentList()
        for version in data['fields']['fixVersions']:
            story.fix_versions.append(version['name'])
        story.fix_version = data['fields']['fixVersions']
        story.created = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(data['fields']['created'][:23],
            '%Y-%m-%dT%H:%M:%S.%f')))
        story.started = None
        for history in data['changelog']['histories']:
            for item in history['items']:
                if item['field'] == 'status' and item['to'] == '3':
                    story.started = datetime.datetime.fromtimestamp(time.mktime(
                        time.strptime(history['created'][:23],
                        '%Y-%m-%dT%H:%M:%S.%f')))
                    break
        story.resolved = None
        for history in data['changelog']['histories']:
            for item in history['items']:
                if item['to'] == '6':
                    if history['created']:
                        story.resolved =datetime.datetime.fromtimestamp(
                            time.mktime( time.strptime(history['created'][:23],
                            '%Y-%m-%dT%H:%M:%S.%f')))
                    break
        story.type = data['fields']['issuetype']['id']
        story.assignee = data['fields']['assignee']
        story.developer = data['fields']['customfield_13435']
        if data['fields']['customfield_11261']:
            story.scrum_team = data['fields']['customfield_11261'][
                'value'].strip()
        else:
            story.scrum_team = None
        story.points = data['fields']['customfield_10792']
        if story.points:
            story.points = int(story.points)
        story.status = int(data['fields']['status']['id'])
        story.history = data['changelog']['histories']
        story.data = data
        for version in story.fix_versions:
            if version in self.cache.data.root():
                self.cache.data.root()[version][story.key] = story
            else:
                release = Release()
                release.version = version
                release[story.key] = story
                self.cache.data.root()[version] = release
        self.commit()
        return story

    def commit(self):
        transaction.commit()

    def call_rest(self, key, expand=[]):
        URL = JIRA_API % (MT_USER, MT_PASS, key)
        if expand:
            URL += '?expand='
            for item in expand:
                URL += item + ','
            URL = URL[:-1]
        return json.loads(urllib.urlopen(URL).read())

    def get_changelog(self, key):
        return self.call_rest(key, ['changelog'])
