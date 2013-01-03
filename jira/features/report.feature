Feature: Report data required by the ExecReport.xls
         In order that I can create the ExecReport.xls
         As a user
         I want to see all numbers required by the report

    Scenario: A user views the aggrigate stats for the release
        Given I have the following issues in the release
        | key  | title | status | points |
        | NG-1 | Foo1  | 6      | 2.0    |
        | NG-2 | Bar2  | 3      | 3.0    |
        | NG-3 | Baz3  | 3      | 6.0    |
        When I enter the command "report"
        Then I see "Stories          : 3" in the output
        And I see "Bugs             : 0" in the output
        And I see "Average Size     : 3.7" in the output
        And I see "Std Dev          : 2.1" in the output
        And I see "Smallest Story   : 2.0" in the output
        And I see "Largest Story    : 6.0" in the output
        And I see "Avg Cycle Time   : None" in the output
        And I see "Points in scope  : 11.0" in the output
        And I see "Points completed : 2.0" in the output
        And I see "Stories IP       : 2" in the output
        And I see "Total WIP        : 9" in the output

