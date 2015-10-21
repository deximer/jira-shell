Feature: Available To Promise
         In order that I can know when I can promise delivery
         As a user
         I want a method that will tell me when a group of issues will be done

    Scenario: A user asks when the next backlog issue will be done
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | status | rank   | created |started | resolved |
        | NG-1 | ng01  | 7    | 6      | 2      | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng02  | 7    | 1      | 1      | 15/3/24 |        |          |
        And I am in the directory "/1.0"
        When I enter the command "atp NG-2"
        Then I see "2015-05-12 1     New     NG-2     6" in the output

    Scenario: A user asks when a lower priority backlog issue will be done
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | status | rank   | created |started | resolved |
        | NG-1 | ng01  | 7    | 6      | 3      | 15/3/23 | 15/3/23| 15/3/27  |
        | NG-2 | ng02  | 7    | 1      | 2      | 15/3/24 |        |          |
        | NG-3 | ng03  | 7    | 1      | 1      | 15/3/24 |        |          |
        And I am in the directory "/1.0"
        When I enter the command "atp NG-3"
        Then I see "2015-05-12 1     New     NG-3     6" in the output
        And I see "2015-05-12" in the output

    Scenario: A user runs atp with no arguments 
        Given I have the following release
        | key |
        | 1.0 |
        And I am in the directory "/1.0"
        When I enter the command "atp"
        Then I see "No arguments" in the output

