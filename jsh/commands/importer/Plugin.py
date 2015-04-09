import getopt
import argparse
from ..base import BaseCommand
try:
    from ...model import Release
except:
    from model import Release

class Command(BaseCommand):
    help = 'Import data from files. Files must by in an "import" subdirectory.'
    usage = 'import <file>'
    examples = '''    import NG-13332.json'''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('file', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        try:
            context = jira.cache.get_by_path(jira.cache.cwd)
        except KeyError:
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        if not isinstance(context, Release):
            print 'Error: Must navigate to a release. (hint: help cd)'
            return
        try:
            json = open('import/%s' % args.file)
        except IOError:
            print 'Error: file %s not found in import directory' % args.file
            return
        obj = jira.json_to_object(json.read())
        # If not file, error out
        story = jira.make_story(obj['key'], obj)
        # If not 'key', fail out
        context.add_story(story)
        print 'Imported issue %s' % story.key

