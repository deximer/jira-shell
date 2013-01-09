Feature: Report data required by the ExecReport.xls
         In order that I can create the ExecReport.xls
         As a user
         I want to see all numbers required by the report

    Scenario: A user views the aggrigate stats for the release
        Given I have the following issues in the release
        | key  | title | type | status | points | created |started | resolved |
        | NG-1 | Foo1  | 72   | 6      | 2.0    | 13/8/20 | 13/9/1 | 13/9/15  |
        | NG-2 | Bar2  | 72   | 3      | 3.0    | 13/8/20 | 13/9/1 | 13/9/7   |
        | NG-3 | Baz3  | 72   | 3      | 6.0    | 13/8/20 | 13/9/1 | 13/9/21  |
        | NG-4 | Bug1  | 1    | 3      | 0.499  | 13/9/1  | 13/9/2 | 13/9/3   |
        | NG-5 | Bug2  | 1    | 6      | 0.499  | 13/9/1  | 13/9/3 | 13/9/5   |
        | NG-6 | Bug3  | 78   | 6      | 0.499  | 13/9/1  | 13/9/9 | 13/9/16  |
        When I enter the command "report"
        Then I see "Stories          : 3" in the output
        And I see "  Avg Size       : 3.7" in the output
        And I see "  Std Dev        : 2.1" in the output
        And I see "  Smallest       : 2.0" in the output
        And I see "  Largest        : 6.0" in the output
        And I see "  # In Process   : 2" in the output
        And I see "  Avg Cycle Time : 13.3" in the output
        And I see "  m Cycle Time   : 14.0" in the output
        And I see "  Std Cycle Time : 7.0" in the output
        And I see "Bugs             : 3" in the output
        And I see "  Production     : 1" in the output
        And I see "    Avg Cycle Time : 15.0" in the output
        And I see "    m Cycle Time   : 15.0" in the output
        And I see "    Std Cycle Time : nan" in the output
        And I see "  Development    : 2" in the output
        And I see "    Avg Cycle Time : 3.0" in the output
        And I see "    m Cycle Time   : 3.0" in the output
        And I see "    Std Cycle Time : 1.4" in the output
        And I see "Points in scope  : 11.0" in the output
        And I see "Points completed : 2.0" in the output
        And I see "Total WIP        : 9" in the output
        And I see "NG-5 4" in the output
        And I see "NG-3 20" in the output
        And I do not see "NG-1" in the output
        And I do not see "NG-2" in the output

    Scenario: A user views a specific team stats for the release
        Given I have the following issues in the release
| key  | title | type | status | points | created |started | resolved | team |
| NG-1 | Foo1  | 72   | 6      | 2.0    | 13/8/20 | 13/9/1 | 13/9/15  | foo  |
| NG-2 | Bar2  | 72   | 3      | 3.0    | 13/8/20 | 13/9/1 | 13/9/7   | foo  |
| NG-3 | Baz3  | 72   | 3      | 6.0    | 13/8/20 | 13/9/1 | 13/9/21  | bar  |
| NG-4 | Bug1  | 1    | 3      | 0.499  | 13/9/1  | 13/9/2 | 13/9/3   | foo  |
| NG-5 | Bug2  | 1    | 6      | 0.499  | 13/9/1  | 13/9/3 | 13/9/5   | bar  |
| NG-6 | Bug3  | 78   | 6      | 0.499  | 13/9/1  | 13/9/9 | 13/9/16  | foo  |
        When I enter the command "report foo"
        Then I see "Stories          : 2" in the output
        And I see "  Avg Size       : 2.5" in the output

    Scenario: A user views a specific developer's stats for the release
        Given I have the following issues in the release
| key  | title | type | status | points | created |started | resolved | dev |
| NG-1 | Foo1  | 72   | 6      | 2.0    | 13/8/20 | 13/9/1 | 13/9/15  | joe |
| NG-2 | Bar2  | 72   | 3      | 3.0    | 13/8/20 | 13/9/1 | 13/9/7   | joe |
| NG-3 | Baz3  | 72   | 3      | 6.0    | 13/8/20 | 13/9/1 | 13/9/21  | ann |
| NG-4 | Bug1  | 1    | 3      | 0.499  | 13/9/1  | 13/9/2 | 13/9/3   | joe |
| NG-5 | Bug2  | 1    | 6      | 0.499  | 13/9/1  | 13/9/3 | 13/9/5   | ann |
| NG-6 | Bug3  | 78   | 6      | 0.499  | 13/9/1  | 13/9/9 | 13/9/16  | joe |
        When I enter the command "report -d ann"
        Then I see "Stories          : 1" in the output
        And I see "  Avg Size       : 6.0" in the output
