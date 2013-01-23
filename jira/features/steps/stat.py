from behave import *
import model
import jira

@then('I see critical data for the specific issue')
def step(context):
    output = context.stdout_capture.getvalue()
    for row in context.table:
        assert 'Status: %s' % row['status'] in output
        assert row['title'] in output
        assert row['key'] in output
        assert row['type'] in output
