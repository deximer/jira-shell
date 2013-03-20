import urllib
import json
import datetime
import time
import copy
import transaction
from xml.etree import ElementTree as ET
from ZODB.DB import DB
from ZODB.FileStorage import FileStorage
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

from repoze.catalog.catalog import ConnectionManager, Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.path import CatalogPathIndex
from repoze.catalog.document import DocumentMap

from BeautifulSoup import BeautifulSoup as BS

from model import Projects, Project, Release, Story, History, Links

MT_USER = 'mindtap.user'
MT_PASS = 'm1ndtap'

JIRA_API = 'http://%s:%s@jira.cengage.com/rest/api/2/issue/%s'

def get_key(obj, default=None):
    return getattr(obj, 'key', default)


class LocalDB(object):
    cache_file = 'db/cache.fs'
    fs = None
    db = None
    connection = None
    root = None
    data = None

    def __init__(self):
        self.init_db()
        self.catalog = self.connection.root()['catalog']
        self.document_map = self.connection.root()['document_map']
        self.data = self.connection.root()['jira']
        self.cwd = ['/']

    def init_db(self):
        self.fs = FileStorage(self.cache_file)
        self.db = DB(self.fs)
        self.connection = self.db.open()
        transaction.begin()
        if 'jira' not in self.connection.root():
            self.connection.root()['jira'] = PersistentMapping()
        self.root = self.connection.root()['jira']
        if not 'catalog' in self.connection.root():
            catalog = Catalog()
            self.connection.root()['catalog'] = catalog
            catalog['key'] = CatalogFieldIndex(get_key)
            self.connection.root()['document_map'] = DocumentMap()
        transaction.commit()

    def close_db(self):
        transaction.abort()
        self.catalog = None
        self.document_map = None
        self.data = None
        self.connection.close()
        self.db.close()
        self.fs.close()

    def keys(self, obj=None, results=[]):
        if obj is None:
            obj = self.data
        for key in obj:
            if not key in results:
                results.append(key)
            if hasattr(obj[key], 'has_key'):
                self.keys(obj[key], results)
        return results

    def get(self, key, context=None):
        key = self.process_raw_key(key)
        results = self.catalog.search(key=key)
        stories = []
        for id in results[1].keys():
            path = self.document_map.address_for_docid(id)
            if path:
                path[0] = '/'
                stories.append(self.get_by_path(path))
        return stories

    def process_raw_key(self, key):
        if key.isdigit():
            key = 'NG-%s' % key
        return key.strip()

    def cwd_contents(self):
        if self.cwd[-1] == '/':
            return tuple(sorted([key for key in self.data]))
        contents = []
        obj = self.get_by_path(self.cwd)
        for key in obj:
            contents.append(key)
        return tuple(contents)

    def get_by_path(self, path):
        path = copy.copy(path)
        if isinstance(path, type('')):
            path = path.split('/')
            if not path[0]:
                path[0] = '/'
        if path[0] == '/':
            obj = self.data
            del path[0]
        else:
            obj = self.get_by_path(self.cwd)
        for directory in path:
            obj = obj[directory]
        return obj


