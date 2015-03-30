''' atp: Available To Promise

   ATP seeks to answer the question "given what we know about the specific characterisitcs of a ticket, what can we say about it's likelyhood of completion"? This is an inversion of the question "given what we know generally about all other tickets, what can we say about the likelyhood of comletion for this ticket specifically"? ATP will reclassify the specific issue in order to to maintain a future prediction. It will not simply return a negative number when cycle times are exceeded. It asks "given that the ticket is outside the predictions, what is it now most like and what does that mean concerning predictability"?
'''

import getopt
import argparse
import sets
import datetime
from dateutil.rrule import DAILY, SA, SU, rrule
from ..base import BaseCommand
from model import humanize

class Command(BaseCommand):
    help = 'Provide estimate delivery dates.'
    usage = 'atp issue_id [-l label]'
    options_help = ''''''
    examples = '''    atp POOL-1
    atp -l non247
    '''

    def run(self, jira, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('-l', nargs='*', required=False)
        parser.add_argument('select', nargs='?')
        try:
            args = parser.parse_args(args)
        except:
            return
        container = jira.cache.get_by_path(jira.cache.cwd)
        kanban = container.kanban()
        stories = []
        if args.l:
            stories = container.stories_for_labels(args.l)
        else:
            stories.append(container.get(args.select))
        report = []
        for story in stories:
            if story.status in [5, 6]:
                continue
            days = int(round(kanban.average_atp(story), 0))
            now = datetime.datetime.now()
            atp = now + datetime.timedelta(days)
            report.append('%s %s %d days' % (str(atp)[:10], story.key, days))

        report.sort()
        for item in report:
            print item

