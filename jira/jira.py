#!/usr/bin/env python2.7
import optparse
import urllib
from xml.etree import ElementTree as ET
from BeautifulSoup import BeautifulSoup as BS
from model import Release, Story, Projects, Project
from dao import Jira
import commands

commands = {'top': commands.top.Plugin.Command(),
            'ls': commands.ls.Plugin.Command(),
            'chart': commands.chart.Plugin.Command(),
            'export': commands.export.Plugin.Command(),
            'report': commands.report.Plugin.Command(),
            'stat': commands.stat.Plugin.Command(),
            'teams': commands.teams.Plugin.Command(),
            'refresh': commands.refresh.Plugin.Command(),
           }

NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
NG_NEXT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?tempMax=10000'
ISSUE='http://mindtap.user:m1ndtap@jira.cengage.com/si/jira.issueviews:issue-xml/%s/%s.xml'
ITEMS = './/*/item'
PROJECTS = 'http://mindtap.user:m1ndtap@jira.cengage.com/secure/BrowseProjects.jspa#all'

cwd = ['/']

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

def process_raw_key(args):
    if args[:2] != 'NG':
        args = 'NG-' + args.strip()
    return args.strip()

def connect_to_jira():
    return Jira('jira.cengage.com', 'mindtap.user:m1ndtap')

def shell():
    return raw_input('%s > ' % '/'.join(cwd))

def dispatch(command):
    try:
        command, args = command.split(' ')
    except ValueError:
        args = ''
    table = {'report': commands['report'].run,
             'teams': commands['teams'].run,
             'ls': commands['ls'].run,
             'stat': commands['stat'].run,
             'top': commands['top'].run,
             'export': commands['export'].run,
             'refresh': commands['refresh'].run,
             'chart': commands['chart'].run,
            }
    if command in table.keys():
        table[command](connect_to_jira(), args)
    else:
        print '%s: command not found' % command

def main():
    p = optparse.OptionParser()
    p.add_option('--command', '-c', action='store_true', dest='command')
    p.add_option('--shell', '-s', action='store_true', dest='shell')
    options, arguments = p.parse_args()
    #request_projects()
    if options.command:
        dispatch(' '.join(arguments))
    elif options.shell:
        command = ''
        while command != 'quit':
            command = shell()
            if command:
                dispatch(command)

if __name__ == '__main__':
    main()
