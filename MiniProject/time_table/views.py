from django.shortcuts import render, redirect
from .models import Department, Teacher, Course, Room, TimetableSlot
from django.views.decorators.csrf import csrf_exempt
import random
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
from django.http import HttpResponse
import io
from django.contrib import messages


def home(request):
    return render(request, 'home.html')

# @csrf_exempt



# views.py
from django.shortcuts import render
from .models import TimetableSlot, Department, Course

# views.py
from django.shortcuts import render
from .models import TimetableSlot, Department


def view_timetable(request):
    department_id = request.GET.get('department')
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '1:00-2:00', '2:00-3:00']

    context = {
        'departments': Department.objects.all(),
        'days': days,
        'time_slots': time_slots,
    }

    if department_id:
        try:
            selected_dept = Department.objects.get(id=department_id)
            slots = TimetableSlot.objects.filter(department=selected_dept).select_related('course', 'course__teacher',
                                                                                          'room')

            # Create a dictionary for easier template access
            timetable_data = {}
            for day in days:
                timetable_data[day] = {}
                for time in time_slots:
                    slot = next((s for s in slots if s.day == day and s.time_slot == time), None)
                    timetable_data[day][time] = slot

            context.update({
                'selected_dept': selected_dept,
                'timetable_data': timetable_data,
                'slots': slots
            })

        except Department.DoesNotExist:
            context.update({'error': 'Department not found.'})
    else:
        context.update({'error': 'No department selected.'})

    return render(request, 'view_timetable.html', context)

@csrf_exempt
def edit_timetable(request):
    departments = Department.objects.all()
    selected_dept_id = request.GET.get("department") or request.POST.get("department")
    selected_dept = Department.objects.filter(id=selected_dept_id).first() if selected_dept_id else None
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '1:00-2:00', '2:00-3:00']

    if request.method == 'POST' and selected_dept:
        # First pass: check for conflicts and count lectures per teacher
        teacher_lecture_counts = defaultdict(int)
        has_conflict = False

        # Count existing lectures for each teacher in this department
        existing_slots = TimetableSlot.objects.filter(department=selected_dept).select_related('course__teacher')
        for slot in existing_slots:
            if slot.course:
                teacher_lecture_counts[slot.course.teacher.id] += 1

        # Process new assignments
        for day in days:
            for time in time_slots:
                course_id = request.POST.get(f"{day}_{time}_course")
                room_id = request.POST.get(f"{day}_{time}_room")

                if course_id:
                    selected_course = Course.objects.select_related('teacher').filter(id=course_id).first()
                    if selected_course:
                        teacher = selected_course.teacher

                        # Check teacher max lectures
                        if teacher_lecture_counts[teacher.id] >= teacher.max_lectures:
                            messages.error(request,
                                           f"⚠️ Teacher {teacher.name} has reached max lectures ({teacher.max_lectures})")
                            has_conflict = True
                            continue

                        teacher_lecture_counts[teacher.id] += 1

                        # Check teacher time conflicts
                        teacher_conflict = TimetableSlot.objects.filter(
                            day=day, time_slot=time, course__teacher=teacher
                        ).exclude(department=selected_dept).exists()

                        if teacher_conflict:
                            messages.error(request,
                                           f"⚠️ Conflict: Teacher {teacher.name} is already assigned on {day} at {time}.")
                            has_conflict = True

                if room_id:
                    room_conflict = TimetableSlot.objects.filter(
                        day=day, time_slot=time, room_id=room_id
                    ).exclude(department=selected_dept).exists()

                    if room_conflict:
                        room_obj = Room.objects.get(id=room_id)
                        messages.error(request,
                                       f"⚠️ Conflict: Room {room_obj.number} is already in use on {day} at {time}.")
                        has_conflict = True

        # Only save if no conflicts
        if not has_conflict:
            # Clear existing slots for this department
            TimetableSlot.objects.filter(department=selected_dept).delete()

            # Create new slots
            for day in days:
                for time in time_slots:
                    course_id = request.POST.get(f"{day}_{time}_course")
                    room_id = request.POST.get(f"{day}_{time}_room")

                    if course_id or room_id:
                        TimetableSlot.objects.create(
                            day=day,
                            time_slot=time,
                            department=selected_dept,
                            course_id=course_id or None,
                            room_id=room_id or None
                        )
            messages.success(request, "✅ Timetable saved successfully!")

    # Prepare context for rendering
    courses = Course.objects.select_related('teacher').all()
    rooms = Room.objects.filter(department=selected_dept) if selected_dept else []
    slots = TimetableSlot.objects.filter(department=selected_dept).select_related('course',
                                                                                  'room') if selected_dept else []

    slots_dict = {day: {time: next((s for s in slots if s.day == day and s.time_slot == time), None)
                        for time in time_slots} for day in days}

    return render(request, 'edit_timetable.html', {
        'departments': departments,
        'selected_dept': selected_dept,
        'days': days,
        'time_slots': time_slots,
        'courses': courses,
        'rooms': rooms,
        'slots_dict': slots_dict
    })
