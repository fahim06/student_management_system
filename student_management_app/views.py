from django.shortcuts import render


# Create your views here.
def ShowDemoPage(request):
    return render(request, 'demo.html')
