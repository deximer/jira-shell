#!/usr/bin/env python2.7
import optparse
import sys
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
from BeautifulSoup import BeautifulSoup as BS
from model import Release, Story, Projects, Project
from dao import Jira, MT_USER, MT_PASS
import commands

cmds = {'top': commands.top.Plugin.Command(),
        'ls': commands.ls.Plugin.Command(),
        'chart': commands.chart.Plugin.Command(),
        'export': commands.export.Plugin.Command(),
        'report': commands.report.Plugin.Command(),
        'stat': commands.stat.Plugin.Command(),
        'teams': commands.teams.Plugin.Command(),
        'legend': commands.legend.Plugin.Command(),
        'developers': commands.developers.Plugin.Command(),
        'refresh': commands.refresh.Plugin.Command(),
       }

NG_CURRENT_RELEASE = 'http://%s:%s@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000' % (MT_USER, MT_PASS)
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

cache = DB(FileStorage('cache.fs')).open()

def connect_to_jira():
    return Jira('jira.cengage.com', 'mindtap.user:m1ndtap', cache)

def shell():
    return raw_input('%s > ' % '/'.join(cwd))

def dispatch(command):
    table = {'report': cmds['report'].run,
             'teams': cmds['teams'].run,
             'developers': cmds['developers'].run,
             'ls': cmds['ls'].run,
             'stat': cmds['stat'].run,
             'top': cmds['top'].run,
             'legend': cmds['legend'].run,
             'export': cmds['export'].run,
             'refresh': cmds['refresh'].run,
             'chart': cmds['chart'].run,
             'help': help,
            }
    args = command.split()[1:]
    command = command.split()[0]
    if command in table.keys():
        table[command](connect_to_jira(), args)
    else:
        print '%s: command not found' % command

def help(jira, command):
    if command:
        command = command[0]
    if not command:
        print 'Print help text for a specified command'
        print 'Usage: help [commands || [command_name]]'
        print 'Example:'
        print '    help commands'
        print '    help ls'
        return
    if command == 'commands':
        print 'Available commands:'
        for command in cmds.keys():
            print command
        return
    print cmds[command].help
    print
    print 'Usage: %s' % cmds[command].usage
    if cmds[command].options_help:
        print 'Options:'
        print cmds[command].options_help
    if cmds[command].examples:
        print 'Examples:'
        print cmds[command].examples

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
        print 'Jira Shell 0.1'
        print 'Type "help" to get started. Type "quit" to exit.'
        while command != 'quit':
            command = shell()
            if command:
                dispatch(command)

if __name__ == '__main__':
    main()
