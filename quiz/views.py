from django.shortcuts import render, redirect, reverse
from django.db.models import Sum, Q
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.core.mail import send_mail
from . import forms, models
from teacher import models as TMODEL
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM

import requests

def generate_ai_question(topic, course):
    """Generate questions using Flask API"""
    try:
        response = requests.get(f'http://localhost:5500/get_mcqs/{topic}')
        if response.status_code == 200:
            data = response.json()
            return "\n".join(data['questions'])
        return f"Error: API returned status {response.status_code}"
    except Exception as e:
        return f"Error connecting to API: {str(e)}"
from teacher import models as TMODEL
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM
from django.contrib.auth.models import User



def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request,'quiz/index.html')


def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

def afterlogin_view(request):
    if is_student(request.user):      
        return redirect('student/student-dashboard')
                
    elif is_teacher(request.user):
        accountapproval=TMODEL.Teacher.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('teacher/teacher-dashboard')
        else:
            return render(request,'teacher/teacher_wait_for_approval.html')
    else:
        return redirect('admin-dashboard')



def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    'total_teacher':TMODEL.Teacher.objects.all().filter(status=True).count(),
    'total_course':models.Course.objects.all().count(),
    'total_question':models.Question.objects.all().count(),
    }
    return render(request,'quiz/admin_dashboard.html',context=dict)

@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    dict={
    'total_teacher':TMODEL.Teacher.objects.all().filter(status=True).count(),
    'pending_teacher':TMODEL.Teacher.objects.all().filter(status=False).count(),
    'subjects':TMODEL.Teacher.objects.all().filter(status=True).values_list('subject', flat=True).distinct().count(),
    }
    return render(request,'quiz/admin_teacher.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=True)
    return render(request,'quiz/admin_view_teacher.html',{'teachers':teachers})


@login_required(login_url='adminlogin')
def update_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=TMODEL.User.objects.get(id=teacher.user_id)
    userForm=TFORM.TeacherUserForm(instance=user)
    teacherForm=TFORM.TeacherForm(instance=teacher)
    mydict={'userForm':userForm,'teacherForm':teacherForm}
    if request.method=='POST':
        userForm=TFORM.TeacherUserForm(request.POST,instance=user)
        teacherForm=TFORM.TeacherForm(request.POST,request.FILES,instance=teacher)
        if userForm.is_valid() and teacherForm.is_valid():
            user=userForm.save(commit=False)
            user.set_password(user.password)
            user.save()
            teacherForm.save()
            return redirect('admin-view-teacher')
    return render(request,'quiz/update_teacher.html',context=mydict)



@login_required(login_url='adminlogin')
def delete_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-teacher')




@login_required(login_url='adminlogin')
def admin_view_pending_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=False)
    return render(request,'quiz/admin_view_pending_teacher.html',{'teachers':teachers})


@login_required(login_url='adminlogin')
def approve_teacher_view(request,pk):
    teacher = TMODEL.Teacher.objects.get(id=pk)
    subjects = [
        "sem 5 CSC501 Theoretical Computer Science ",
        "sem 5 CSC502 Software Engineering",
        "sem 5 CSC503 Computer Network ",
        "sem 5 CSC504 Data Warehousing & Mining",
        "sem 6 CSC602 Cryptography & System Security",
        "sem 6 CSC603 Mobile Computing",
        "sem 6 CSC604 Artificial Intelligence",
        "sem 6 CSC501 Theoretical Computer Science",
        "sem 6 CSC502 Software Engineering",
        "sem 6 CSC503 Computer Network3",
        "sem 6 CSC504 Data Warehousing & Mining"
    ]
    if request.method=='POST':
        subject = request.POST.get('subject')
        if subject:
            teacher.subject = subject
            teacher.status = True
            teacher.save()
            return HttpResponseRedirect('/admin-view-pending-teacher')
    else:
        subject = teacher.subject
    return render(request,'quiz/subject_form.html',{'teacher': teacher, 'subjects': subjects, 'selected_subject': subject})

@login_required(login_url='adminlogin')
def reject_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-pending-teacher')

# Removed the salary view as it is no longer needed




@login_required(login_url='adminlogin')
def admin_student_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    }
    return render(request,'quiz/admin_student.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'quiz/admin_view_student.html',{'students':students})



@login_required(login_url='adminlogin')
def update_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=SMODEL.User.objects.get(id=student.user_id)
    userForm=SFORM.StudentUserForm(instance=user)
    studentForm=SFORM.StudentForm(instance=student)
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=SFORM.StudentUserForm(request.POST,instance=user)
        studentForm=SFORM.StudentForm(request.POST,request.FILES,instance=student)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save(commit=False)
            user.set_password(user.password)
            user.save()
            studentForm.save()
            return redirect('admin-view-student')
    return render(request,'quiz/update_student.html',context=mydict)



@login_required(login_url='adminlogin')
def delete_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return HttpResponseRedirect('/admin-view-student')


@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request,'quiz/admin_course.html')


