from behave import *

@then('I see these teams listed')
def step(context):
    output = context.stdout_capture.getvalue()
    for row in context.table:
        line = '%s' % row['team']
        line = line.ljust(25) + ' :  %s' % row['stories']
        assert line in output
