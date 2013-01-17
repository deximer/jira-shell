import urllib
import json
import datetime
import time
from xml.etree import ElementTree as ET
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
            release.add(self.get_story(key))
        return release

    def get_release_keys(self, refresh=False):
        page = self.request_page('sr/jira.issueviews:searchrequest-xml/24619/' \
            'SearchRequest-24619.xml?tempMax=10000', refresh)
        tree = ET.fromstring(page)
        keys = []
        for key in tree.findall('.//*/item/key'):
            keys.append(key.text)
        return keys

    def get_story(self, key):
        story = Story(key)
        data = self.call_rest(key, expand=['changelog'])
        story.data = data
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
