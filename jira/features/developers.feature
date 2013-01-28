Feature: List the developers that are participating in a release
         In order that I can quickly identify the developers in a release
         As a user
         I want a method to quickly display the developers working on a release

    Scenario: A user views the the developers with assigned work in a release
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | dev |
        | NG-1 | Foo1  | ann |
        | NG-2 | Bar2  | ann |
        | NG-3 | Baz3  | joe |
        And I am in the directory "/1.0"
        When I enter the command "developers"
        Then I see these developers listed
        | dev | stories |
        | joe | 1       |
        | ann | 2       |
