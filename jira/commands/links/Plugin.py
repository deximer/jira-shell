import curses
import argparse
from ..base import BaseCommand
from model import Release, KANBAN

class Command(BaseCommand):
    help = 'Render issue link graphs'
    usage = 'links <issue_id>'
    examples = '''    links 12345
    links NG-12345
    '''

    def run(self, jira, args):
        if not args:
            print 'Error: you must specify an issue key'
            return
        parser = argparse.ArgumentParser()
        parser.add_argument('key')
        args = parser.parse_args(args)
        story = jira.cache.get(args.key)
        if not story:
            print 'Error: story key %s not found' % args.key
            return
        story = story[0]
        print story.key, story.type, story.status
        if story.links.all:
            for link in story.links.all:
                print '\-> %s' % link.key, link.type, link.status
                self.recurse_links(link, [link.key])

    def recurse_links(self, issue, indent):
        for link in issue.links.all:
            if link.key in indent:
                continue
            print ''.ljust(len(indent)), '\-> %s' % link.key, link.type, \
                link.status
            if link.links.all:
                indent.append(link.key)
                self.recurse_links(link, indent)
                del indent[0]
