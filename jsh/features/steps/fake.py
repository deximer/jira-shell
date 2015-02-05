from behave import *
import dao

@then('The fake project key is in the database')
def step(context):
    assert 'fP1' in dao.Jira.cache.data
        
@then('The fake release is in the fake project')
def step(context):
    assert 'f1.0' in dao.Jira.cache.data['fP1']

@then('The fake release has 19 fake issues')
def step(context):
    assert len(dao.Jira.cache.data['fP1']['f1.0'].keys()) == 19
