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
