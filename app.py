from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from database import get_db_connection
from ai_agent import ai_agent

app = Flask(__name__)
app.secret_key = "studenthub-secret-key"


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/")
def dashboard():

    connection = get_db_connection()
    cursor = connection.cursor()

    # Total students
    cursor.execute("""
        SELECT COUNT(*) AS total_students
        FROM students
    """)
    total_students = cursor.fetchone()["total_students"]

    # Active students
    cursor.execute("""
        SELECT COUNT(*) AS active_students
        FROM students
        WHERE status = 'Active'
    """)
    active_students = cursor.fetchone()["active_students"]

    # Inactive students
    cursor.execute("""
        SELECT COUNT(*) AS inactive_students
        FROM students
        WHERE status = 'Inactive'
    """)
    inactive_students = cursor.fetchone()["inactive_students"]

    # Total courses
    cursor.execute("""
        SELECT COUNT(*) AS total_courses
        FROM courses
    """)
    total_courses = cursor.fetchone()["total_courses"]

    # Recent students
    cursor.execute("""
        SELECT
            students.id,
            students.name,
            courses.name AS course,
            students.status
        FROM students
        INNER JOIN courses
            ON students.course_id = courses.id
        ORDER BY students.id DESC
        LIMIT 5
    """)
    recent_students = cursor.fetchall()

    # Course-wise statistics
    cursor.execute("""
        SELECT
            courses.name AS course,
            COUNT(students.id) AS total
        FROM courses
        LEFT JOIN students
            ON courses.id = students.course_id
        GROUP BY courses.id, courses.name
        ORDER BY total DESC
    """)
    course_stats = cursor.fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        active_students=active_students,
        inactive_students=inactive_students,
        total_courses=total_courses,
        recent_students=recent_students,
        course_stats=course_stats,
        ai_insights=ai_agent.get_dashboard_insights()
    )


# ==================================================
# STUDENT LIST
# ==================================================

@app.route("/students")
def students():

    search = request.args.get(
        "search",
        ""
    ).strip()

    course_id = request.args.get(
        "course_id",
        ""
    )

    status = request.args.get(
        "status",
        ""
    )

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            students.id,
            students.name,
            students.email,
            students.phone,
            students.gender,
            students.status,
            courses.name AS course
        FROM students
        INNER JOIN courses
            ON students.course_id = courses.id
        WHERE 1 = 1
    """

    parameters = []

    # Search by name, email or phone
    if search:

        query += """
            AND (
                students.name LIKE ?
                OR students.email LIKE ?
                OR students.phone LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value,
            search_value
        ])

    # Course filter
    if course_id:

        query += """
            AND students.course_id = ?
        """

        parameters.append(course_id)

    # Status filter
    if status:

        query += """
            AND students.status = ?
        """

        parameters.append(status)

    query += """
        ORDER BY students.id DESC
    """

    cursor.execute(
        query,
        parameters
    )

    students_list = cursor.fetchall()

    # Get courses for dropdown
    cursor.execute("""
        SELECT id, name
        FROM courses
        ORDER BY name
    """)

    courses = cursor.fetchall()

    connection.close()

    return render_template(
        "students.html",
        students=students_list,
        courses=courses,
        search=search,
        selected_course=course_id,
        selected_status=status
    )


# ==================================================
# ADD STUDENT
# ==================================================

@app.route("/student/add", methods=["GET", "POST"])
def add_student():

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get courses for the form
    cursor.execute("""
        SELECT id, name
        FROM courses
        ORDER BY name
    """)

    courses = cursor.fetchall()

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        gender = request.form["gender"]
        course_id = request.form["course_id"]
        date_of_birth = request.form["date_of_birth"]
        status = request.form["status"]

        # Validation
        if not name or not email or not course_id:

            connection.close()

            flash(
                "Name, email and course are required.",
                "error"
            )

            return redirect(
                url_for("add_student")
            )

        # Insert student
        cursor.execute("""
            INSERT INTO students
            (
                name,
                email,
                phone,
                gender,
                course_id,
                date_of_birth,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            phone,
            gender,
            course_id,
            date_of_birth,
            status
        ))

        connection.commit()
        connection.close()

        flash(
            "Student added successfully.",
            "success"
        )

        return redirect(
            url_for("students")
        )

    connection.close()

    return render_template(
        "student_form.html",
        student=None,
        courses=courses,
        form_title="Add Student"
    )


# ==================================================
# STUDENT DETAILS
# ==================================================

@app.route("/student/<int:student_id>")
def student_detail(student_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            students.id,
            students.name,
            students.email,
            students.phone,
            students.gender,
            students.date_of_birth,
            students.enrollment_date,
            students.status,
            courses.name AS course
        FROM students
        INNER JOIN courses
            ON students.course_id = courses.id
        WHERE students.id = ?
    """, (student_id,))

    student = cursor.fetchone()

    connection.close()

    if student is None:

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for("students")
        )

    return render_template(
        "student_detail.html",
        student=student
    )


