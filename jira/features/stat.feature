Feature: List critial information about a specific issue
         In order that I can view critical information about an issue
         As a user
         I want a command to list critical data for a specific issue

    Scenario: A user lists critical data for a specific issue
        Given I have the following issues in the release
        | key  | title | status | type | dev |
        | NG-1 | Foo1  | 1      | 1    | joe |
        | NG-2 | Bar2  | 2      | 72   | ann |
        | NG-3 | Baz3  | 3      | 78   | nic |
        When I enter the command "stat NG-2"
        Then I see critical data for the specific issue
        | key  | title | status | type |
        | NG-2 | Bar2  | 2      | 72   |
        And I see "Developer: ann" in the output

    Scenario: A user enters only the numeric portion of an issue id
        Given I have the following issues in the release
        | key  | title | status | type | dev |
        | NG-1 | Foo1  | 1      | 1    | joe |
        | NG-2 | Bar2  | 2      | 72   | ann |
        | NG-3 | Baz3  | 3      | 78   | nic |
        When I enter the command "stat 2"
        Then I see critical data for the specific issue
        | key  | title | status | type |
        | NG-2 | Bar2  | 2      | 72   |
        And I see "Developer: ann" in the output

    Scenario: A user does not supply an issue id
        Given The user is at the command line
        When I enter the command "stat"
        Then I see "Error: you must specify an issue key" in the output
