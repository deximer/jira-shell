#!/usr/bin/env python2.7
import optparse
import urllib
from xml.etree import ElementTree as ET
from model import Release, Story

NG_CURRENT_RELEASE = 'http://mindtap.user:m1ndtap@jira.cengage.com/sr/' \
    'jira.issueviews:searchrequest-xml/24619/SearchRequest-24619.xml?' \
    'tempMax=10000'
ITEMS = './/*/item'

def request_current_release():
    return ET.fromstring(urllib.urlopen(NG_CURRENT_RELEASE).read())

def get_release():
    tree = request_current_release()
    release = Release()
    for item in tree.findall(ITEMS):
        release.add(Story(item))
    return release

def print_release_report():
    release = get_release()
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

def main():
    p = optparse.OptionParser()
    p.add_option('--report', '-r', action='store_true', dest='report')
    options, arguments = p.parse_args()
    if options.report:
        print_release_report()

if __name__ == '__main__':
    main()
