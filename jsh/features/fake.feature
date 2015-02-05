Feature: Create a fake project, release, and issue tree
         In order that I can play with sample data
         As a user
         I want a command to manufacture statistically believable data

    Scenario: A user creates a default fake project tree
        Given The user is at the command line
        When I enter the command "fake"
        Then The fake project key is in the database
        And The fake release is in the fake project
        And The fake release has 19 fake issues

