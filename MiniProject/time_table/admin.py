from django.contrib import admin
from .models import *

admin.site.register(Department)
admin.site.register(Teacher)
admin.site.register(Course)
admin.site.register(Room)
admin.site.register(TimetableSlot)
admin.site.register(Student)
admin.site.register(Attendance)
