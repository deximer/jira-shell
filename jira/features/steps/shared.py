from behave import *
import model
import jira
import dao

@given('I have the following issues in the release')
def step(context):
    context.release = model.Release()
    for row in context.table:
        context.release.add(make_story(row))

@when('I enter the command "{command}"')
def step(context, command):
    def mock_get_release(self=None, refresh=False):
        return context.release
    jira.get_release = mock_get_release
    dao.Jira.get_release = mock_get_release
    def mock_request_issue(self=None, refresh=False):
        return context.release.get('NG-' + command.split(' ')[1])
    jira.request_issue = mock_request_issue
    jira.dispatch(command)

@then('I see these issues listed')
def step(context):
    output = context.stdout_capture.getvalue()
    for row in context.table:
        assert row['title'] in output

@then('I see "{value}" in the output')
def step(context, value):
    assert value in context.stdout_capture.getvalue()

def make_story(row):
    story = model.Story()
    story.key = row['key']
    if 'team' in row.headings:
        story.scrum_team = row['team']
    else:
        story.scrum_team = 'Foo'
    if 'points' in row.headings:
        story.points = float(row['points'])
    else:
        story.points = 1.0
    story.started = None
    story.resolved = None
    story.components = []
    story.title = row['title']
    if 'status' in row.headings:
        story.status = int(row['status'])
    else:
        story.status = 3
    story.type = '72'
    return story
