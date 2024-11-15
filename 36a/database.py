import sqlite3
from datetime import datetime
 
class AttendanceDB:
    def __init__(self):
      self.conn = sqlite3.connect('attendance.db')
      self.create_tables()
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            class_id TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            class_id TEXT,
            date TEXT,
            time TEXT,
            confidence REAL,
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
        ''')
        self.conn.commit()
    def mark_attendance(self, student_id, class_id, confidence):
       # Kiểm tra xem sinh viên đã điểm danh trong ngày chưa
       cursor = self.conn.cursor()
       today = datetime.now().strftime("%Y-%m-%d")
       cursor.execute('''
       SELECT COUNT(*) FROM attendance 
       WHERE student_id=? AND class_id=? AND date=?
       ''', (student_id, class_id, today))
       if cursor.fetchone()[0] == 0:
           now = datetime.now()
           cursor.execute('''
           INSERT INTO attendance (student_id, class_id, date, time, confidence)
           VALUES (?, ?, ?, ?, ?)
           ''', (student_id, class_id, today, now.strftime("%H:%M:%S"), confidence))
           self.conn.commit()
           return True
       return False
 
    def get_student_name(self, student_id):
       cursor = self.conn.cursor()
       cursor.execute('SELECT name FROM students WHERE student_id=?', (student_id,))
       result = cursor.fetchone()
       return result[0] if result else "Unknown"
    def get_attendance_report(self, class_id, date):
       cursor = self.conn.cursor()
       cursor.execute('''
       SELECT s.student_id, s.name, a.time, a.confidence
       FROM students s
       LEFT JOIN attendance a ON s.student_id = a.student_id
       WHERE a.class_id = ? AND a.date = ?
       ORDER BY a.time
       ''', (class_id, date))
       return cursor.fetchall()
 
atb = AttendanceDB()