# TechnoDynamicV2 API
TechnoDynamicV2 (Techno-Dynamic-Learning V2) API serves as the backend service for  [Techno-Dynamic-Learning V2](https://github.com/jmarcbalbada/techno-dynamic-v2), powering advanced learning management features, dynamic content generation, content versioning, and AI-driven insights. It provides a robust and scalable web API to enhance the technopreneurship learning experience.

## Features

- **User-friendly Interface**: Intuitive and accessible interface for seamless user interactions.
- **AI Chatbot Assistant**: Provides personalized support, addressing student inquiries with real-time responses.
- **Dynamic Content Generation**: Automatically generates and updates content based on student inquiries and interactions.
- **Insights and Suggestions**: Analyzes FAQ data to offer actionable insights and suggestions for educators and students.
- **Content Versioning**: Allows users to create, manage, and restore different content versions, enabling easy rollback to previous versions for effective lesson management.

Follow these steps to set up and run the backend:

> Backend - Django

1. Clone the backend repository

```bash
  git clone https://github.com/jmarcbalbada/technodynamicAPI.git
```

1. Create a virtual environment

```bash
  python -m venv venv
```

2. Activate a virtual environment

```bash
  .\venv\scripts\activate
```

3. Install dependencies

```bash
  pip install -r requirements.txt
```

4. Run PostgreSQL db via Docker

```bash
  docker compose up
```

5. Run migration

```bash
  python manage.py makemigrations
  python manage.py migrate
```

6. Run backend server

```bash
  python3 manage.py runserver / python manage.py runserver
```

## Features
The API is built using the Django REST framework and comes with Swagger documentation, which provides an interactive interface to explore and test the API. Once the server is running, you can access the Swagger documentation at:

```bash
  [docker compose up](http://localhost:8000/swagger/)
```

For concerns/inquiries, [contact](mailto:jmarcbalbada@gmail.com).

> All rights reserved 2024.