class Jira(object):
    cache = LocalDB()

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
        for key in self.cache.data.keys():
            if key == version:
                return self.cache.data[key]
        return None

    def refresh_cache(self, releases=['2.7'], links=True):
        keys = self.get_release_keys(releases)
        release_keys = []
        #for release in releases:
        #    obj = self.cache.get_by_path('/NG/%s' % release)
        #    release_keys.extend(obj.keys())
        #orphans = [k for k in release_keys if k not in keys]
        #keys.extend(orphans)
        factor = 120.0
        if links:
            factor = 12.0
        print 'Refreshing %d keys. About %d minutes' % (len(keys),
            round(len(keys)/factor, 1))
        for key in keys:
            self.get_story(key, True, links=links)

    def get_release_keys(self, releases):
        if len(releases) > 1:
            notice = 'Retrieving release keys for %s' % ', '.join(releases[:-1])
            notice += ' and %s' % releases[-1]
        else:
            notice = 'Retrieving release keys for %s' % releases[0]
        print notice
        issues = []
        for release in releases:
            issues.extend(self.call_api('search?' \
                'jql=project%20=%20ng%20AND%20fixVersion="' + release + '"' \
                '&startAt=0&maxResults=10000&fields=key')['issues'])
        return [i['key'] for i in issues]

    def get_story(self, key, refresh=False, links=True):
        story = self.cache.get(key)
        if story and not refresh:
            return story[0]
        try:
            data = self.call_rest(key, expand=['changelog'])
        except ValueError:
            print 'Error: Jira down for maintenance'
            return None
        return self.make_story(key, data, links=links)

    def make_story(self, key, data, links=True):
        if not data['fields']['fixVersions']:
            return None
        transaction.begin()
        story = Story(key)
        story.id = int(data['id'])
        story.history = History(data['changelog'])
        story.url = data['self']
        story.title = data['fields']['summary']
        story.fix_versions = PersistentList()
        for version in data['fields']['fixVersions']:
            story.fix_versions.append(version['name'])
        story.fix_version = data['fields']['fixVersions']
        story.created = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(data['fields']['created'][:23],
            '%Y-%m-%dT%H:%M:%S.%f')))
        story.type = data['fields']['issuetype']['id']
        story.assignee = data['fields']['assignee']
        story.developer = data['fields']['customfield_13435']
        story.scrum_team = None
        if data['fields'].has_key('customfield_11261'):
            if data['fields']['customfield_11261']:
                story.scrum_team = data['fields']['customfield_11261'][
                    'value'].strip()
        else:
            story.scrum_team = None
        story.points = None
        if data['fields'].has_key('customfield_10792'):
            story.points = data['fields']['customfield_10792']
        if story.points:
            story.points = int(story.points)
        story.status = int(data['fields']['status']['id'])
        story.project = data['fields']['project']['key']
        if not story.project in self.cache.data:
            self.cache.data[story.project] = Project(story.project,
                data['fields']['project']['name'])
        project = self.cache.data[story.project]
        for version in story.fix_versions:
            if version in project.keys():
                if not project[version].has_key(story.key):
                    project[version][story.key] = story
            else:
                release = Release()
                release.version = version
                release[story.key] = story
                project[version] = release
        transaction.commit()
        transaction.begin()
        docid = self.cache.document_map.add(
            ['jira', story.project, story.fix_versions[0], story.key])
        self.cache.catalog.index_doc(docid, story)
        transaction.commit()
        if not links:
            return story
        transaction.begin()
        for link in data['fields']['issuelinks']:
            if link.has_key('outwardIssue'):
                type = link['type']['name']
                key = link['outwardIssue']['key']
                if not type in story.links['out'].keys():
                    story.links['out'][type] = PersistentMapping()
                    transaction.commit()
                    s = self.get_story(key)
                    if not s:
                        continue
                    story.links['out'][type][key] = s
                else:
                    if not key in story.links['out'][type].keys():
                        s = self.get_story(key)
                        if not s:
                            continue
                        story.links['out'][type][key] = s
            elif link.has_key('inwardIssue'):
                type = link['type']['name']
                key = link['inwardIssue']['key']
                if not type in story.links['in'].keys():
                    story.links['in'][type] = PersistentMapping()
                    transaction.commit()
                    s = self.get_story(key)
                    if not s:
                        continue
                    story.links['in'][type][key] = s
                else:
                    if not key in story.links['in'][type].keys():
                        s = self.get_story(key)
                        if not s:
                            continue
                        story.links['in'][type][key] = s
        transaction.commit()
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
        return self.json_to_object(urllib.urlopen(URL).read())

    def pull_kyts(self):
        jql = 'search?jql=project=KYTS+AND+status=Open+ORDER+BY+priority+DESC&expand=changelog'
        issues = self.call_api(jql)
        print 'Importing %d KYTS issues...' % len(issues['issues'])
        for issue in issues['issues']:
            print 'Make: %s' % issue['key']
            self.make_story(issue['key'], issue, True)

    def call_api(self, method):
        URL = 'http://%s:%s@jira.cengage.com/rest/api/2/%s' \
            % (MT_USER, MT_PASS, method)
        return self.json_to_object(urllib.urlopen(URL).read())

    def json_to_object(self, json_data):
        return json.loads(json_data)

    def get_changelog(self, key):
        return self.call_rest(key, ['changelog'])
