Feature: Refresh local cache from Jira database
         In order that I can use the latest Jira data
         As a user
         I want to be able to refresh my local cache

    Scenario: A user refresh all Jira data
        Given: I am at the root
        When: I enter "refresh -a"
        Then: All Jira data is loaded into the cache

    Scenario: A user refreshes a single issue
        Given: I am at the root
        And: There is an issue with id "ISS-1"
        When: I enter "refresh ISS-1"
        Then: The issue "ISS-1" is refreshed

    Scenario: A user refreshes a single project
        Given: I am at the root
        And: There is a project with id "97"
        When: I enter "refresh 97"
        Then: All issues for project "97" are refreshed

    Scenario: A user refreshes a single project with all changes in past day
        Given: I am at the root
        And: There is a project with id "97"
        When: I enter "refresh -t 1d"
        Then: All issues updated in last day for project 97 are refreshed

    Scenario: A user refreshes a project in the cwd
        Given: There is a project with id "97"
        And: I am at the root of project with id "97"
        When: I enter "refresh"
        Then: All issues for project "97" are refreshed

    Scenario: A user refreshes an issue in the cwd
        Given: There is a project with id "97"
        Given: There is an issue with id "ISS-1"
        And: I am at the root of issue with id "ISS-1"
        When: I enter "refresh"
        Then: The issue with id "ISS-1" is updated

