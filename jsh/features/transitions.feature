Feature: Transitions
         In order that I can investigate all transitions for a board
         As a user
         I want a command with specific tools for transitions

    Scenario: List an overview of the boards transitions
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | status | rank   | created |started | resolved |
        | NG-1 | ng01  | 7    | 6      | 2      | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng01  | 7    | 6      | 3      | 15/3/23 | 15/3/26| 15/3/29  |
        | NG-3 | ng02  | 7    | 1      | 1      | 15/3/24 |        |          |
        And I am in the directory "/1.0"
        When I enter the command "transitions"
        Then I see "Total : 4" in the output
        And I see "First : 2015-03-23 00:00:00 NG-1" in the output
        And I see "Last  : 2015-03-29 00:00:00 NG-2" in the output
        And I see "Spread: 6 days" in the output

    Scenario: All the transitions for all stories
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | status | rank   | created |started | resolved |
        | NG-1 | ng01  | 7    | 6      | 2      | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng01  | 7    | 6      | 3      | 15/3/23 | 15/3/26| 15/3/29  |
        | NG-3 | ng02  | 7    | 1      | 1      | 15/3/24 |        |          |
        And I am in the directory "/1.0"
        When I enter the command "transitions -a"
        Then I see "Total : 4" in the output
        And I see "2015-03-23 00:00:00 New   -> Start None  NG-1" in the output
        And I see "2015-03-29 00:00:00 Start -> Closd 1     NG-2" in the output

    Scenario: All the transitions for issue types 1 and 3
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | status | rank   | created |started | resolved |
        | NG-1 | ng01  | 7    | 6      | 2      | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng01  | 1    | 6      | 3      | 15/3/23 | 15/3/26| 15/3/29  |
        | NG-3 | ng02  | 3    | 6      | 1      | 15/3/20 | 15/3/22| 15/3/24  |
        And I am in the directory "/1.0"
        When I enter the command "transitions -a -t 1 3"
        Then I see "Total : 4" in the output
        And I see "Spread: 7 days" in the output
        And I see "2015-03-22 00:00:00 New   -> Start None  NG-3" in the output
        And I see "2015-03-29 00:00:00 Start -> Closd 1     NG-2" in the output

    Scenario: View all transitions for specific priorities
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | priority | rank | created |started | resolved |
        | NG-1 | ng01  | 7    | Critical | 2    | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng01  | 1    | 6        | 3    | 15/3/23 | 15/3/26| 15/3/29  |
        | NG-3 | ng02  | 3    | Critical | 1    | 15/3/20 | 15/3/22| 15/3/24  |
        And I am in the directory "/1.0"
        When I enter the command "transitions -a -p Critical"
        Then I see "Total : 4" in the output
        And I see "Spread: 5 days" in the output
        And I see "2015-03-22 00:00:00 New   -> Start None  NG-3" in the output
        And I see "2015-03-27 00:00:00 Start -> Closd 4     NG-1" in the output

    Scenario: View number of transitions by state
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | status | rank | created |started | resolved |
        | NG-1 | ng01  | 7    | 6      | 2    | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng01  | 1    | 6      | 3    | 15/3/23 | 15/3/26| 15/3/29  |
        | NG-3 | ng02  | 3    | 6      | 1    | 15/3/20 | 15/3/22|          |
        And I am in the directory "/1.0"
        When I enter the command "transitions -s"
        Then I see "Total : 5" in the output
        And I see "Closd : 2" in the output
        And I see "Start : 3" in the output

    Scenario: View number of transitions by state
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | status | rank | created |started | resolved |
        | NG-1 | ng01  | 7    | 6      | 2    | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng01  | 1    | 6      | 3    | 15/3/23 | 15/3/26| 15/3/29  |
        | NG-3 | ng02  | 3    | 6      | 1    | 15/3/20 | 15/3/22|          |
        And I am in the directory "/1.0"
        When I enter the command "transitions -s Closd"
        Then I see "2015-03-27 00:00:00 Start -> Closd 4     NG-1" in the output
