from django.shortcuts import render,HttpResponse


# Create your views here.
def home(request):
	#return HttpResponse('Home page!')
	numbers=[1,2,3,4,5]
	name="Pranav Chaturvedi"
	args={'myName':name,'myNumbers':numbers}
	return render(request,'accounts/home.html',args)