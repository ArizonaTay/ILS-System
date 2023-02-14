## Library Management System

# Overview
This report details the development and implementation of a Flask web application that manages a library information system (ILS). The ILS application is designed to keep track of books in a library and provides a platform for users to sign up, log in and perform various operations such as checking the books available, reserving a book, etc.

## Technical Overview
The ILS application is built using the Flask web framework, a Python-based micro-web framework. The application makes use of the following technologies and libraries:

Flask for web development
MySQL for data storage
PyMySQL for connecting to the MySQL database
MongoDB for storing the books data
PyMongo for connecting to the MongoDB database


## Sign up: 
Users can sign up for an account by providing their username and password.

##Log in: 
Users can log in to the application using their username and password.

##User View: 
Once logged in, users are directed to a page where they can view the books available in the library, filter the books based on the author, and reserve a book.

##Admin View: 
Admins can log in to the application using their username and password and are directed to a page where they can manage the books in the library and manage user accounts.

##Data Processing:
The data retrieved from MongoDB is processed to clean and display the information in a more readable format.

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
The code delivers a robust Flask application that seamlessly integrates with both MySQL and MongoDB databases, effectively functioning as a comprehensive Library Management system.
