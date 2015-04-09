Feature: Transitions
         In order that I can investigate all transitions for a board
         As a user
         I want a command with specific tools for transitions

    Scenario: A user asks when the next backlog issue will be done
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | status | rank   | created |started | resolved |
        | NG-1 | ng01  | 7    | 6      | 2      | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng01  | 7    | 6      | 2      | 15/3/23 | 15/3/26| 15/3/29  |
        | NG-3 | ng02  | 7    | 1      | 1      | 15/3/24 |        |          |
        And I am in the directory "/1.0"
        When I enter the command "transitions"
        Then I see "Total : 4" in the output
        And I see "First : 2015-03-23 00:00:00 NG-1" in the output
        And I see "Last  : 2015-03-29 00:00:00 NG-2" in the output
        And I see "Spread: 6 days" in the output
