# Student Management System

A comprehensive, Django-based web application for managing students, staff, courses, attendance, and feedback within an
educational institution. The system provides dedicated portals for Administrators, Staff, and Students, each with
role-specific functionalities.

![Python CI](https://github.com/fahim06/student_management_system/actions/workflows/CICD-Build.yml/badge.svg)
![GitHub top language](https://img.shields.io/badge/Python-1E415E?style=for-the-badge&logo=python&logoColor=blue)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)

---

## ✨ Key Features

- **Three User Roles:**
    - **Admin/HOD Portal:** Full control over the system.
    - **Staff Portal:** For teachers to manage their students and activities.
    - **Student Portal:** For students to track their progress and interact with the system.
- **Core Functionalities:**
    - 👤 **User Management:** Add, edit, and manage Admins, Staff, and Students.
    - 📚 **Course & Subject Management:** Easily define courses and assign subjects.
    - ✅ **Attendance Tracking:** Staff can take attendance, and both Admins and Students can view attendance records
      with a modern, interactive UI.
    - 💬 **Feedback System:** A stylish, card-based feedback loop between students/staff and the administration.
    - ✈️ **Leave Management:** A streamlined process for staff and students to apply for leave and for admins to
      approve/reject requests.
    - 👤 **Profile Management:** Users can update their personal information, including profile pictures and passwords,
      via a clean, two-column interface.

---

## 📸 Screenshots

*It's highly recommended to add screenshots of your application here to showcase the UI.*

|     Admin Dashboard      |      Staff Feedback      |
|:------------------------:|:------------------------:|
| *(Your Screenshot Here)* | *(Your Screenshot Here)* |
|   **View Attendance**    |    **Staff Profile**     |
| *(Your Screenshot Here)* | *(Your Screenshot Here)* |

---

## 🛠️ Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript, jQuery
- **UI Framework:** [AdminLTE v4](https://adminlte.io/) (based on Bootstrap 5)
- **Icons:** [Bootstrap Icons](https://icons.getbootstrap.com/) & [Font Awesome](https://fontawesome.com/)
- **Database:** MySQL (configurable)

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing
purposes.

### Prerequisites

Make sure you have the following installed on your system:

- [Python](https://www.python.org/downloads/) (version 3.10 or higher)
- `pip` (Python package installer)
- Git

### Installation

1. **Clone the repository:**
   *(Replace `your-username/your-repo-name` with your actual GitHub details)*
   ```sh
   git clone git@github.com:fahim06/student_management_system.git
   cd student_management_system
   ```

2. **Create and activate a virtual environment:**
   This keeps your project dependencies isolated.

    - **On Windows:**
      ```sh
      python -m venv venv
      venv\Scripts\activate
      ```

    - **On macOS/Linux:**
      ```sh
      python3 -m venv venv
      source venv/bin/activate
      ```

3. **Install dependencies:**
   This project uses a `requirements.txt` file to manage its Python packages. Run the following command to install them:
   ```sh
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   This will create the necessary database tables.
   ```sh
   python manage.py migrate
   ```

5. **Create a superuser:**
   This account will have full administrative privileges.
   ```sh
   python manage.py createsuperuser
   ```
   Follow the prompts to create your username and password.

6. **Run the development server:**
   ```sh
   python manage.py runserver
   ```

7. **Access the application:**
   Open your web browser and navigate to `http://127.0.0.1:8000/`. You can log in with the superuser credentials you
   just created.

---

## 📖 Usage

1. **Log in** as the admin user.
2. From the admin dashboard, you can:
    - Add **Courses** (e.g., "Computer Science", "Business Administration").
    - Add **Subjects** and assign them to courses.
    - Add **Staff** members and assign them to subjects.
    - Add **Students** and enroll them in courses and sessions.
3. Log out and log in as a **Staff** or **Student** user to see their respective dashboards and functionalities.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any
contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 Contact

Fahim - fahim.yusuf06@gmail.com

Project Link: https://github.com/fahim06/student_management_system