def generate_timetable_image(request, dept_id):
    department = Department.objects.get(id=dept_id)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '1:00-2:00', '2:00-3:00']
    slots = TimetableSlot.objects.filter(department=department).select_related('course', 'course__teacher', 'room')

    img_width, img_height = 1000, 600
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    cell_width = img_width // (len(days) + 1)
    cell_height = img_height // (len(time_slots) + 1)

    for i, day in enumerate([''] + days):
        draw.text((i * cell_width + 10, 5), day, fill='black', font=font)

    for j, time in enumerate(time_slots):
        draw.text((5, (j + 1) * cell_height + 10), time, fill='black', font=font)

    for i, day in enumerate(days):
        for j, time in enumerate(time_slots):
            slot = next((s for s in slots if s.day == day and s.time_slot == time), None)
            if slot:
                text = f"{slot.course.name}\n{slot.course.teacher.name}\nRoom: {slot.room.number if slot.room else 'N/A'}"
            else:
                text = ""
            draw.text(((i + 1) * cell_width + 5, (j + 1) * cell_height + 5), text, fill='black', font=font)

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{department.name}_timetable.png"'
    return response


def add_teacher(request):
    departments = Department.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        department_id = request.POST.get('department')
        max_lectures = request.POST.get('max_lectures')

        department = Department.objects.get(id=department_id)
        Teacher.objects.create(name=name, department=department, max_lectures=max_lectures)

        # ✅ Instead of redirecting, clear the form and re-render
        return render(request, 'add_teacher.html', {
            'departments': departments,
            'success_message': 'Teacher added successfully!'
        })

    return render(request, 'add_teacher.html', {'departments': departments})


def add_room(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        number = request.POST.get('number')
        dept_id = request.POST.get('department')
        department = Department.objects.get(id=dept_id)
        Room.objects.create(number=number, department=department)
        # No redirect to home
    return render(request, 'add_room.html', {'departments': departments})

def add_department(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Department.objects.create(name=name)
        # No redirect; stay on the same page
    return render(request, 'add_department.html')

from .models import Course, Teacher

def add_course(request):
    teachers = Teacher.objects.select_related('department').all()
    if request.method == 'POST':
        name = request.POST.get('name')
        teacher_id = request.POST.get('teacher')
        teacher = Teacher.objects.get(id=teacher_id)
        Course.objects.create(name=name, teacher=teacher)
        # No redirect, stay on the same page
    return render(request, 'add_course.html', {'teachers': teachers})


@csrf_exempt
def auto_allocate_lectures(request):
    departments = Department.objects.all()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '1:00-2:00', '2:00-3:00']

    for dept in departments:
        courses = list(Course.objects.filter(teacher__department=dept).select_related('teacher'))
        rooms = list(Room.objects.filter(department=dept))
        teacher_lecture_count = defaultdict(int)

        # Shuffle all day/time combinations
        all_slots = [(day, time) for day in days for time in time_slots]
        random.shuffle(all_slots)

        for day, time in all_slots:
            random.shuffle(courses)
            for course in courses:
                teacher = course.teacher
                if teacher_lecture_count[teacher.id] < teacher.max_lectures:
                    room = random.choice(rooms) if rooms else None
                    TimetableSlot.objects.update_or_create(
                        department=dept, day=day, time_slot=time,
                        defaults={'course': course, 'room': room}
                    )
                    teacher_lecture_count[teacher.id] += 1
                    break  # go to next slot after assigning

    return redirect('edit_timetable')


def generate_timetable_image(request, dept_id):
    department = Department.objects.get(id=dept_id)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '1:00-2:00', '2:00-3:00']
    slots = TimetableSlot.objects.filter(department=department).select_related('course', 'course__teacher', 'room')

    # Create an image
    img_width, img_height = 1000, 600
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    cell_width = img_width // (len(days) + 1)
    cell_height = img_height // (len(time_slots) + 1)

    # Draw table headers
    for i, day in enumerate(['Time/Day'] + days):
        draw.text((i * cell_width + 5, 5), day, fill='black', font=font)

    for j, time in enumerate(time_slots):
        draw.text((5, (j + 1) * cell_height + 5), time, fill='black', font=font)
        for i, day in enumerate(days):
            slot = next((s for s in slots if s.day == day and s.time_slot == time), None)
            if slot and slot.course:
                content = f"{slot.course.name}\n{slot.course.teacher.name}\nRoom: {slot.room.number}"
            else:
                content = "Free"
            draw.multiline_text((i * cell_width + cell_width + 5, (j + 1) * cell_height + 5), content, fill='black', font=font)

    # Convert to HttpResponse
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{department.name}_timetable.png"'
    return response


# views.py
from .models import Student, Attendance, TimetableSlot

def mark_attendance(request):
    students = Student.objects.all()
    departments = Department.objects.all()
    slots = TimetableSlot.objects.all().order_by('day', 'time_slot')

    if request.method == 'POST':
        for student in students:
            for slot in slots:
                key = f"attend_{student.id}_{slot.id}"
                status = request.POST.get(key)
                Attendance.objects.update_or_create(
                    student=student, slot=slot,
                    defaults={'is_present': status == 'present'}
                )
        return render(request, 'mark_attendance.html', {
            'students': students,
            'slots': slots,
            'success': "✅ Attendance updated!",
            'departments': departments
        })

    existing_attendance = {(att.student.id, att.slot.id): att.is_present for att in Attendance.objects.all()}
    return render(request, 'mark_attendance.html', {
        'students': students,
        'slots': slots,
        'existing_attendance': existing_attendance,
        'departments': departments
    })
