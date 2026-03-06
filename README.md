# ClassPulse – Coursework Planner

ClassPulse is a full-stack web application designed to help university students organise their courses, assignments, and study plans in one place.  
The system provides a dashboard overview, timetable management, and tools to track deadlines and study progress.

---

# Features

- User registration and login
- Course management
- Class timetable management
- Assignment tracking
- Study plan creation
- Dashboard timetable overview
- Assignment search and filtering
- Study plan countdown timer

---

# Technology Stack

### Backend
- Python
- Django
- Django REST Framework

### Frontend
- Vue.js
- Axios

### Database
- SQLite (development)

### Deployment
- Render (backend)
- Vercel (frontend)

---

# Running the Project

## Start Backend
1. Navigate to backend directory

cd backend

2. Create virtual environment

python -m venv venv

3. Activate virtual environment

source venv/bin/activate

4. Install dependencies

pip install -r requirements.txt

5. Run migrations

python manage.py migrate

6. Start server

python manage.py runserver

## Start Frontend
1. Navigate to frontend directory

cd frontend/classpulse-frontend

2. Install dependencies

npm install

3. Start development server

npm run dev

## Running Tests
Run all backend tests using:

python manage.py test planner
