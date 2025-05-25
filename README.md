# Travel Management System

A Flask-based web application for managing travel plans and itineraries.

## Features

- User authentication (login/register)
- Create and manage travel plans
- View trip details including destination, dates, and descriptions
- Modern and responsive UI

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd travel-management-system
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- On Windows:
```bash
venv\Scripts\activate
```
- On macOS/Linux:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Make sure you're in the project directory and your virtual environment is activated.

2. Initialize the database:
```bash
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

3. Run the application:
```bash
python app.py
```

4. Open your web browser and navigate to `http://localhost:5000`

## Project Structure

```
travel-management-system/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, JS, images)
│   └── css/
│       └── style.css
├── templates/         # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── add_trip.html
└── README.md          # This file
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details. 