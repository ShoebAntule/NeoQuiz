from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from quiz import models as QMODEL
from teacher import models as TMODEL


#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'student/studentclick.html')

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import render, redirect

def student_signup_view(request):
    userForm = forms.StudentUserForm()
    studentForm = forms.StudentForm()
    mydict = {'userForm': userForm, 'studentForm': studentForm}
    if request.method == 'POST':
        userForm = forms.StudentUserForm(request.POST)
        studentForm = forms.StudentForm(request.POST, request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            email = userForm.cleaned_data.get('email')
            if not email.endswith('@eng.rizvi.edu.in'):
                messages.error(request, "Email must end with @eng.rizvi.edu.in")
                return render(request, 'student/studentsignup.html', context=mydict)
            user = userForm.save(commit=False)
            user.username = email  # Set username to email for compatibility
            user.set_password(user.password)
            user.save()
            student = studentForm.save(commit=False)
            student.user = user
            student.save()
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
            return redirect('studentlogin')
    return render(request, 'student/studentsignup.html', context=mydict)

from django.views import View

class StudentLoginView(View):
    form_class = forms.StudentLoginForm
    template_name = 'student/studentlogin.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            if not email.endswith('@eng.rizvi.edu.in'):
                messages.error(request, "Email must end with @eng.rizvi.edu.in")
                return render(request, self.template_name, {'form': form})
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('student-dashboard')
            else:
                messages.error(request, "Invalid email or password")
        return render(request, self.template_name, {'form': form})

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    student = models.Student.objects.get(user=request.user)
    # Get teachers who blocked this student
    blocking_teachers = TMODEL.Teacher.objects.filter(blocked_students=student)
    # Get User ids of blocking teachers
    blocking_teacher_user_ids = blocking_teachers.values_list('user', flat=True)
    # Get courses taught by blocking teachers (User objects)
    blocked_courses = QMODEL.Course.objects.filter(teacher__in=blocking_teacher_user_ids)
    blocked_course_ids = set(blocked_courses.values_list('id', flat=True))
    # Get recent quiz excluding blocked courses
    recent_quiz = QMODEL.Course.objects.exclude(id__in=blocked_course_ids).order_by('-id').first()
    last_attempted_result = QMODEL.Result.objects.filter(student=student).order_by('-id').first()
    dict={
        'total_course':QMODEL.Course.objects.all().count(),
        'total_question':QMODEL.Question.objects.all().count(),
        'recent_quiz': recent_quiz,
        'last_attempted_result': last_attempted_result,
        'blocked_course_ids': blocked_course_ids,
    }
    return render(request,'student/student_dashboard.html',context=dict)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    student = models.Student.objects.get(user=request.user)
    # Get teachers who blocked this student
    blocking_teachers = TMODEL.Teacher.objects.filter(blocked_students=student)
    # Get User ids of blocking teachers
    blocking_teacher_user_ids = blocking_teachers.values_list('user', flat=True)
    # Get courses taught by blocking teachers (User objects)
    blocked_courses = QMODEL.Course.objects.filter(teacher__in=blocking_teacher_user_ids)
    # Get all courses excluding blocked courses
    courses = QMODEL.Course.objects.exclude(id__in=blocked_courses.values_list('id', flat=True))
    # Pass blocked course ids to template for frontend logic
    blocked_course_ids = set(blocked_courses.values_list('id', flat=True))
    return render(request, 'student/student_exam.html', {'courses': courses, 'blocked_course_ids': blocked_course_ids})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    total_questions=QMODEL.Question.objects.all().filter(course=course).count()
    questions=QMODEL.Question.objects.all().filter(course=course)
    total_marks=0
    for q in questions:
        total_marks=total_marks + q.marks
    
    return render(request,'student/take_exam.html',{'course':course,'total_questions':total_questions,'total_marks':total_marks})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def start_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    questions=QMODEL.Question.objects.all().filter(course=course)
    if request.method=='POST':
        pass
    response= render(request,'student/start_exam.html',{'course':course,'questions':questions})
    response.set_cookie('course_id',course.id)
    return response


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def calculate_marks_view(request):
    if request.COOKIES.get('course_id') is not None:
        course_id = request.COOKIES.get('course_id')
        course=QMODEL.Course.objects.get(id=course_id)
        
        total_marks=0
        questions=QMODEL.Question.objects.all().filter(course=course)
        detailed_results = []
        selected_answers = []
        for i in range(len(questions)):
            # Read selected answer from POST data instead of cookies
            selected_ans = request.POST.get(str(i+1))
            selected_answers.append(selected_ans)
            actual_answer = questions[i].answer
            # Directly compare selected_ans with actual_answer (both are like "Option1")
            if selected_ans == actual_answer:
                total_marks = total_marks + questions[i].marks
            
            # Prepare detailed result for each question
            options_dict = {
                "A": questions[i].option1,
                "B": questions[i].option2,
                "C": questions[i].option3,
                "D": questions[i].option4,
            }
            # Map actual_answer like "Option1" to "A" for display
            answer_key_map = {
                "Option1": "A",
                "Option2": "B",
                "Option3": "C",
                "Option4": "D",
            }
            correct_option_key = answer_key_map.get(actual_answer, '')
            # Map selected answer value like "Option1" to key like "A" for display
            selected_option_key_map = {
                "Option1": "A",
                "Option2": "B",
                "Option3": "C",
                "Option4": "D",
            }
            selected_option_key = selected_option_key_map.get(selected_ans, '')
            detailed_results.append({
                "question": questions[i].question,
                "options": options_dict,
                "selectedOption": selected_option_key,
                "correctOption": correct_option_key,
            })
        student = models.Student.objects.get(user_id=request.user.id)
        result = QMODEL.Result()
        result.marks=total_marks
        result.exam=course
        result.student=student
        result.save()

        # Save each selected answer in StudentAnswer model
        for i in range(len(questions)):
            selected_ans = selected_answers[i]
            student_answer = QMODEL.StudentAnswer(
                result=result,
                question=questions[i],
                selected_option=selected_ans if selected_ans else ''
            )
            student_answer.save()

        # Pass detailed results and score to the template
        import logging
        logger = logging.getLogger(__name__)
        # Map answer values like "Option1" to keys like "A" for options_dict
        option_key_map = {
            "Option1": "A",
            "Option2": "B",
            "Option3": "C",
            "Option4": "D",
        }
        # Add correct answer text directly to each detailed result to avoid template filter
        for item in detailed_results:
            correct_option_value = item['correctOption']  # e.g. "Option1"
            mapped_key = option_key_map.get(correct_option_value, '')
            correct_answer_text = item['options'].get(mapped_key, '')
            item['correctAnswerText'] = correct_answer_text
            logger.debug(f"Question: {item['question']}, Correct Option: {correct_option_value}, Mapped Key: {mapped_key}, Correct Answer Text: {correct_answer_text}")

        total_marks_possible = 0
        for q in questions:
            total_marks_possible += q.marks

        context = {
            "score": total_marks,
            "total": total_marks_possible,
            "detailedResults": detailed_results,
        }
        return render(request, 'student/quiz_result.html', context)



@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/view_result.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def quiz_result_view(request):
    # This view can be removed or kept for testing purposes
    return render(request, 'student/quiz_result.html')
    

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results= QMODEL.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'student/check_marks.html',{'results':results})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_marks.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def quiz_history_view(request, pk):
    # pk is course id
    course = QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    
    # Fetch all results for this student and course
    results = QMODEL.Result.objects.filter(exam=course, student=student)
    
    # For each result, fetch detailed question and answer info including student's selected answers
    quiz_histories = []
    for result in results:
        questions = QMODEL.Question.objects.filter(course=course)
        # Fetch student's selected answers for this result
        student_answers = QMODEL.StudentAnswer.objects.filter(result=result)
        # Map question id to selected_option for quick lookup
        answer_map = {sa.question.id: sa.selected_option for sa in student_answers}
        
        detailed_results = []
        for q in questions:
            options_dict = {
                "A": q.option1,
                "B": q.option2,
                "C": q.option3,
                "D": q.option4,
            }
            answer_key_map = {
                "Option1": "A",
                "Option2": "B",
                "Option3": "C",
                "Option4": "D",
            }
            correct_option_key = answer_key_map.get(q.answer, '')
            selected_option_value = answer_map.get(q.id, '')
            # Map selected_option_value like 'Option1' to 'A'
            selected_option_key = ''
            if selected_option_value == 'Option1':
                selected_option_key = 'A'
            elif selected_option_value == 'Option2':
                selected_option_key = 'B'
            elif selected_option_value == 'Option3':
                selected_option_key = 'C'
            elif selected_option_value == 'Option4':
                selected_option_key = 'D'
            detailed_results.append({
                "question": q.question,
                "options": options_dict,
                "correctOption": correct_option_key,
                "selectedOption": selected_option_key,
            })
        quiz_histories.append({
            "result": result,
            "detailedResults": detailed_results,
        })
    
    context = {
        "course": course,
        "quiz_histories": quiz_histories,
    }
    return render(request, 'student/quiz_history.html', context)
  