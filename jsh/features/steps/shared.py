from behave import *
import model
import jsh
import dao
from datetime import datetime
from persistent.mapping import PersistentMapping

@given('The user is at the command line')
def step(context):
    context.release = model.Release()
    if 'table' not in context or not context.table:
        return
    for row in context.table:
        context.release.add_story(make_story(row))

@given('I have the following release')
def step(context):
    for row in context.table:
        dao.Jira.cache.data[row['key']] = model.Release(row['key'])

@given('I have the following issues in the release')
def step(context):
    context.release = dao.Jira.cache.data['1.0']
    def mock_get(self, key):
        if key.isdigit():
            key = 'NG-%s' % key
        key = key.strip()
        if context.release.has_key(key):
            return [context.release[key]]
        return None
    dao.LocalDB.get = mock_get
    for row in context.table:
        context.release.add_story(make_story(row))

@given('Issue "{issue_key}" has this transition history')
def step(context, issue_key):
    context.release = dao.Jira.cache.data['1.0']
    issue = context.release[issue_key]
    issue.history.data = []
    for row in context.table:
        add_history(issue, row['date'], row['from'], row['to'])

@given('Issue "{issue_key}" has the following links')
def step(context, issue_key):
    issue = context.release[issue_key]
    for row in context.table:
        add_link(issue, context.release[row['key']])

@given('I have the json file "{some_file}" in the import directory')
def step(context, some_file):
    pass

@given('The file "{some_file}" is not in the import directory')
def step(context, some_file):
    pass

@given('I am in the directory "{command}"')
def step(context, command):
    if command == '/':
        dao.Jira.cache.cwd = ['/']
    else:
        dao.Jira.cache.cwd = command.split('/')
        dao.Jira.cache.cwd[0] = '/'

@when('I enter the command "{command}"')
def step(context, command):
    def mock_get_release(self=None, refresh=False):
        return context.release
    jsh.get_release = mock_get_release
    dao.Jira.get_release = mock_get_release
    def mock_request_issue(self=None, refresh=False):
        return context.release.get('NG-' + command.split(' ')[1])
    jsh.request_issue = mock_request_issue
    jsh.dispatch(command)
    print '/%s > ' % '/'.join(dao.Jira.cache.cwd[1:])

@then('The REPL displays "{command}"')
def step(context, command):
    output = context.stdout_capture.getvalue()
    print output
    assert command in output

@then('I see these issues listed')
def step(context):
    output = context.stdout_capture.getvalue()
    for row in context.table:
        assert row['title'] in output

@then('I see "{value}" in the output')
def step(context, value):
    assert value in context.stdout_capture.getvalue()

@then('I do not see "{value}" in the output')
def step(context, value):
    assert value not in context.stdout_capture.getvalue()

def make_story(row):
    story = model.Story()
    story.key = row['key']
    if 'labels' in row.headings:
        story.labels = row['labels'].split(',')
    if 'components' in row.headings:
        story.components = row['components'].split(',')
    if 'priority' in row.headings:
        story.priority = row['priority']
    else:
        story.priority = 'Minor'
    story.title = row['title']
    story.root_cause = ''
    story.root_cause_details = ''
    story.components = []
    if 'rank' in row.headings:
        story.rank = row['rank']
    else:
        story.rank = ''
    if 'team' in row.headings:
        story.scrum_team = row['team']
    else:
        story.scrum_team = 'unspecified'
    if 'dev' in row.headings:
        story.developer = row['dev']
    else:
        story.developer = 'unspecified'
    if 'points' in row.headings:
        story.points = float(row['points'])
    else:
        story.points = 1.0
    if 'created' in row.headings and row['created']:
        date = row['created'].split('/')
        story.created = datetime(2000+int(date[0]), int(date[1]), int(date[2]))
    else:
        story.created = None
    story.resolution = 'Fixed'
    story.history = model.History()
    if 'started' in row.headings and row['started']:
        date = row['started'].split('/')
        start_date = datetime(2000+int(date[0]), int(date[1]), int(date[2]))
        story.history.data.append((start_date, 1, 10002, None, 'Sarah Conner'))
    if 'resolved' in row.headings and row['resolved']:
        date = row['resolved'].split('/')
        resolved_date = datetime(2000+int(date[0]), int(date[1]), int(date[2]))
        story.history.data.append((resolved_date, 10002, 6, 'Jane Doe'))
    if 'status' in row.headings:
        story.status = int(row['status'])
    else:
        story.status = 10002
    if 'type' in row.headings:
        story.type = row['type']
    else:
        story.type = '7'
    if 'fix' in row.headings:
        story.fix_versions = row['fix'].split(',')
    else:
        story.fix_versions = []
    return story

def add_history(issue, date, start, end):
    date = date.split('/')
    date = datetime(2000+int(date[0]), int(date[1]), int(date[2]), 12, 30, 0)
    days = None
    issue.history.data.append((date, int(start), int(end), 'Jane Doe'))

def add_link(parent, child):
    if 'Related' not in parent['links']['out']:
        parent['links']['out']['Related'] = PersistentMapping()
    parent['links']['out']['Related'][child.key] = child
