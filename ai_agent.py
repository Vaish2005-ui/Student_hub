import re
from database import get_db_connection

class StudentHubAIAgent:
    """
    StudentHub AI Agent
    An intelligent academic advisor and data analyst agent that analyzes student database
    records, answers natural language questions, and generates real-time actionable insights.
    """

    def __init__(self):
        pass

    def get_dashboard_insights(self):
        """
        Generates real-time AI insights based on live SQLite database metrics.
        """
        connection = get_db_connection()
        cursor = connection.cursor()

        # Gather dataset metrics
        cursor.execute("SELECT COUNT(*) AS total FROM students")
        total_students = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS active FROM students WHERE status = 'Active'")
        active_students = cursor.fetchone()["active"]

        cursor.execute("SELECT COUNT(*) AS inactive FROM students WHERE status = 'Inactive'")
        inactive_students = cursor.fetchone()["inactive"]

        cursor.execute("SELECT COUNT(*) AS total_courses FROM courses")
        total_courses = cursor.fetchone()["total_courses"]

        cursor.execute("""
            SELECT courses.name, COUNT(students.id) AS count
            FROM courses
            LEFT JOIN students ON courses.id = students.course_id
            GROUP BY courses.id, courses.name
            ORDER BY count DESC
        """)
        course_counts = cursor.fetchall()

        connection.close()

        insights = []

        if total_students == 0:
            insights.append({
                "type": "warning",
                "title": "Database Initialization",
                "icon": "⚡",
                "text": "The student database is currently empty. Add initial student enrollments to unlock full AI predictive analytics."
            })
            return insights

        # Retention & Status Analysis
        active_pct = (active_students / total_students * 100) if total_students > 0 else 0
        if active_pct >= 80:
            insights.append({
                "type": "success",
                "title": "High Student Engagement",
                "icon": "✨",
                "text": f"Healthy active enrollment rate of <strong>{active_pct:.1f}%</strong> ({active_students} out of {total_students} students active)."
            })
        elif inactive_students > 0:
            insights.append({
                "type": "warning",
                "title": "Action Required: Inactive Follow-ups",
                "icon": "⚠️",
                "text": f"<strong>{inactive_students} student(s)</strong> are currently marked as Inactive. Consider scheduling academic check-ins."
            })

        # Course Popularity & Balance Insight
        if course_counts:
            top_course = course_counts[0]
            insights.append({
                "type": "info",
                "title": "Top Academic Program",
                "icon": "🎯",
                "text": f"<strong>{top_course['name']}</strong> leads in enrollment with <strong>{top_course['count']}</strong> student(s)."
            })

            # Check for empty courses
            empty_courses = [c['name'] for c in course_counts if c['count'] == 0]
            if empty_courses:
                insights.append({
                    "type": "warning",
                    "title": "Course Allocation Notice",
                    "icon": "💡",
                    "text": f"The following course(s) have 0 active enrollments: <strong>{', '.join(empty_courses)}</strong>."
                })

        # Smart Recommendation
        insights.append({
            "type": "primary",
            "title": "AI Recommendation",
            "icon": "🤖",
            "text": f"Automated audit complete. All {total_students} student records mapped across {total_courses} programs."
        })

        return insights

    def process_query(self, query):
        """
        Processes natural language user questions and queries the SQLite database.
        Returns a dict with 'reply' (markdown text) and 'suggestions' (suggested follow-ups).
        """
        if not query or not query.strip():
            return {
                "reply": "Hello! I am your **StudentHub AI Agent**. How can I assist you with student records, course analytics, or enrollment trends today?",
                "suggestions": [
                    "How many students are enrolled?",
                    "Show inactive students",
                    "Which course is most popular?",
                    "Summarize database status"
                ]
            }

        q = query.lower().strip()
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            # 1. TOTAL / COUNT INQUIRIES
            if re.search(r'\b(how many|count|total|number of)\b.*\b(student|enrolled|registered)\b', q):
                cursor.execute("SELECT COUNT(*) AS total FROM students")
                total = cursor.fetchone()["total"]
                cursor.execute("SELECT COUNT(*) AS active FROM students WHERE status = 'Active'")
                active = cursor.fetchone()["active"]
                cursor.execute("SELECT COUNT(*) AS inactive FROM students WHERE status = 'Inactive'")
                inactive = cursor.fetchone()["inactive"]

                reply = (
                    f"### 📊 Student Enrollment Overview\n\n"
                    f"- **Total Students:** {total}\n"
                    f"- **Active Students:** {active} ({active / total * 100:.1f}%)\n" if total > 0 else f"- **Total Students:** 0\n"
                )
                if total > 0:
                    reply += f"- **Inactive Students:** {inactive}\n\nYou can view full details in the [Students Directory](/students)."

                return {
                    "reply": reply,
                    "suggestions": [
                        "Show course breakdown",
                        "Show inactive students",
                        "Who was recently added?"
                    ]
                }

            # 2. INACTIVE / AT-RISK STUDENTS
            if re.search(r'\b(inactive|at risk|dropped|graduated|status)\b', q):
                cursor.execute("""
                    SELECT students.id, students.name, students.email, courses.name AS course
                    FROM students
                    INNER JOIN courses ON students.course_id = courses.id
                    WHERE students.status = 'Inactive'
                    ORDER BY students.name ASC
                """)
                inactive_list = cursor.fetchall()

                if not inactive_list:
                    reply = "🎉 **Great news!** All currently registered students are active in their respective courses."
                else:
                    reply = f"### ⚠️ Inactive Students ({len(inactive_list)})\n\nHere are the students currently set as **Inactive**:\n\n"
                    for s in inactive_list:
                        reply += f"- **[{s['name']}](/student/{s['id']})** — {s['course']} (`{s['email']}`)\n"
                    reply += "\n*Click any student's name to view their full profile or update their status.*"

                return {
                    "reply": reply,
                    "suggestions": [
                        "View all active students",
                        "Show recent enrollments",
                        "What is the total student count?"
                    ]
                }

            # 3. RECENT ENROLLMENTS / LATEST
            if re.search(r'\b(recent|latest|new|newest|last)\b', q):
                cursor.execute("""
                    SELECT students.id, students.name, students.email, students.status, courses.name AS course
                    FROM students
                    INNER JOIN courses ON students.course_id = courses.id
                    ORDER BY students.id DESC
                    LIMIT 5
                """)
                recent = cursor.fetchall()

                if not recent:
                    reply = "No student records found in the system yet."
                else:
                    reply = "### 🆕 5 Most Recently Enrolled Students\n\n"
                    for s in recent:
                        status_badge = "🟢 Active" if s['status'] == 'Active' else "🔴 Inactive"
                        reply += f"1. **[{s['name']}](/student/{s['id']})** — {s['course']} ({status_badge})\n"
                    reply += "\nNeed to add a new record? Use the [+ Add Student](/student/add) form."

                return {
                    "reply": reply,
                    "suggestions": [
                        "Show course distribution",
                        "Filter by active status",
                        "Add a new student"
                    ]
                }

            # 4. COURSES & POPULARITY
            if re.search(r'\b(course|program|popular|distribution|department|subject)\b', q):
                cursor.execute("""
                    SELECT courses.name, COUNT(students.id) AS total
                    FROM courses
                    LEFT JOIN students ON courses.id = students.course_id
                    GROUP BY courses.id, courses.name
                    ORDER BY total DESC
                """)
                courses_stat = cursor.fetchall()

                reply = "### 📚 Course Enrollment Breakdown\n\n"
                for c in courses_stat:
                    reply += f"- **{c['name']}**: {c['total']} student(s)\n"
                reply += "\nExplore full course rosters on the [Courses Page](/courses)."

                return {
                    "reply": reply,
                    "suggestions": [
                        "How many total students?",
                        "Show inactive students",
                        "Who are the newest students?"
                    ]
                }

            # 5. SPECIFIC STUDENT SEARCH (NAME OR EMAIL)
            if re.search(r'\b(search|find|who is|lookup|detail|information on|about)\b', q):
                # Extract potential search terms
                search_term = re.sub(r'^(search|find|who is|lookup|detail|information on|about|for|\s)+', '', q, flags=re.I).strip()
                if search_term:
                    cursor.execute("""
                        SELECT students.id, students.name, students.email, students.phone, students.status, courses.name AS course
                        FROM students
                        INNER JOIN courses ON students.course_id = courses.id
                        WHERE students.name LIKE ? OR students.email LIKE ? OR courses.name LIKE ?
                        LIMIT 5
                    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                    matches = cursor.fetchall()

                    if matches:
                        reply = f"### 🔍 Search Results for \"{search_term}\"\n\nFound **{len(matches)}** matching record(s):\n\n"
                        for s in matches:
                            reply += f"- **[{s['name']}](/student/{s['id']})** | {s['course']} | Status: `{s['status']}` | Email: `{s['email']}`\n"
                        return {
                            "reply": reply,
                            "suggestions": ["Show all students", "Search another student", "View dashboard"]
                        }

            # 6. DEFAULT GENERAL / AI ASSISTANT SUMMARY
            cursor.execute("SELECT COUNT(*) AS total FROM students")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS active FROM students WHERE status = 'Active'")
            active = cursor.fetchone()["active"]

            cursor.execute("SELECT COUNT(*) AS courses FROM courses")
            c_count = cursor.fetchone()["courses"]

            reply = (
                f"### 🤖 StudentHub AI Agent Response\n\n"
                f"I processed your query: *\"{query}\"*\n\n"
                f"**Current System Summary:**\n"
                f"- 👥 **{total}** Registered Students ({active} Active)\n"
                f"- 📖 **{c_count}** Academic Programs\n\n"
                f"You can ask me questions like:\n"
                f"- *\"How many students are enrolled?\"*\n"
                f"- *\"List all inactive students\"*\n"
                f"- *\"Which is the most popular course?\"*\n"
                f"- *\"Show recent enrollments\"*"
            )

            return {
                "reply": reply,
                "suggestions": [
                    "How many students are enrolled?",
                    "Show inactive students",
                    "Which course is most popular?",
                    "Show recent enrollments"
                ]
            }

        finally:
            connection.close()


# Singleton Agent instance
ai_agent = StudentHubAIAgent()
