Feature: List critial information about a specific issue
         In order that I can answer questions about a specific issue
         As a user
         I want a command to list critical data for a specific issue

    Scenario: A user lists critical data for a specific issue
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
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

    Scenario: A user enters a non "NG" style id
        Given I have the following issues in the release
        | key    | title | status | type | dev |
        | NG-1   | Foo1  | 1      | 1    | joe |
        | NG-2   | Bar2  | 2      | 72   | ann |
        | MTQA-1 | Baz3  | 3      | 78   | nic |
        When I enter the command "stat MTQA-1"
        Then I see critical data for the specific issue
        | key    | title | status | type |
        | MTQA-1 | Baz3  | InPro  | 78   |
        And I see "Developer: nic" in the output

    Scenario: A user stats an issue with states not in the MT Kanban
        Given I have the following issues in the release
        | key    | title | status | type | dev |
        | NG-1   | Foo1  | 1      | 1    | joe |
        | NG-2   | Bar2  | 2      | 72   | ann |
        | MTQA-1 | Baz3  | 9999   | 78   | nic |
        When I enter the command "stat MTQA-1"
        Then I see critical data for the specific issue
        | key    | title | status | type |
        | MTQA-1 | Baz3  | 9999   | 78   |
        And I see "Developer: nic" in the output

    Scenario: A user views the transition log for a specific issue
        Given I have the following issues in the release
        | key    | title | status | type | dev |
        | NG-1   | Foo1  | 1      | 1    | joe |
        | NG-2   | Bar2  | 2      | 72   | ann |
        | MTQA-1 | Baz3  | 9999   | 78   | nic |
        And Issue "NG-2" has this transition history
        | date   | from | to |
        | 13/9/1 | 1    | 3  |
        | 13/9/8 | 3    | 6  |
        When I enter the command "stat NG-2"
        Then I see "2013-09-01 12:30:00, [   ], Jane Doe          , Open  -> InPro" in the output
        And I see "2013-09-08 12:30:00, [7  ], Jane Doe          , InPro -> Closd" in the output

    Scenario: A user views the transition log for an issue with backflow
        Given I have the following issues in the release
        | key    | title | status | type | dev |
        | NG-1   | Foo1  | 1      | 1    | joe |
        | NG-2   | Bar2  | 2      | 72   | ann |
        | MTQA-1 | Baz3  | 9999   | 78   | nic |
        And Issue "NG-2" has this transition history
        | date   | from  | to    |
        | 13/9/1 | 1     | 10089 |
        | 13/9/2 | 10089 | 3     |
        | 13/9/3 | 3     | 10089 |
        | 13/9/4 | 10089 | 3     |
        | 13/9/5 | 3     | 6     |
        When I enter the command "stat NG-2"
        Then I see "2013-09-03 12:30:00, [1  ], Jane Doe          , InPro -> Ready <- backflow" in the output

    Scenario: A user does not supply an issue id
        Given The user is at the command line
        When I enter the command "stat"
        Then I see "Error: you must specify an issue key" in the output
