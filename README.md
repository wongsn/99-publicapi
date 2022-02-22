# Submission for the Backend Tech Challenge

### Architecture
This submission comprises of 3 independent web applications:

- **[Listing service:](https://listing99.herokuapp.com)** Stores all the information about properties that are available to rent and buy
- **[User service:](https://users99.herokuapp.com)** Stores information about all the users in the system
- **[Public API layer:](https://public99.herokuapp.com)** Set of APIs that are exposed to the web/public

Respective API calls are detailed in the respective submodules.

## Introduction
The system is designed as a set of small web applications that each perform a specific task (otherwise known as "microservices"). The listing service and user service are backed by relevant databases to persist data. The services are essentially a wrapper around their respective databases to manipulate the data stored in them. For this reason, the services are not intended to be directly accessible by any external client/application.

Services are free to store the data in any format they wish (in a SQL table, or as a document in a NoSQL db, etc.). The only requirement is for them to expose a set of REST APIs that return data in a standardised JSON format. Services are the guardians/gatekeepers for their respective databases. **Any other application/service that wishes to access the data must go solely through the REST APIs exposed by the service. It cannot access the data directly from the database at any cost.**

How does the mobile app or user-facing website access the data in the system? This is where the public API layer comes in. The public API layer is a web application that contains APIs that can be called by external clients/applications. This web application is responsible for interacting with the listing/user service through its APIs to pull out the relevant data and return it to the external caller in the appropriate format.

