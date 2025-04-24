import subprocess
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect

from teacher import models
from student import models as SMODEL
from quiz import models as QMODEL
from quiz import forms as QFORM

def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

from django.contrib.auth.models import Group
from django.contrib import messages
from django.shortcuts import redirect
from . import forms

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import login

def teacher_signup_view(request):
    if request.method == 'POST':
        print("Received POST request in signup view")
        userForm = forms.TeacherUserForm(request.POST)
        teacherForm = forms.TeacherForm(request.POST, request.FILES)
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save(commit=False)
            user.set_password(user.password)
            user.save()
            teacher = teacherForm.save(commit=False)
            teacher.user = user
            teacher.status = False  # explicitly set status to False (pending approval)
            print(f"Teacher status before save: {teacher.status}")
            teacher.save()
            print(f"Teacher status after save: {teacher.status}")
            teacher_group, created = Group.objects.get_or_create(name='TEACHER')
            teacher_group.user_set.add(user)

            # Send approval request email to admin
            subject = 'New Teacher Signup Approval Needed'
            message = f'A new teacher has signed up with username: {user.username}. Please review and approve the account.'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = settings.EMAIL_RECEIVING_USER
            send_mail(subject, message, from_email, recipient_list, fail_silently=True)

            from django.contrib.auth import authenticate

            # Authenticate the user to set backend attribute
            authenticated_user = authenticate(username=user.username, password=request.POST['password'])
            if authenticated_user is not None:
                login(request, authenticated_user)
                return redirect('afterlogin')
            else:
                # Fallback: redirect to login page if authentication fails
                return redirect('teacherlogin')
        else:
            # If the forms are invalid, render the form with errors
            return render(request, 'teacher/teachersignup.html', {
                'userForm': userForm,
                'teacherForm': teacherForm
            })
    else:
        # If GET request, render empty forms
        userForm = forms.TeacherUserForm()
        teacherForm = forms.TeacherForm()
        return render(request, 'teacher/teachersignup.html', {
            'userForm': userForm,
            'teacherForm': teacherForm
        })

