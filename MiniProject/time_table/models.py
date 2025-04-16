# models.py
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Teacher(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    max_lectures = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Room(models.Model):
    number = models.CharField(max_length=10)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.number

class TimetableSlot(models.Model):
    day = models.CharField(max_length=10)
    time_slot = models.CharField(max_length=20)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.day} {self.time_slot} - {self.department.name}"

# models.py
class Student(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    slot = models.ForeignKey(TimetableSlot, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.name} - {self.slot} - {'Present' if self.is_present else 'Absent'}"
