import urllib
import json
import datetime
import getpass
import time
import copy
import transaction
import jira
from xml.etree import ElementTree as ET
from ZODB.DB import DB
from ZODB.FileStorage import FileStorage
from repoze.folder import Folder
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

from repoze.catalog.catalog import ConnectionManager, Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.path import CatalogPathIndex
from repoze.catalog.document import DocumentMap

from model import Issues, Project, Release, Story

ZIPCAR_API = 'https://%s:%s@jira.zipcar.com/rest/api/2/issue/%s'

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
        if 'issues' not in self.connection.root()['jira']:
            self.connection.root()['jira']['issues'] = Issues()
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

    def process_raw_key(self, key):
        if key.isdigit():
            key = 'NG-%s' % key
        return key.strip()

    def get(self, key, context=None):
        #key = self.process_raw_key(key)
        results = self.catalog.search(key=key)
        stories = []
        for sid in results[1]:
            path = self.document_map.address_for_docid(sid)
            if path:
                path[0] = '/'
                stories.append(self.get_by_path(path))
        return stories

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
    user = None
    password = None

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

    def get_release(self, version=None):
        if not version:
            version = self.cwd[-1]
        for key in self.cache.data.keys():
            if key == version:
                return self.cache.data[key]
        return None

    def pull_projects(self):
        if not self.user or not self.password:
            self.password = getpass.getpass('Password: ')
            self.user = raw_input('User: ')
            self.server = jira.client.JIRA({'server': 'https://jira.zipcar.com'}
                , basic_auth=(self.user, self.password))
            self.agile = jira.client.GreenHopper(
                  {'server': 'https://jira.zipcar.com'}
                , basic_auth=(self.user, self.password))
        for prj in self.agile.boards():
            pid = getattr(prj, 'id')
            transaction.begin()
            project = Project(str(pid), prj.name)
            project.query = prj.filter.query
            if prj.sprintSupportEnabled:
                project.process = 'Scrum'
            else:
                project.process = 'Kanban'
            self.cache.data[str(pid)] = project
            transaction.commit()
            transaction.begin()
            docid = self.cache.document_map.add(['jira', str(pid)])
            self.cache.catalog.index_doc(docid, project)
            transaction.commit()

    def pull_releases(self):
        for project in self.cache.data.values():
            if project.process == 'Kanban':
                self.pull_kanban(project)
            if project.process == 'Scrum':
                self.pull_scrum(project)

    def pull_scrum(self, project):
        for spr in self.agile.sprints(int(project.key)):
            sid = getattr(spr, 'id')
            sprint = Release()
            sprint.key = str(sid)
            sprint.version = str(sid)
            sprint.name = spr.name
            transaction.begin()
            self.cache.data[project.key][str(sid)] = sprint
            transaction.commit()
            transaction.begin()
            docid = self.cache.document_map.add(['jira', project.key, str(sid)])
            self.cache.catalog.index_doc(docid, sprint)
            transaction.commit()
            self.pull_scrum_stories(project, sprint)

    def pull_scrum_stories(self, project, sprint):
        issues = []
        try:
            issues.extend(self.agile.incompleted_issues(project.key,sprint.key))
        except:
            pass
        try:
            issues.extend(self.agile.completed_issues(project.key, sprint.key))
        except:
            pass
        for issue in issues:
            if self.cache.data['issues'].has_key(issue.key):
                story = self.cache.data['issues'][issue.key]
            else:
                print issue.key, 'not found!'
                continue
            #story = self.get_story(issue.key)
            transaction.begin()
            sprint.add_story(story)
            transaction.commit()
            transaction.begin()
            docid = self.cache.document_map.add(
                ['jira', project.key, sprint.key, story.key])
            self.cache.catalog.index_doc(docid, story)
            transaction.commit()

    def pull_kanban(self, project):
        kanban = Release()
        kanban.key = 'BRD-%s' % project.key
        kanban.version = kanban.key
        kanban.name = 'Kanban Board'
        transaction.begin()
        self.cache.data[project.key][kanban.key] = kanban
        transaction.commit()
        transaction.begin()
        docid = self.cache.document_map.add(
            ['jira', str(project.key), kanban.key])
        self.cache.catalog.index_doc(docid, kanban)
        transaction.commit()
        self.pull_kanban_stories(project, kanban)

    def pull_issues(self):
        store = self.cache.data['issues']
        
        issues = self.server.search_issues('', maxResults=0)
        print 'Importing', len(issues), 'stories...'
        for issue in issues:
            story = self.get_story(issue.key)
            if store.has_key(issue.key):
                continue
            print 'Importing:', story.key
            transaction.begin()
            store[story.key] = story
            transaction.commit()
            transaction.begin()
            docid = self.cache.document_map.add(
                ['jira', 'issues', story.key])
            self.cache.catalog.index_doc(docid, story)
            transaction.commit()
            for link in issue.fields.issuelinks:
                transaction.begin()
                if hasattr(link, 'outwardIssue') and link.outwardIssue:
                    type = link.type.name
                    key = link.outwardIssue.key
                    if not type in story['links']['out'].keys():
                        story['links']['out'][type] = Folder()
                        story['links']['out'][type].key = type
                        transaction.commit()
                        s = self.get_story(key)
                        if not s:
                            continue
                        story['links']['out'][type][key] = s
                    else:
                        if not key in story['links']['out'][type].keys():
                            s = self.get_story(key)
                            if not s:
                                continue
                            story['links']['out'][type][key] = s
                elif hasattr(link, 'inwardIssue') and link.inwardIssue:
                    type = link.type.name
                    key = link.inwardIssue.key
                    if not type in story['links']['in'].keys():
                        story['links']['in'][type] = Folder()
                        story['links']['in'][type].key = type
                        transaction.commit()
                        s = self.get_story(key)
                        if not s:
                            continue
                        story['links']['in'][type][key] = s
                    else:
                        if not key in story['links']['in'][type].keys():
                            s = self.get_story(key)
                            if not s:
                                continue
                            story['links']['in'][type][key] = s
                transaction.commit()

    def pull_kanban_stories(self, project, kanban):
        issues = self.server.search_issues(project.query, maxResults=0)
        for issue in issues:
            #story = self.get_story(issue.key)
            if self.cache.data['issues'].has_key(issue.key):
                story = self.cache.data['issues'][issue.key]
            else:
                print issue.key, 'not found!'
                continue
            transaction.begin()
            kanban.add_story(story)
            transaction.commit()
            transaction.begin()
            docid = self.cache.document_map.add(
                ['jira', project.key, kanban.key, story.key])
            self.cache.catalog.index_doc(docid, story)
            transaction.commit()
            continue
            for link in issue.fields.issuelinks:
                transaction.begin()
                if hasattr(link, 'outwardIssue') and link.outwardIssue:
                    type = link.type.name
                    key = link.outwardIssue.key
                    if not type in story['links']['out'].keys():
                        story['links']['out'][type] = Folder()
                        story['links']['out'][type].key = type
                        transaction.commit()
                        s = self.get_story(key)
                        if not s:
                            continue
                        story['links']['out'][type][key] = s
                    else:
                        if not key in story['links']['out'][type].keys():
                            s = self.get_story(key)
                            if not s:
                                continue
                            story['links']['out'][type][key] = s
                elif hasattr(link, 'inwardIssue') and link.inwardIssue:
                    type = link.type.name
                    key = link.inwardIssue.key
                    if not type in story['links']['in'].keys():
                        story['links']['in'][type] = Folder()
                        story['links']['in'][type].key = type
                        transaction.commit()
                        s = self.get_story(key)
                        if not s:
                            continue
                        story['links']['in'][type][key] = s
                    else:
                        if not key in story['links']['in'][type].keys():
                            s = self.get_story(key)
                            if not s:
                                continue
                            story['links']['in'][type][key] = s
                transaction.commit()

    def refresh_cache(self, releases=['2.7'], links=True):
        if not self.user or not self.password:
            self.password = getpass.getpass('Password: ')
            self.user = raw_input('User: ')
            self.server = jira.client.JIRA({'server': 'https://jira.zipcar.com'}
                , basic_auth=(self.user, self.password))
            self.agile = jira.client.GreenHopper(
                  {'server': 'https://jira.zipcar.com'}
                , basic_auth=(self.user, self.password))
        self.pull_issues()
        #self.pull_projects()
        #self.pull_releases()
        for prj in self.agile.boards():
            pid = getattr(prj, 'id')
            if pid not in [97, 148, 149]:
                continue
            transaction.begin()
            project = Project(str(pid), prj.name)
            project.query = prj.filter.query
            if prj.sprintSupportEnabled:
                project.process = 'Scrum'
            else:
                project.process = 'Kanban'
            self.cache.data[str(pid)] = project
            transaction.commit()
            transaction.begin()
            docid = self.cache.document_map.add(['jira', str(pid)])
            self.cache.catalog.index_doc(docid, project)
            transaction.commit()
            if project.process == 'Kanban':
                release = Release()
                release.key = 'BRD-%d' % pid
                release.version = release.key
                release.name = 'Kanban Board'
                transaction.begin()
                self.cache.data[project.key][release.key] = release
                transaction.commit()
                transaction.begin()
                docid = self.cache.document_map.add(
                    ['jira', str(pid), release.key])
                self.cache.catalog.index_doc(docid, release)
                transaction.commit()
                issues = self.server.search_issues(
                    project.query, maxResults=1000)
                for iss in issues:
                    if self.cache.data['issues'].has_key(iss.key):
                        story = self.cache.data['issues'][iss.key]
                    else:
                        print iss.key, 'not found!'
                        continue
                    #story = self.get_story(iss.key)
                    transaction.begin()
                    release.add_story(story)
                    transaction.commit()
                    transaction.begin()
                    docid = self.cache.document_map.add(
                        ['jira', str(pid), release.key, story.key])
                    self.cache.catalog.index_doc(docid, story)
                    transaction.commit()
            for spr in self.agile.sprints(int(project.key)):
                sid = getattr(spr, 'id')
                release = Release()
                release.key = str(sid)
                release.version = str(sid)
                release.name = spr.name
                transaction.begin()
                self.cache.data[project.key][str(sid)] = release
                transaction.commit()
                transaction.begin()
                docid = self.cache.document_map.add(['jira', str(pid),str(sid)])
                self.cache.catalog.index_doc(docid, release)
                transaction.commit()
                issues = []
                try:
                    issues.extend(self.agile.incompleted_issues(pid, sid))
                except:
                    pass
                try:
                    issues.extend(self.agile.completed_issues(pid, sid))
                except:
                    pass
                for iss in issues:
                    story = self.get_story(iss.key)
                    transaction.begin()
                    release.add_story(story)
                    transaction.commit()
                    transaction.begin()
                    docid = self.cache.document_map.add(
                        ['jira', str(pid), str(sid), story.key])
                    self.cache.catalog.index_doc(docid, story)
                    transaction.commit()
        return

        keys = self.get_release_keys(releases)
        #release_keys = []
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

    def get_story(self, key, refresh=False, links=False):
        story = self.cache.get(key)
        if story and not refresh:
            return story[0]
        try:
            data = self.call_rest(key, expand=['changelog'])
        except ValueError:
            print 'Error: Jira down for maintenance'
            return None
        return Story(self.server.issue(key, expand='changelog'))

    def make_story(self, key, data, links=True):
        return Story(self.server.issue(key, expand='changelog'))

        if not links:
            return story
        transaction.begin()
        for link in data['fields']['issuelinks']:
            if link.has_key('outwardIssue'):
                type = link['type']['name']
                key = link['outwardIssue']['key']
                if not type in story['links']['out'].keys():
                    story['links']['out'][type] = Folder()
                    story['links']['out'][type].key = type
                    transaction.commit()
                    s = self.get_story(key)
                    if not s:
                        continue
                    story['links']['out'][type][key] = s
                else:
                    if not key in story['links']['out'][type].keys():
                        s = self.get_story(key)
                        if not s:
                            continue
                        story['links']['out'][type][key] = s
            elif link.has_key('inwardIssue'):
                type = link['type']['name']
                key = link['inwardIssue']['key']
                if not type in story['links']['in'].keys():
                    story['links']['in'][type] = Folder()
                    story['links']['in'][type].key = type
                    transaction.commit()
                    s = self.get_story(key)
                    if not s:
                        continue
                    story['links']['in'][type][key] = s
                else:
                    if not key in story['links']['in'][type].keys():
                        s = self.get_story(key)
                        if not s:
                            continue
                        story['links']['in'][type][key] = s
        transaction.commit()
        return story

    def commit(self):
        transaction.commit()

    def call_rest(self, key, expand=[]):
        if not hasattr(self, 'user'):
            print
            self.user = raw_input('User: ')
            self.password = getpass.getpass('Password: ')
        URL = ZIPCAR_API % (self.user, self.password, key)
        if expand:
            URL += '?expand='
            for item in expand:
                URL += item + ','
            URL = URL[:-1]
        return self.json_to_object(urllib.urlopen(URL).read())

    def call_api(self, method):
        if not hasattr(self, 'user'):
            print
            self.user = raw_input('User: ')
            self.password = getpass.getpass('Password: ')
        URL = 'http://%s:%s@jira.zipcar.com/rest/api/2/%s' \
            % (self.user, self.password, method)
        return self.json_to_object(urllib.urlopen(URL).read())

    def json_to_object(self, json_data):
        return json.loads(json_data)

    def get_changelog(self, key):
        return self.call_rest(key, ['changelog'])
