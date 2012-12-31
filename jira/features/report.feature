Feature: Report data required by the ExecReport.xls
         In order that I can create the ExecReport.xls
         As a user
         I want to see all numbers required by the report

    Scenario: A user views the total number of stories in scope
        Given I have the following issues in the release
        | key  | title | status | points |
        | NG-1 | Foo1  | 6      | 2.0    |
        | NG-2 | Bar2  | 3      | 3.0    |
        | NG-3 | Baz3  | 3      | 6.0    |
        When I enter the command "report"
        Then I see "Stories          : 3" in the output

    Scenario: A user views the total WIP in scope
        Given I have the following issues in the release
        | key  | title | status | points |
        | NG-1 | Foo1  | 6      | 2.0    |
        | NG-2 | Bar2  | 3      | 3.0    |
        | NG-3 | Baz3  | 3      | 6.0    |
        When I enter the command "report"
        Then I see "Total WIP        : 9" in the output
