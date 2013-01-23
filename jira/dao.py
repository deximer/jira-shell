import urllib
import json
import datetime
import time
from xml.etree import ElementTree as ET
import transaction
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from BeautifulSoup import BeautifulSoup as BS
from model import Projects, Project, Release, Story

MT_USER = 'mindtap.user'
MT_PASS = 'm1ndtap'

JIRA_API = 'http://%s:%s@jira.cengage.com/rest/api/2/issue/%s'

class Jira(object):
    def __init__(self, server=None, auth=None):
        self.server = server
        self.auth = auth
        self.cwd = [['/'], ['/']]
        self.cache = DB(FileStorage('cache.fs')).open().root()

    def format_request(self, path):
        return 'http://%s@%s/%s' % (self.auth, self.server, path)

    def request_page(self, path, refresh=False):
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

    def get_release(self, refresh=False):
        page = self.request_page('sr/jira.issueviews:searchrequest-xml/24619/' \
            'SearchRequest-24619.xml?tempMax=10000', refresh)
        tree = ET.fromstring(page)
        release = Release()
        for key in self.get_release_keys():
            release.add(self.get_story(key, refresh))
        return release

    def get_release_keys(self, refresh=False):
        page = self.request_page('sr/jira.issueviews:searchrequest-xml/24619/' \
            'SearchRequest-24619.xml?tempMax=10000', refresh)
        tree = ET.fromstring(page)
        keys = []
        for key in tree.findall('.//*/item/key'):
            keys.append(key.text)
        return keys

    def get_story(self, key, refresh=False):
        if not refresh and key in self.cache.keys():
            return self.cache[key]
        story = Story(key)
        data = self.call_rest(key, expand=['changelog'])
        story.title = data['fields']['summary']
        story.created = datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(data['fields']['created'][:23],
            '%Y-%m-%dT%H:%M:%S.%f')))
        story.started = None
        story.resolved = None
        for history in data['changelog']['histories']:
            for item in history['items']:
                if item['to'] == '3':
                    story.started = datetime.datetime.fromtimestamp(time.mktime(
                        time.strptime(history['created'][:23],
                        '%Y-%m-%dT%H:%M:%S.%f')))
                else:
                    story.started = None
                    break
        for history in data['changelog']['histories']:
            for item in history['items']:
                if item['to'] == '6':
                    if history['created']:
                        story.resolved =datetime.datetime.fromtimestamp(
                            time.mktime( time.strptime(history['created'][:23],
                            '%Y-%m-%dT%H:%M:%S.%f')))
                    else:
                        story.resolved = None
                    break
        story.type = data['fields']['issuetype']['id']
        story.assignee = data['fields']['assignee']
        if data['fields']['customfield_11261']:
            story.scrum_team = data['fields']['customfield_11261'][
                'value'].strip()
        else:
            story.scrum_team = None
        story.points = data['fields']['customfield_10792']
        if story.points:
            story.points = int(story.points)
        story.status = data['fields']['status']['id']
        story.history = data['changelog']['histories']
        story.data = data
        self.cache[key] = story
        transaction.commit()
        return story

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
