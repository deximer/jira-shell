#!/usr/bin/env python2.7
import optparse
import urllib
from xml.etree import ElementTree as ET
from BeautifulSoup import BeautifulSoup as BS
from model import Release, Story, Projects, Project
from dao import Jira
import commands

commands = {'top': commands.top.Plugin.Command(),
            'export': commands.export.Plugin.Command(),
            'report': commands.report.Plugin.Command(),
           }

NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
NG_NEXT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?tempMax=10000'
ISSUE='http://mindtap.user:m1ndtap@jira.cengage.com/si/jira.issueviews:issue-xml/%s/%s.xml'
ITEMS = './/*/item'
PROJECTS = 'http://mindtap.user:m1ndtap@jira.cengage.com/secure/BrowseProjects.jspa#all'

cwd = ['/']

def request_issue(key):
    tree = ET.fromstring(urllib.urlopen(ISSUE % (key, key)).read())
    return Story(tree.find(ITEMS))

def request_current_release():
    return ET.fromstring(urllib.urlopen(NG_CURRENT_RELEASE).read())

def get_release():
    tree = request_current_release()
    release = Release()
    for item in tree.findall(ITEMS):
        release.add(Story(item))
    return release

def request_projects():
    page = urllib.urlopen(PROJECTS).read()
    soup = BS(page)
    names = soup.find('tbody', {'class' : 'projects-list'}).findAll('td')[::4]
    codes = soup.find('tbody', {'class' : 'projects-list'}).findAll('td')[1::4]
    owner = soup.find('tbody', {'class' : 'projects-list'}).findAll('td')[2::4]
    projects = Projects()
    for count in range(0, len(names)):
        projects.add(Project(names[count].text, codes[count].text,
            owner[count].text))
    return projects

def ls(args):
    release = get_release()
    for story in release.data:
        team = story.scrum_team
        if not team:
            team = 'Everything Else'
        print team[:18].ljust(18), str(story.points).ljust(5), str(story.status).ljust(5), str(release.kanban().contingency_outside(story.key)).ljust(5), story.title[:43]

def process_raw_key(args):
    if args[:2] != 'NG':
        args = 'NG-' + args.strip()
    return args.strip()

def stat(args):
    key = process_raw_key(args)
    story = request_issue(key)
    print 'Key: ', story.key
    print 'Title: ', story.title
    print 'Points: ', story.points
    print 'Status: ', story.status
    print 'Components:'
    for component in story.components:
        print '    ', component

def top(args):
    #def mock_request_page(self, url):
    #    return open('tests/data/rss.xml').read()
    #jira.request_page = mock_request_page
    commands['top'].run(connect_to_jira(), args)

def export(args):
    #def mock_request_page(self, url):
    #    return open('tests/data/rss.xml').read()
    #jira.request_page = mock_request_page
    commands['export'].run(connect_to_jira(), args)

def report(args):
    #def mock_request_page(self, url):
    #    return open('tests/data/rss.xml').read()
    #jira.request_page = mock_request_page
    commands['report'].run(connect_to_jira(), args)

def connect_to_jira():
    return Jira('jira.cengage.com', 'mindtap.user:m1ndtap')

def shell():
    return raw_input('%s > ' % '/'.join(cwd))

def dispatch(command):
    try:
        command, args = command.split(' ')
    except ValueError:
        args = ''
    table = {'report': report,
             'ls': ls,
             'stat': stat,
             'top': top,
             'export': export,
            }
    if command in table.keys():
        table[command](args)
    else:
        print '%s: command not found' % command

def main():
    p = optparse.OptionParser()
    p.add_option('--report', '-r', action='store_true', dest='report')
    p.add_option('--shell', '-s', action='store_true', dest='shell')
    options, arguments = p.parse_args()
    #request_projects()
    if options.report:
        report('')
    if options.shell:
        command = ''
        while command != 'quit':
            command = shell()
            if command:
                dispatch(command)

if __name__ == '__main__':
    main()
