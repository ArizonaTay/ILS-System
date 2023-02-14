## Library Management System

# Overview
This report provides an in-depth review of two functions in the Library Management System. The functions are loan2 and makereservation.

## Function loan2
The function loan2 is responsible for managing loan operations in the library. It takes two parameters bookid and action. The function is accessible to logged-in users who are not administrators.

The function starts by initializing the database connection and populating the necessary variables, such as user and session. It then checks the following conditions:

The number of books a user has on loan (loancount) must not exceed 4.
The user must not have any outstanding fines.
The book being requested must not be on loan.
If the action parameter is set to reserve, the book must not be reserved by another user.
If all the conditions are met, the function proceeds to loan or reserve the book depending on the value of the action parameter. If the user has a reservation for the book, the reservation is converted to a loan.

In case any of the conditions are not met, an error message is displayed and the user is redirected to the book search page.

## Function makereservation
The function makereservation is responsible for managing book reservation operations in the library. It takes one parameter bookid. The function is accessible to logged-in users who are not administrators.

The function starts by initializing the database connection and checking if the user has any outstanding fines. If there are any, the user is redirected to the book search page with an error message.

The function then checks if the book is already reserved or currently on loan to the user. If either of these conditions is met, the user is redirected to the book search page with an error message.

If all conditions are met, the function proceeds to reserve the book and commit the reservation to the database. The user is then redirected to the book search page with a success message.

## Conclusion
The loan2 and makereservation functions are crucial components of the Library Management System. They ensure that the lending and reservation operations are executed seamlessly and that the rules and conditions set out by the library are followed.
