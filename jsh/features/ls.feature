Feature: list issues in a release
         So that I can better understand the state of the workflow
         As a user
         I want to be able to query issues within a release

    Scenario: A user lists the issues in a release
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-2 | Bar 2 |
        | NG-3 | Baz 3 |
        And I am in the directory "/1.0"
        When I enter the command "ls"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-2 | Bar 2 |
        | NG-3 | Baz 3 |

    Scenario: A user lists issues in a release with a status of 3
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | status |
        | NG-1 | Foo 1 | 3      |
        | NG-2 | Bar 2 | 6      |
        | NG-3 | Baz 3 | 3      |
        | NG-4 | Baz 4 | 1      |
        And I am in the directory "/1.0"
        When I enter the command "ls -s 3"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        And I do not see "NG-4" in the output
        And I do not see "NG-2" in the output

    Scenario: A user tries to list issues but uses an invalid status
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | status |
        | NG-1 | Foo 1 | 3      |
        | NG-2 | Bar 2 | 6      |
        | NG-3 | Baz 3 | 3      |
        | NG-4 | Baz 4 | 1      |
        And I am in the directory "/1.0"
        When I enter the command "ls -s invalid"
        Then I see "Error: invalid is an invalid status" in the output
        And I do not see "Team:" in the output

    Scenario: A user lists issues of type 72 in the release
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type |
        | NG-1 | Foo 1 | 72   |
        | NG-2 | Bar 2 | 78   |
        | NG-3 | Baz 3 | 72   |
        | NG-4 | Baz 4 | 1    |
        And I am in the directory "/1.0"
        When I enter the command "ls -t 72"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        And I do not see "NG-4" in the output
        And I do not see "NG-2" in the output

    Scenario: A user lists issues of type 72 or type 1 in the release
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type |
        | NG-1 | Foo 1 | 72   |
        | NG-2 | Bar 2 | 78   |
        | NG-3 | Baz 3 | 72   |
        | NG-4 | Baz 4 | 1    |
        And I am in the directory "/1.0"
        When I enter the command "ls -t 72 1"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        | NG-4 | Baz 3 |
        And I do not see "NG-2" in the output

    Scenario: A user lists issues for a the MathML team
        Given I have the following release
        | key |
        | 1.0 |
        Given I have the following issues in the release
        | key  | title | team   |
        | NG-1 | Foo 1 | MathML |
        | NG-2 | Bar 2 | Foo    |
        | NG-3 | Baz 3 | MathML |
        | NG-4 | Baz 4 | Bar    |
        And I am in the directory "/1.0"
        When I enter the command "ls Math"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        And I do not see "NG-4" in the output
        And I do not see "NG-2" in the output

    Scenario: A user lists issues that are not the MathML team
        Given I have the following release
        | key |
        | 1.0 |
        Given I have the following issues in the release
        | key  | title | team   |
        | NG-1 | Foo 1 | MathML |
        | NG-2 | Bar 2 | Foo    |
        | NG-3 | Baz 3 | MathML |
        | NG-4 | Baz 4 | Bar    |
        And I am in the directory "/1.0"
        When I enter the command "ls !Math"
        Then I see these issues listed
        | key  | title |
        | NG-2 | Bar 2 |
        | NG-4 | Baz 4 |
        And I do not see "NG-3" in the output
        And I do not see "NG-1" in the output

    Scenario: A user lists issues for a the MathML and status 6 and type 72
        Given I have the following release
        | key |
        | 1.0 |
        Given I have the following issues in the release
        | key  | title | team   | status | type |
        | NG-1 | Foo 1 | MathML | 6      | 72   |
        | NG-2 | Bar 2 | Foo    | 1      | 72   |
        | NG-3 | Baz 3 | MathML | 1      | 1    |
        | NG-4 | Baz 4 | Bar    | 6      | 72   |
        And I am in the directory "/1.0"
        When I enter the command "ls Math -s 6 -t 72"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        And I do not see "NG-2" in the output
        And I do not see "NG-3" in the output
        And I do not see "NG-4" in the output

    Scenario: A user lists issues with an estimate of 2
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | points |
        | NG-1 | Foo 1 | 2.0    |
        | NG-2 | Bar 2 | 1.0    |
        | NG-3 | Baz 3 | 0.499  |
        And I am in the directory "/1.0"
        When I enter the command "ls -w 2"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        And I do not see "NG-2" in the output
        And I do not see "NG-3" in the output

    Scenario: A user lists issues that are not in state 6
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | status |
        | NG-1 | Foo 1 | 6      |
        | NG-2 | Bar 2 | 6      |
        | NG-3 | Baz 3 | 3      |
        And I am in the directory "/1.0"
        When I enter the command "ls -s !6"
        Then I see these issues listed
        | key  | title |
        | NG-3 | Baz 3 |
        And I do not see "NG-1" in the output
        And I do not see "NG-2" in the output

    Scenario: A user lists issues that are not of type 78
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type |
        | NG-1 | Foo 1 | 72   |
        | NG-2 | Bar 2 | 78   |
        | NG-3 | Baz 3 | 1    |
        And I am in the directory "/1.0"
        When I enter the command "ls -t !78"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        And I do not see "NG-2" in the output

    Scenario: A user lists issues for a specific developer
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | dev |
        | NG-1 | Foo 1 | 72   | joe |
        | NG-2 | Bar 2 | 78   | ann |
        | NG-3 | Baz 3 | 1    | nic |
        | NG-4 | Baz 4 | 72   | ann |
        And I am in the directory "/1.0"
        When I enter the command "ls -d an"
        Then I see "NG-2" in the output
        And I see "NG-4" in the output
        And I do not see "NG-1" in the output
        And I do not see "NG-3" in the output

    Scenario: A user lists issues for several developers
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | dev |
        | NG-1 | Foo 1 | 72   | joe |
        | NG-2 | Bar 2 | 78   | ann |
        | NG-3 | Baz 3 | 1    | nic |
        | NG-4 | Baz 4 | 72   | ann |
        And I am in the directory "/1.0"
        When I enter the command "ls -d ann nic"
        Then I see "NG-2" in the output
        And I see "NG-4" in the output
        And I see "NG-3" in the output
        And I do not see "NG-1" in the output

    Scenario: A user views the cycle times for listed issues
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | started | resolved |
        | NG-1 | Foo 1 | 7    | 13/9/1  | 13/9/3   |
        | NG-2 | Bar 2 | 1    | 13/9/7  | 13/9/17  |
        | NG-3 | Baz 3 | 1    | 13/9/2  | 13/9/2   |
        And I am in the directory "/1.0"
        When I enter the command "ls"
        Then I see "Start  1  " in the output
        And I see "Start  6  " in the output
        And I see "Start       " in the output

    Scenario: A user views the cycle times over the specified amount
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | started | resolved |
        | NG-1 | Foo 1 | 7    | 13/9/1  | 13/9/3   |
        | NG-2 | Bar 2 | 1    | 13/9/7  | 13/9/17  |
        | NG-3 | Baz 3 | 7    | 13/9/2  | 13/9/9   |
        | NG-4 | Baz 4 | 7    | 13/9/2  | 13/9/20  |
        And I am in the directory "/1.0"
        When I enter the command "ls -y 5"
        Then I do not see "InPro  1  " in the output
        Then I do not see "  5  " in the output
        And I see "  6  " in the output
        And I see "  14 " in the output
        And I see "Total Issues: 2" in the output

    Scenario: A user lists issues that have backflow
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | started | resolved |
        | NG-1 | Foo 1 | 72   | 13/9/1  | 13/9/3   |
        | NG-2 | Bar 2 | 78   | 13/9/7  | 13/9/17  |
        | NG-3 | Baz 3 | 1    | 13/9/2  | 13/9/2   |
        And Issue "NG-2" has this transition history
        | date   | from  | to    |
        | 13/9/1 | 10024 | 10002 |
        | 13/9/5 | 10002 | 10024 |
        | 13/9/5 | 10024 | 10002 |
        | 13/9/9 | 10002 | 6     |
        And I am in the directory "/1.0"
        When I enter the command "ls -b"
        Then I see "NG-2" in the output
        And I see "<2" in the output
        And I do not see "NG-1" in the output
        And I do not see "NG-3" in the output

    Scenario: A user view the story points in a listing
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | started | resolved | points |
        | NG-1 | Foo 1 | 1    | 13/9/1  | 13/9/3   | 1      |
        | NG-2 | Bar 2 | 7    | 13/9/7  | 13/9/17  | 2      |
        | NG-3 | Baz 3 | 7    | 13/9/2  | 13/9/2   | 9      |
        And I am in the directory "/1.0"
        When I enter the command "ls"
        Then I see "Story Points: 11" in the output

    Scenario: A user view the total epic points in a listing
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | started | resolved | points |
        | NG-1 | Foo 1 | 71   | 13/9/1  | 13/9/3   | 1      |
        | NG-2 | Bar 2 | 71   | 13/9/7  | 13/9/17  | 2      |
        | NG-3 | Baz 3 | 72   | 13/9/2  | 13/9/2   | 9      |
        And I am in the directory "/1.0"
        When I enter the command "ls"
        Then I see "Epic Points: 3" in the output

    Scenario: A user lists the contents of an issue
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title |
        | NG-1 | Foo 1 |
        And I am in the directory "/1.0/NG-1"
        When I enter the command "ls"
        Then I see "links                              None" in the output

    Scenario: A lists all issues with a specific label
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | started | resolved | points | labels |
        | NG-1 | Foo 1 | 71   | 13/9/1  | 13/9/3   | 1      | l1     |
        | NG-2 | Bar 2 | 71   | 13/9/7  | 13/9/17  | 2      | l2     |
        | NG-3 | Baz 3 | 72   | 13/9/2  | 13/9/2   | 9      | l3     |
        And I am in the directory "/1.0"
        When I enter the command "ls -l l2"
        Then I see "NG-2" in the output
        And I do not see "NG-1" in the output
        And I do not see "NG-3" in the output

    Scenario: A lists all issues with a specific component
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | started | resolved | points | component |
        | NG-1 | Foo 1 | 71   | 13/9/1  | 13/9/3   | 1      | c1        |
        | NG-2 | Bar 2 | 71   | 13/9/7  | 13/9/17  | 2      | c2        |
        | NG-3 | Baz 3 | 72   | 13/9/2  | 13/9/2   | 9      | c3        |
        And I am in the directory "/1.0"
        When I enter the command "ls -c c2"
        Then I see "NG-2" in the output
        And I do not see "NG-1" in the output
        And I do not see "NG-3" in the output