def teacherclick_view(request):
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'teacher/teacherclick.html')

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    return render(request, 'teacher/teacher_dashboard.html')

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def run_mcq_bot_view(request):
    try:
        # Run the streamlit app in a new console window (Windows)
        subprocess.Popen(
            ['streamlit', 'run', 'mcq_bot.py'],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        # Redirect back to teacher dashboard
        return redirect('teacher-dashboard')
    except Exception as e:
        # Optionally handle errors here, for now redirect back
        return redirect('teacher-dashboard')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    return render(request,'teacher/teacher_exam.html')

@csrf_exempt
@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def generate_mcqs(request):
    if request.method == "POST":
        topic = request.POST.get('topic', '')
        import os
        from dotenv import load_dotenv
        load_dotenv()
        client = openai.Client(
            base_url="https://models.inference.ai.azure.com",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        prompt = f"""Generate 5 multiple-choice questions about {topic} with:
        - Clear question text
        - 4 options each (labeled a-d)
        - Correct answer marked
        Format each question like:
        Q1. [question]
        a) Option 1
        b) Option 2
        c) Option 3
        d) Option 4
        Answer: [correct letter]"""

        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert MCQ generator for educational content."},
                    {"role": "user", "content": prompt},
                ],
                model="gpt-4o",
                temperature=0.7,
            )
            
            return JsonResponse({
                'mcqs': response.choices[0].message.content
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'mcqs': f"Error generating questions: {str(e)}"
            }, status=500)
            
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_exam_view(request):
    courseForm=QFORM.CourseForm()
    if request.method=='POST':
        courseForm=QFORM.CourseForm(request.POST)
        if courseForm.is_valid():
            exam = courseForm.save(commit=False)
            exam.teacher = request.user
            exam.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/teacher/teacher-view-exam')
    return render(request,'teacher/teacher_add_exam.html',{'courseForm':courseForm})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_exam_view(request):
    courses = QMODEL.Course.objects.filter(teacher=request.user)
    return render(request,'teacher/teacher_view_exam.html',{'courses':courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def delete_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    if course.teacher == request.user:
        course.delete()
    return HttpResponseRedirect('/teacher/teacher-view-exam')

@login_required(login_url='adminlogin')
def teacher_question_view(request):
    return render(request,'teacher/teacher_question.html')

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    questionForm = QFORM.QuestionForm(user=request.user)
    
    if request.method == 'POST':
        if 'generate_ai' in request.POST:
            try:
                course = QMODEL.Course.objects.get(id=request.POST.get('courseID'))
                topic = request.POST.get('topic', '').strip()
                if not topic:
                    return render(request,'teacher/teacher_add_question.html',{
                        'questionForm': questionForm,
                        'error': 'Please enter a topic for question generation'
                    })
                
                # Call the existing generate_mcqs view function
                response = generate_mcqs(request)
                if response.status_code == 200:
                    data = json.loads(response.content)
                    if 'mcqs' in data:
                        # Parse the generated questions
                        questions = data['mcqs'].split('\n\n')
                        if questions:
                            first_q = questions[0].split('\n')
                            if len(first_q) >= 6:
                                question_data = {
                                    'question': first_q[0].replace('Q1.', '').strip(),
                                    'option1': first_q[1][3:].strip(),
                                    'option2': first_q[2][3:].strip(),
                                    'option3': first_q[3][3:].strip(),
                                    'option4': first_q[4][3:].strip(),
                                    'answer': first_q[5][-1].upper(),
                                    'marks': 1,
                                    'courseID': course.id
                                }
                                questionForm = QFORM.QuestionForm(initial=question_data, user=request.user)
                                return render(request,'teacher/teacher_add_question.html',{
                                    'questionForm': questionForm,
                                    'success': 'Question generated successfully!'
                                })
                return render(request,'teacher/teacher_add_question.html',{
                    'questionForm': questionForm,
                    'error': 'Failed to generate question'
                })
            except Exception as e:
                return render(request,'teacher/teacher_add_question.html',{
                    'questionForm': questionForm,
                    'error': f'Error: {str(e)}'
                })
        else:
            questionForm = QFORM.QuestionForm(request.POST, user=request.user)
            if questionForm.is_valid():
                question = questionForm.save(commit=False)
                question.course = QMODEL.Course.objects.get(id=request.POST.get('courseID'))
                question.save()
                return HttpResponseRedirect('/teacher/teacher-view-question')
    
    return render(request,'teacher/teacher_add_question.html',{
        'questionForm': questionForm
    })

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    courses= QMODEL.Course.objects.filter(teacher=request.user)
    return render(request,'teacher/teacher_view_question.html',{'courses':courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def see_question_view(request,pk):
    try:
        course = QMODEL.Course.objects.get(id=pk)
    except QMODEL.Course.DoesNotExist:
        return HttpResponseRedirect('/teacher/teacher-view-question')
    if course.teacher != request.user:
        return HttpResponseRedirect('/teacher/teacher-view-question')
    questions=QMODEL.Question.objects.filter(course_id=pk)
    return render(request,'teacher/see_question.html',{'questions':questions})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def remove_question_view(request,pk):
    question=QMODEL.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/teacher/teacher-view-question')

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def manage_students_view(request):
    teacher = models.Teacher.objects.get(user=request.user)
    active_students = SMODEL.Student.objects.exclude(
        id__in=teacher.blocked_students.all().values_list('id', flat=True)
    )
    blocked_students = teacher.blocked_students.all()
    
    return render(request, 'teacher/manage_students.html', {
        'active_students': active_students,
        'blocked_students': blocked_students
    })

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def toggle_student_status_view(request, student_id):
    if request.method == 'POST':
        try:
            teacher = models.Teacher.objects.get(user=request.user)
            student = SMODEL.Student.objects.get(id=student_id)
            
            if student in teacher.blocked_students.all():
                teacher.blocked_students.remove(student)
                action = 'unblocked'
                message = f'Student {student.get_name} has been unblocked'
            else:
                teacher.blocked_students.add(student)
                action = 'blocked'
                message = f'Student {student.get_name} has been blocked'
                
            return JsonResponse({
                'status': 'success', 
                'action': action,
                'message': message
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def chatbot_view(request):
    return render(request, 'teacher/chatbot.html')
