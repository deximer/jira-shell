#!/usr/bin/env python2.7
import optparse
import urllib
from xml.etree import ElementTree as ET
from BeautifulSoup import BeautifulSoup as BS
from model import Release, Story, Projects, Project
from dao import Jira
import commands

commands = {'top': commands.top.Plugin.Command(),
           }

NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
ISSUE='http://mindtap.user:m1ndtap@jira.cengage.com/si/jira.issueviews:issue-xml/%s/%s.xml'
ITEMS = './/*/item'
PROJECTS = 'http://mindtap.user:m1ndtap@jira.cengage.com/secure/BrowseProjects.jspa#all'

cwd = ['/']

def request_issue(key):
    return ET.fromstring(urllib.urlopen(ISSUE % (key, key)).read())

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

def print_release_report(args):
    release = get_release()
    print 'Total Stories    :', release.total_stories()
    print 'Total Bugs       :', len(release.bugs())
    print 'Average Size     :', round(release.average_story_size(), 2)
    print 'Std Dev          :', round(release.std_story_size(), 2)
    print 'Smallest Story   :', release.sort_by_size()[-1].points
    print 'Largest Story    :', release.sort_by_size()[0].points
    print 'Points in scope  :', round(release.total_points(), 2)
    print 'Points completed :', round(release.points_completed(), 2)
    print 'Stories IP       :', release.stories_in_process()
    print 'Total WIP        :', round(release.wip(), 2)
    print
    print 'WIP by Status:'
    wip = release.wip_by_status()
    for key in wip:
        print key.ljust(16), ':', str(wip[key]['wip']).ljust(6), \
            wip[key]['stories']
    print
    print 'WIP by Swim Lane:'
    wip = release.wip_by_component()
    for key in wip:
        print key.ljust(16), ':',  str(wip[key]['wip']).ljust(6), \
            str(wip[key]['stories']).ljust(3), wip[key]['largest']

def ls(args):
    release = get_release()
    for story in release.data:
        print story.key, str(story.points).ljust(5), str(story.status).ljust(5), story.title[:50]

def process_raw_key(args):
    if args[:2] != 'NG':
        args = 'NG-' + args.strip()
    return args.strip()

def stat(args):
    key = process_raw_key(args)
    story = request_issue(key)
    story = Story(story.find(ITEMS))
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
    commands['top'].run(jira, args)

def shell():
    return raw_input('%s > ' % '/'.join(cwd))

def dispatch(command):
    try:
        command, args = command.split(' ')
    except ValueError:
        args = ''
    table = {'report': print_release_report,
             'ls': ls,
             'stat': stat,
             'top': top,
            }
    if command in table.keys():
        table[command](args)
    else:
        print '%s: command not found' % command

jira = Jira('jira.cengage.com', 'mindtap.user:m1ndtap')

def main():
    p = optparse.OptionParser()
    p.add_option('--report', '-r', action='store_true', dest='report')
    p.add_option('--shell', '-s', action='store_true', dest='shell')
    options, arguments = p.parse_args()
    #request_projects()
    if options.report:
        print_release_report()
    if options.shell:
        command = ''
        while command != 'quit':
            command = shell()
            if command:
                dispatch(command)

if __name__ == '__main__':
    main()