# ==================================================
# EDIT STUDENT
# ==================================================

@app.route("/student/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get student
    cursor.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    )

    student = cursor.fetchone()

    # Get courses
    cursor.execute(
        "SELECT id, name FROM courses ORDER BY name"
    )

    courses = cursor.fetchall()

    if student is None:

        connection.close()

        flash(
            "Student not found.",
            "error"
        )

        return redirect(
            url_for("students")
        )

    # Update student
    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        gender = request.form["gender"]
        course_id = request.form["course_id"]
        date_of_birth = request.form["date_of_birth"]
        status = request.form["status"]

        cursor.execute("""
            UPDATE students
            SET
                name = ?,
                email = ?,
                phone = ?,
                gender = ?,
                course_id = ?,
                date_of_birth = ?,
                status = ?
            WHERE id = ?
        """, (
            name,
            email,
            phone,
            gender,
            course_id,
            date_of_birth,
            status,
            student_id
        ))

        connection.commit()
        connection.close()

        flash(
            "Student updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "student_detail",
                student_id=student_id
            )
        )

    connection.close()

    return render_template(
        "student_form.html",
        student=student,
        courses=courses,
        form_title="Edit Student"
    )


# ==================================================
# DELETE STUDENT
# ==================================================

@app.route("/student/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM students
        WHERE id = ?
    """, (student_id,))

    connection.commit()
    connection.close()

    flash(
        "Student deleted successfully.",
        "success"
    )

    return redirect(
        url_for("students")
    )
# ==================================================
# COURSES OVERVIEW
# ==================================================

@app.route("/courses")
def courses():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            courses.id,
            courses.name,
            COUNT(students.id) AS total_students
        FROM courses
        LEFT JOIN students
            ON courses.id = students.course_id
        GROUP BY courses.id, courses.name
        ORDER BY courses.name ASC
    """)

    courses_data = cursor.fetchall()

    cursor.execute("""
        SELECT
            students.id,
            students.name,
            students.email,
            students.status,
            students.course_id
        FROM students
        ORDER BY students.name ASC
    """)

    students_data = cursor.fetchall()

    connection.close()

    course_students = {}
    for s in students_data:
        cid = s["course_id"]
        if cid not in course_students:
            course_students[cid] = []
        course_students[cid].append(dict(s))

    return render_template(
        "courses.html",
        courses=courses_data,
        course_students=course_students
    )


# ==================================================
# ABOUT PAGE
# ==================================================

@app.route("/about")
def about():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) AS total_students FROM students")
    total_students = cursor.fetchone()["total_students"]

    cursor.execute("SELECT COUNT(*) AS total_courses FROM courses")
    total_courses = cursor.fetchone()["total_courses"]

    connection.close()

    return render_template(
        "about.html",
        total_students=total_students,
        total_courses=total_courses
    )


# ==================================================
# STUDENTS API
# ==================================================

@app.route("/api/students")
def api_students():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            students.id,
            students.name,
            students.email,
            students.phone,
            students.gender,
            students.date_of_birth,
            students.enrollment_date,
            students.status,
            courses.name AS course
        FROM students
        INNER JOIN courses
            ON students.course_id = courses.id
        ORDER BY students.id DESC
    """)

    students = cursor.fetchall()

    connection.close()

    return jsonify([
        dict(student)
        for student in students
    ])


# ==================================================
# AI AGENT ROUTES
# ==================================================

@app.route("/api/ai/chat", methods=["POST"])
def api_ai_chat():
    """
    Endpoint for natural language chat interaction with StudentHub AI Agent.
    """
    data = request.get_json() or {}
    message = data.get("message", "")
    response = ai_agent.process_query(message)
    return jsonify(response)


@app.route("/api/ai/insights", methods=["GET"])
def api_ai_insights():
    """
    Endpoint for automated real-time database insights generated by AI Agent.
    """
    insights = ai_agent.get_dashboard_insights()
    return jsonify(insights)


@app.route("/ai-assistant")
def ai_assistant():
    """
    Dedicated AI Advisor and Assistant page.
    """
    insights = ai_agent.get_dashboard_insights()
    return render_template("ai_assistant.html", insights=insights)


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)