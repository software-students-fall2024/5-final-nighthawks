# Group Study Session Tracker

[![CI/CD Pipeline](https://github.com/software-students-fall2024/5-final-nighthawks/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/software-students-fall2024/5-final-nighthawks/actions/workflows/ci-cd.yml)
[![log github events](https://github.com/software-students-fall2024/5-final-nighthawks/actions/workflows/event-logger.yml/badge.svg)](https://github.com/software-students-fall2024/5-final-nighthawks/actions/workflows/event-logger.yml)

## Description

The **Group Study Session Tracker** is a web-based application designed to help users organize and track study sessions. The system enables users to create, join, and manage study groups with features such as a calendar view, session scheduling, user availability management, and secure authentication. It is containerized for seamless deployment and includes a CI/CD pipeline for continuous integration and delivery.

## DockerHub Container Images

- **Backend**: [Study Scheduler Backend](https://hub.docker.com/r/yourusername/study-scheduler-backend)
- **Frontend**: [Study Scheduler Frontend](https://hub.docker.com/r/yourusername/study-scheduler-frontend)

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed on your system.
- A MongoDB instance accessible with the appropriate connection string.
- Python 3.10 or higher installed (for local testing and development).

### Steps to Run the Project

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/group-study-session-tracker.git
   cd group-study-session-tracker	
	```

2. **Set Up Environment Variables**
Create a .env file in the project root with the following content:

	```env
	MONGO_URI=mongodb://<username>:<password>@<host>:<port>/<database>
	SECRET_KEY=<your_secret_key>
	```

3. **Build and Run Containers**
Use Docker Compose to build and run the application:

```bash
docker-compose up --build
```
4. **Access the Application**
Once the containers are running:

The backend will be accessible at http://localhost:5000
The frontend will be accessible at http://localhost:3000

5. **Shut Down the Application**
To stop the application, run:

```bash
docker-compose down
```

## TEAM MEMBERS

- [Tahsin Tawhid](https://github.com/tahsintawhid)
- [James Whitten](https://github.com/jwhit0)
- [Jack Zhang](https://github.com/yz6973)
- [Joseph Hwang](https://github.com/JosephNYU)

