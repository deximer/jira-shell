from behave import *
import model
import jira
import dao

@then('I see these teams listed')
def step(context):
    output = context.stdout_capture.getvalue()
    for row in context.table:
        line = '%s: %s' % (row['team'], row['stories'])
        assert line in output
