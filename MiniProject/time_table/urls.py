from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),  # root path of 'home/'
    path('timetable/', edit_timetable, name='timetable'),
    path('edit/', edit_timetable, name='edit_timetable'),
    path('timetable/', edit_timetable, name='timetable'),
    path('timetable_image/<int:dept_id>/', generate_timetable_image, name='generate_timetable_image'),
    path('attendance/', mark_attendance, name='mark_attendance'),
    path('view/', view_timetable, name='view_timetable'),
    path('add_teacher/', add_teacher, name='add_teacher'),
    path('add_room/', add_room, name='add_room'),
    path('add_department/', add_department, name='add_department'),
    path('add-course/', add_course, name='add_course'),
    path('auto-allocate/', auto_allocate_lectures, name='auto_allocate'),
    path('generate_timetable_image/<int:dept_id>/', generate_timetable_image, name='generate_timetable_image'),

]
