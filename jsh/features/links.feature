Feature: Render issue link graph
         In order that I can trace the relationships between issues over time
         As a user
         I want a way to visualize the link dependancies between issues

    Scenario: A user lists the link graph for a specified issue
        Given I have the following issues in the release
        | key    | title | status | type | dev |
        | NG-1   | Foo1  | 1      | 1    | joe |
        | NG-2   | Bar2  | 2      | 72   | ann |
        | MTQA-1 | Baz3  | 9999   | 78   | nic |
        And Issue "NG-2" has the following links
        | key  |
        | NG-1 |
        When I enter the command "links NG-2"
        Then I see "-> NG-1" in the output
        And I do not see "-> MTQA-1" in the output

    Scenario: A user lists only dev bugs in the link graph for a specified issue
        Given I have the following issues in the release
        | key    | title | status | type | dev |
        | NG-1   | Foo1  | 1      | 1    | joe |
        | NG-2   | Bar2  | 2      | 72   | ann |
        | NG-3   | Bar2  | 2      | 1    | ann |
        | MTQA-1 | Baz3  | 9999   | 78   | nic |
        And Issue "NG-2" has the following links
        | key    |
        | NG-1   |
        | MTQA-1 |
        And Issue "NG-1" has the following links
        | key    |
        | NG-3   |
        When I enter the command "links NG-2 -t 1"
        Then I see "-> NG-1" in the output
        And I see "-> NG-3" in the output
        And I do not see "-> MTQA-1" in the output

    Scenario: A user changes the graph traversal method to tracking bugs
        Given I have the following issues in the release
        | key    | title | status | type | dev |
        | NG-1   | Foo1  | 1      | 72   | joe |
        | NG-2   | Bar2  | 2      | 72   | ann |
        | NG-3   | Bar2  | 2      | 1    | ann |
        | NG-4   | Baz3  | 3      | 1    | nic |
        | NG-5   | Baz3  | 3      | 1    | nic |
        And Issue "NG-1" has the following links
        | key    |
        | NG-2   |
        | NG-3   |
        And Issue "NG-3" has the following links
        | key    |
        | NG-5   |
        And Issue "NG-2" has the following links
        | key    |
        | NG-4   |
        When I enter the command "links NG-1 -b"
        Then I see "NG-1" in the output
        And I see "-> NG-3" in the output
        And I see "-> NG-5" in the output
        And I do not see "-> NG-2" in the output
        And I do not see "-> NG-4" in the output
