Feature: Reveal meaning of various status codes
         As a user
         I want a the application to reveal the meaning of the codes in english
         so that I can understand the meaning of the various codes

  Scenario: A user lists a legend detailing the meaning of all types
    Given The user is at the command line
    When I enter the command "legend"
    Then I see "Status codes:" in the output
    And I see "1     : New" in the output
    And I see "3     : In Progress" in the output
    And I see "4     : Reopened" in the output
    And I see "6     : Closed" in the output
    And I see "Issue types:" in the output
    And I see "1     : Bug" in the output
    And I see "3     : Task" in the output
    And I see "7     : Story" in the output

  Scenario: A user lists a legend detailing the meaning of the status codes
    Given The user is at the command line
    When I enter the command "legend status"
    Then I see "Status codes:" in the output
    And I see "1     : New" in the output
    And I see "3     : In Progress" in the output
    And I see "4     : Reopened" in the output
    And I see "6     : Closed" in the output
    And I do not see "Issue types:" in the output

  Scenario: A user lists a legend detailing the meaning of issue types
    Given The user is at the command line
    When I enter the command "legend issuetype"
    Then I do not see "Status codes:" in the output
    And I see "Issue types:" in the output
    And I see "1     : Bug" in the output
    And I see "3     : Task" in the output
    And I see "7     : Story" in the output