Feature: Manage issue components
         In order that I can make use of components in my analysis
         As a user
         I want a method to perform various operations on components

    Scenario: A user views all the unique components in a collection of issues
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | status | points | team | components |
        | NG-1 | Foo1  | 6      | 2.0    | Foo  | c1,c3      |
        | NG-2 | Bar2  | 3      | 3.0    | Foo  | c1         |
        | NG-3 | Baz3  | 3      | 6.0    | Bar  | c2         |
        And I am in the directory "/1.0"
        When I enter the command "components"
        Then I see "c1" in the output
        And I see "c2" in the output
        And I see "c3" in the output
