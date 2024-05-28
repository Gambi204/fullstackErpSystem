JikoTrack: A Web-Based Solution for Small Restaurant Management

 Introduction

JikoTrack is a comprehensive web-based system designed specifically for small eateries to streamline accounting and inventory management processes. This solution aims to address the operational inefficiencies and financial challenges faced by small restaurant enterprises, providing a unified platform for optimizing accounting and inventory management procedures.

 Features

- Inventory Management: Track inventory levels in real-time, manage stock movements, and streamline supplier communications.
- Accounting Module: Simplify expense tracking, revenue management, and financial reporting for improved financial transparency.
- Reporting Dashboard: Visualize key performance indicators and gain actionable insights into business operations.
- User-Friendly Interface: Intuitive navigation ensures ease of use for small restaurant owners and employees.

 Methodology

- Structured System Analysis and Design Methodology (SSADM): Employed for deep analysis and structured planning of the system.
- Design Thinking: Utilized for problem-solving, emphasizing user-centric solutions and rapid prototyping.

 Installation Guide

1. Create a Virtual Environment:
   
   python -m venv venv
   

2. Activate the Virtual Environment:
   
   .\venv\Scripts\Activate
   

3. Install Required Python Packages:
   
   pip install mysqlclient
   pip install django-mysql
   pip install django-cors-headers
   pip install PyJWT
   pip install django-filter
   pip install markdown
   pip install djangorestframework
   pip install phonenumbers
   pip install djangorestframework-simplejwt
   pip install pycountry
   

4. Install Pipenv:
   
   pip install pipenv
   

5. Configure Database Connection:
   - Navigate to settings.py and configure database credentials under the DATABASES section.

6. Set Up and Migrate the Database:
   
   python manage.py makemigrations
   python manage.py migrate
   

7. Run the Django Development Server:
   
   python manage.py runserver
   

 Dependencies

- MySQL
- Django
- Django REST Framework
- PyJWT
- Django Filter
- Django CORS Headers
- Django MySQL
- Django REST Framework Simple JWT
- Phonenumbers
- Pycountry

 License

This project is licensed under the [MIT License](LICENSE).

 Contributors

- Strathmore University
