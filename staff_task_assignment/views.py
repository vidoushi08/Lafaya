from django.shortcuts import render


def index(request):
    return render(request, "staff_task_assignment/task_assignment.html")
