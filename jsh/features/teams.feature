Feature: List the scrum teams that are participating in a release
         In order that I can identify which teams are active in a release
         As a user
         I want a method to display the scrum teams working a release

    Scenario: A user views the the scrum teams with assigned work in a release
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | status | points | team |
        | NG-1 | Foo1  | 6      | 2.0    | Foo |
        | NG-2 | Bar2  | 3      | 3.0    | Foo |
        | NG-3 | Baz3  | 3      | 6.0    | Bar |
        And I am in the directory "/1.0"
        When I enter the command "teams"
        Then I see these teams listed
        | team | stories |
        | Foo  | 2       |
        | Bar  | 1       |
