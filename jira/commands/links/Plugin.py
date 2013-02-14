import curses
import argparse
from ..base import BaseCommand
from model import Release, KANBAN

class Command(BaseCommand):
    help = "Render an issue's link graphs"
    usage = 'links <issue_id> [-t <issue_type [...]>]'
    options_help = '''    -t : Show only issues of the specified type
    -b : use bug traversal alogrithm (only descend development links)
    '''
    examples = '''    links 12345
    links NG-12345 -t 1 78
    links NG-12345 -b
    '''

    def run(self, jira, args):
        if not args:
            print 'Error: you must specify an issue key'
            return
        parser = argparse.ArgumentParser()
        parser.add_argument('key')
        parser.add_argument('-t', nargs='*', required=False)
        parser.add_argument('-b', action='store_true', required=False)
        self.args = parser.parse_args(args)
        story = jira.cache.get(self.args.key)
        if not story:
            print 'Error: story key %s not found' % self.args.key
            return
        story = story[0]
        if self.args.b:
            self.args.t = ['1']
        print 'Release:'.ljust(15), 'Typ:', 'Stat:', ' Relationship Tree:'
        print ''.join(story.fix_versions).ljust(15)[:15], \
            str(story.type).ljust(4), str(story.status).ljust(6), story.key
        if story.links.outward:
            for link in story.links.outward:
                if not self.args.t or link.type in self.args.t:
                    print ''.join(link.fix_versions).ljust(15)[:15], \
                        str(link.type).ljust(4), \
                        str(link.status).ljust(6),'\-> %s' % link.key
                if self.args.b and link.type not in self.args.t:
                    continue
                self.recurse_links(link, [link.key])

    def recurse_links(self, issue, indent):
        for link in issue.links.outward:
            if link.key in indent:
                continue
            if not self.args.t or link.type in self.args.t:
                print ''.join(link.fix_versions).ljust(15)[:15], \
                    str(link.type).ljust(4), str(link.status).ljust(6), \
                    ''.ljust(len(indent[:-1])), '\-> %s' % link.key
            if self.args.b and link.type not in self.args.t:
                continue
            if link.links.outward:
                indent.append(link.key)
                self.recurse_links(link, indent)
                del indent[0]