@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm=forms.CourseForm()
    if request.method=='POST':
        courseForm=forms.CourseForm(request.POST)
        if courseForm.is_valid():
            exam = courseForm.save(commit=False)
            exam.teacher = request.user
            exam.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-course')
    return render(request,'quiz/admin_add_course.html',{'courseForm':courseForm})


@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.Course.objects.filter(teacher=request.user, teacher__isnull=False)
    return render(request,'quiz/admin_view_course.html',{'courses':courses})

@login_required(login_url='adminlogin')
def delete_course_view(request,pk):
    course=models.Course.objects.get(id=pk)
    if course.teacher and course.teacher == request.user:
        course.delete()
    return HttpResponseRedirect('/admin-view-course')



@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request,'quiz/admin_question.html')


@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm = forms.QuestionForm()
    
    if request.method == 'POST':
        if 'generate_ai' in request.POST:
            # Handle AI question generation
            try:
                course = models.Course.objects.get(id=request.POST.get('courseID'))
                topic = request.POST.get('topic', 'general knowledge').strip()
                if not topic:
                    raise ValueError("Topic cannot be empty")
                    
                generated = generate_ai_question(topic, course.course_name)
                
                # Parse generated question with better validation
                lines = [line.strip() for line in generated.split('\n') if line.strip()]
                if len(lines) < 6:
                    raise ValueError("Invalid question format from AI")
                    
                question_data = {
                    'question': lines[0].replace('Question:', '').strip(),
                    'option1': lines[1][3:].strip() if lines[1].startswith('A)') else lines[1].strip(),
                    'option2': lines[2][3:].strip() if lines[2].startswith('B)') else lines[2].strip(),
                    'option3': lines[3][3:].strip() if lines[3].startswith('C)') else lines[3].strip(),
                    'option4': lines[4][3:].strip() if lines[4].startswith('D)') else lines[4].strip(),
                    'answer': lines[5][-1].upper() if lines[5].startswith('Answer:') else lines[5].strip().upper(),
                    'marks': 1,
                    'courseID': course.id,
                    'topic': topic
                }
                
                # Validate answer is A-D
                if question_data['answer'] not in ('A', 'B', 'C', 'D'):
                    raise ValueError("Invalid answer format from AI")
                questionForm = forms.QuestionForm(initial=question_data)
                return render(request, 'quiz/admin_add_question.html', {
                    'questionForm': questionForm,
                    'ai_generated': True
                })
            except ValueError as e:
                print(f"Validation error: {e}")
                questionForm.add_error(None, str(e))
            except Exception as e:
                print(f"AI generation failed: {e}")
                questionForm.add_error(None, f"AI generation failed: {str(e)}. Please check your API key and try again.")
        else:
            # Handle normal form submission
            questionForm = forms.QuestionForm(request.POST)
            if questionForm.is_valid():
                question = questionForm.save(commit=False)
                course = models.Course.objects.get(id=request.POST.get('courseID'))
                question.course = course
                question.save()
                return HttpResponseRedirect('/admin-view-question')
    
    return render(request, 'quiz/admin_add_question.html', {
        'questionForm': questionForm,
        'ai_generated': False
    })


@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses= models.Course.objects.all()
    return render(request,'quiz/admin_view_question.html',{'courses':courses})

@login_required(login_url='adminlogin')
def view_question_view(request,pk):
    questions=models.Question.objects.all().filter(course_id=pk)
    return render(request,'quiz/view_question.html',{'questions':questions})

@login_required(login_url='adminlogin')
def delete_question_view(request,pk):
    question=models.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/admin-view-question')

@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'quiz/admin_view_student_marks.html',{'students':students})

@login_required(login_url='adminlogin')
def admin_view_marks_view(request,pk):
    courses = models.Course.objects.all()
    response =  render(request,'quiz/admin_view_marks.html',{'courses':courses})
    response.set_cookie('student_id',str(pk))
    return response

@login_required(login_url='adminlogin')
def admin_check_marks_view(request,pk):
    course = models.Course.objects.get(id=pk)
    student_id = request.COOKIES.get('student_id')
    student= SMODEL.Student.objects.get(id=student_id)

    results= models.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'quiz/admin_check_marks.html',{'results':results})
    




def aboutus_view(request):
    return render(request,'quiz/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'quiz/contactussuccess.html')
    return render(request, 'quiz/contactus.html', {'form':sub})


