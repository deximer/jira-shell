Feature: Release simulation
         So that I can predict the failure rate of a work strategy
         As a user
         I want to simulate releases based on empirical or theoretical data

    Scenario: A user simulates a theoretical release
        Given I am in the directory "/"
        When I enter the command "simulate -a 7.9 -d 9.1 -s 136 -p 19 -b 33 -v 23 -t 1 -c 10 -e 2.2 1.2"
        Then I see "Work:" in the output
        And I see "Capacity:" in the output
        And I see "-s 136" in the output
        And I see "-p 19" in the output

    Scenario: A user simulates an actual release
        Given I have the following release
        | key |
        | 1.0 |
        And I have the following issues in the release
        | key  | title | type | started | resolved | dev |
        | NG-1 | Foo 1 | 72   | 13/9/1  | 13/9/3   | ann |
        | NG-2 | Bar 2 | 72   | 13/9/7  | 13/9/17  | ann |
        | NG-3 | Baz 3 | 72   | 13/9/2  | 13/9/2   | nik |
        And I am in the directory "/1.0"
        When I enter the command "simulate"
        Then I see "Work:" in the output
        And I see "Capacity:" in the output
        And I see "-s 3" in the output
        And I see "-p 1" in the output

    Scenario: A user lists the simulation run history
        Given I am in the directory "/"
        When I enter the command "simulate -a 7.9 -d 9.1 -s 136 -p 19 -b 33 -v 23 -c 1"
        And I enter the command "simulate -z"
        Then I see "1 : simulate -s 136" in the output

    Scenario: A user executes a simulation from the run history
        Given I am in the directory "/"
        When I enter the command "simulate -a 7.9 -d 9.1 -s 136 -p 19 -b 33 -v 23 -c 1"
        And I enter the command "simulate -x 1"
        Then I see "Work:" in the output
        And I see "Capacity:" in the output
        And I see "-s 136" in the output
        And I see "-p 19" in the output

    Scenario: A user prints detailed simulation information
        Given I am in the directory "/"
        When I enter the command "simulate -a 7.9 -d 9.1 -s 136 -p 19 -b 33 -v 23 -c 1"
        And I enter the command "simulate -i 1 0"
        Then I see "Work Load:" in the output
        And I see "Starting Pair Capacity:" in the output
        And I see "Ending Pair Capacity:" in the output

    Scenario: A user runs simulate unparamiterized while not in a release
        Given I am in the directory "/"
        When I enter the command "simulate"
        Then I see "Error: you must be in a release to run simulate without all parameters specified" in the output
