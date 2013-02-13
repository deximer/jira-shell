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
        print story.key
        if story.links.data:
            for link in story.links.data:
                print '|-> %s' % link.key
                self.recurse_links(link, [link.key])

    def recurse_links(self, issue, indent):
        for link in issue.links.data:
            if link.key in indent:
                continue
            print ''.ljust(len(indent)), '|-> %s' % link.key
            if link.links.data:
                indent.append(link.key)
                self.recurse_links(link, indent)
                del indent[0]
