from behave import *
import model
import jira
import dao

@then('I see these developers listed')
def step(context):
    output = context.stdout_capture.getvalue()
    for row in context.table:
        line = '%s' % row['dev']
        line = line.ljust(25) + ' :  %s' % row['stories']
        assert line in output
