Feature: Manage issue labels
         In order that I can make use of labels in my analysis
         As a user
         I want a method to perform various operations on labels

    Scenario: A user views all the unique labels in a collection of issues
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | status | points | team | labels |
        | NG-1 | Foo1  | 6      | 2.0    | Foo  | l1     |
        | NG-2 | Bar2  | 3      | 3.0    | Foo  | l1     |
        | NG-3 | Baz3  | 3      | 6.0    | Bar  | l2     |
        And I am in the directory "/1.0"
        When I enter the command "labels"
        Then I see "l1" in the output
        And I see "l2" in the output
