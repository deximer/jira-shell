#!/usr/bin/env python2.7
import optparse
import urllib
from xml.etree import ElementTree as ET
from model import Release, Story

NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
ISSUE='http://mindtap.user:m1ndtap@jira.cengage.com/si/jira.issueviews:issue-xml/%s/%s.xml'
ITEMS = './/*/item'

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

def print_release_report(args):
    release = get_release()
    print 'Total Stories    :', len(release.data)
    print 'Points in scope  :', release.total_points()
    print 'Points completed :', release.points_completed()
    print 'WIP              :', release.wip()
    print
    wip = release.wip_by_status()
    for key in wip:
        print key.ljust(16), ':', wip[key]
    print
    wip = release.wip_by_component()
    for key in wip:
        print key.ljust(16), ':',  wip[key]

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
    print
    print 'Description:'
    print story.description
    

def shell():
    return raw_input('/2.5 > ')

def dispatch(command):
    try:
        command, args = command.split(' ')
    except ValueError:
        args = ''
    table = {'report': print_release_report,
             'ls': ls,
             'stat': stat,
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
