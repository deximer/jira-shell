from behave import *
import model
import jira
import dao

@then('I see these developers listed')
def step(context):
    output = context.stdout_capture.getvalue()
    for row in context.table:
        line = '%s: %s' % (row['dev'], row['stories'])
        assert line in output
