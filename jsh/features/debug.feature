Feature: Enter the Python debugger
         In order that I can investigate and diagnose application issues
         As a user
         I want a method to activate the Python debugger

    Scenario: A user activates the Python debugger
        Given I am at the root
        When I enter the command "debug"
        Then I see the pdb debug prompt
