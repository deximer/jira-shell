Feature: Manage issue versions
         In order that I can make use of versions in my analysis
         As a user
         I want a method to perform various operations on versions

    Scenario: A user views all the unique versions in a collection of issues
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | status | points | team | fix |
        | NG-1 | Foo1  | 6      | 2.0    | Foo  | v1  |
        | NG-2 | Bar2  | 3      | 3.0    | Foo  | v1  |
        | NG-3 | Baz3  | 3      | 6.0    | Bar  | v2  |
        And I am in the directory "/1.0"
        When I enter the command "versions"
        Then I see "v1" in the output
        And I see "v2" in the output
