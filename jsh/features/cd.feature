Feature: Change director
         So that I can explore the Jira project and release sturcture
         As a user
         I want some way to navigate the structure

    Scenario: A user changes the current context to a release 1.0
        Given I have the following release
        | key |
        | 1.0 |
        And I am in the directory "/"
        When I enter the command "cd 1.0"
        Then I see "/1.0 >" in the output

    Scenario: A user changes the context to an issue
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title |
        | NG-1 | Foo 1 |
        And I am in the directory "/"
        When I enter the command "cd 1.0/NG-1"
        Then I see "/1.0/NG-1 >" in the output
