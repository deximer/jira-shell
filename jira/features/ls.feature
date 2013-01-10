Feature: list issues in a release
         So that I can better understand the state of the workflow
         As a user
         I want to be able to query issues within a release

    Scenario: A user lists the issues in a release
        Given I have the following issues in the release
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-2 | Bar 2 |
        | NG-3 | Baz 3 |
        When I enter the command "ls"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-2 | Bar 2 |
        | NG-3 | Baz 3 |

    Scenario: A user lists issues in a release with a status of 3
        Given I have the following issues in the release
        | key  | title | status |
        | NG-1 | Foo 1 | 3      |
        | NG-2 | Bar 2 | 6      |
        | NG-3 | Baz 3 | 3      |
        | NG-4 | Baz 4 | 1      |
        When I enter the command "ls -s 3"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        And I do not see "NG-4" in the output
        And I do not see "NG-2" in the output

    Scenario: A user lists issues of type 72 in the release
        Given I have the following issues in the release
        | key  | title | type |
        | NG-1 | Foo 1 | 72   |
        | NG-2 | Bar 2 | 78   |
        | NG-3 | Baz 3 | 72   |
        | NG-4 | Baz 4 | 1    |
        When I enter the command "ls -t 72"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        And I do not see "NG-4" in the output
        And I do not see "NG-2" in the output

    Scenario: A user lists issues of type 72 or type 1 in the release
        Given I have the following issues in the release
        | key  | title | type |
        | NG-1 | Foo 1 | 72   |
        | NG-2 | Bar 2 | 78   |
        | NG-3 | Baz 3 | 72   |
        | NG-4 | Baz 4 | 1    |
        When I enter the command "ls -t 72 1"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        | NG-4 | Baz 3 |
        And I do not see "NG-2" in the output

    Scenario: A user lists issues for a the MathML team
        Given I have the following issues in the release
        | key  | title | team   |
        | NG-1 | Foo 1 | MathML |
        | NG-2 | Bar 2 | Foo    |
        | NG-3 | Baz 3 | MathML |
        | NG-4 | Baz 4 | Bar    |
        When I enter the command "ls Math"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        | NG-3 | Baz 3 |
        And I do not see "NG-4" in the output
        And I do not see "NG-2" in the output

    Scenario: A user lists issues for a the MathML and status 6 and type 72
        Given I have the following issues in the release
        | key  | title | team   | status | type |
        | NG-1 | Foo 1 | MathML | 6      | 72   |
        | NG-2 | Bar 2 | Foo    | 1      | 72   |
        | NG-3 | Baz 3 | MathML | 1      | 1    |
        | NG-4 | Baz 4 | Bar    | 6      | 72   |
        When I enter the command "ls Math -s 6 -t 72"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        And I do not see "NG-2" in the output
        And I do not see "NG-3" in the output
        And I do not see "NG-4" in the output

    Scenario: A user lists issues with an estimate of 2
        Given I have the following issues in the release
        | key  | title | points |
        | NG-1 | Foo 1 | 2.0    |
        | NG-2 | Bar 2 | 1.0    |
        | NG-3 | Baz 3 | 0.499  |
        When I enter the command "ls -p 2"
        Then I see these issues listed
        | key  | title |
        | NG-1 | Foo 1 |
        And I do not see "NG-2" in the output
        And I do not see "NG-3" in the output