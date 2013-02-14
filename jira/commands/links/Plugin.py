import curses
import argparse
from ..base import BaseCommand
from model import Release, KANBAN

class Command(BaseCommand):
    help = "Render an issue's link graphs"
    usage = 'links <issue_id> [-t <issue_type [...]>]'
    options_help = '''    -t : Show only issues of the specified type
    '''
    examples = '''    links 12345
    links NG-12345 -t 1 78
    '''

    def run(self, jira, args):
        if not args:
            print 'Error: you must specify an issue key'
            return
        parser = argparse.ArgumentParser()
        parser.add_argument('key')
        parser.add_argument('-t', nargs='*', required=False)
        args = parser.parse_args(args)
        story = jira.cache.get(args.key)
        if not story:
            print 'Error: story key %s not found' % args.key
            return
        story = story[0]
        print story.key, story.type, story.status
        if story.links.all:
            for link in story.links.all:
                if args.t and link.type not in args.t:
                    continue
                print '\-> %s' % link.key, link.type, link.status
                self.recurse_links(link, [link.key], args.t)

    def recurse_links(self, issue, indent, types=[]):
        for link in issue.links.all:
            if link.key in indent or (types and link.type not in types):
                continue
            print ''.ljust(len(indent)), '\-> %s' % link.key, link.type, \
                link.status
            if link.links.all:
                indent.append(link.key)
                self.recurse_links(link, indent)
                del indent[0]
