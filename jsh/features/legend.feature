Feature: Reveal meaning of various status codes
         In order that I can understand the meaning of the various codes
         As a user
         I want a the application to reveal the meaning of the codes in english

    Scenario: A user lists a legend detailing the meaning of the status codes
        Given The user is at the command line
        When I enter the command "legend"
        Then I see "1     : Open" in the output
        And I see "3     : In Progress" in the output
        And I see "4     : Reopened" in the output
        And I see "6     : Closed" in the output
        And I see "10036 : Verified" in the output
        And I see "10089 : Ready" in the output
        And I see "10090 : Completed" in the output
        And I see "10092 : QA Active" in the output
        And I see "10104 : QA Ready" in the output
        And I see "72    : Story" in the output
        And I see "1     : Development Bug" in the output
        And I see "78    : Production Bug" in the output
