from __future__ import unicode_literals
try:
    import Image
except ImportError:
    from PIL import Image
from django.shortcuts import render,redirect,get_object_or_404
from accounts.forms import (
	RegistrationForm, 
	EditProfileForm,
	DocumentForm,
)
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm,PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
import textract, re, StringIO, curses.ascii, pytesseract, glob, os, codecs,sys, subprocess
from django.http import HttpResponse
from accounts.models import Document, Clauses
from django.contrib.auth.decorators import login_required
from django.conf import settings



# Create your views here.
@login_required
def home(request):
	form = DocumentForm(request.POST or None, request.FILES or None)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.save()
		if instance.doc.url.endswith(".pdf"):
			text = pdf_extractor(instance.doc.url)
		elif instance.doc.url.endswith(".jpg"):
			text = pytesseract.image_to_string(Image.open(instance.doc.url))
		elif instance.doc.url.endswith(".docx"):
			text = textract.process(instance.doc.url)
			print text
		elif instance.doc.url.endswith(".doc"):
			text = textract.process(instance.doc.url)
			print text
		else:
			text=""
		if text:
			extractor(request, text)
	context = {
			"form":form,
		}	

	return render(request,'accounts/home.html',context)

def register(request):
	form=RegistrationForm(request.POST or None)
	if form.is_valid():
		instance = form.save(commit=False)
		instance.save()
		return redirect('/account')
	args={'form':form}
	return render(request,'accounts/reg_form.html',args)

@login_required	
def view_profile(request):
	args={'user': request.user}
	return render(request, 'accounts/profile.html', args)	

@login_required
def edit_profile(request):
	if request.method=='POST':
		form = EditProfileForm(request.POST, instance=request.user)

		if form.is_valid():
			form.save()
			return redirect('/account/profile')

	else:
		form = EditProfileForm(instance=request.user)
		args = {'form': form}
		return render(request,'accounts/edit_profile.html', args)		

@login_required
def change_password(request):
	if request.method=='POST':
		form = PasswordChangeForm(data=request.POST, user=request.user)

		if form.is_valid():
			form.save()
			update_session_auth_hash(request, form.user)
			return redirect('/account/profile')
		else:
			return redirect('/account/profile/change-password')
	else:
		form = PasswordChangeForm(user=request.user)
		args = {'form': form}
		return render(request,'accounts/change_password.html', args)	

def pdf_extractor(url):
	text = textract.process(url)
	# try:
	pdf = codecs.open(url, encoding="ISO8859-1", mode="rb").read()
	startmark = "\xff\xd8"
	startfix = 0
	endmark = "\xff\xd9"
	endfix = 2
	i = 0
	njpg = 0
	while True:
	    istream = pdf.find("stream", i)
	    if istream < 0:
	        break
	    istart = pdf.find(startmark, istream, istream+20)
	    if istart < 0:
	        i = istream+20
	        continue
	    iend = pdf.find("endstream", istart)
	    if iend < 0:
	        raise Exception("Didn't find end of stream!")
	    iend = pdf.find(endmark, iend-20)
	    if iend < 0:
	        raise Exception("Didn't find end of JPG!")
	    istart += startfix
	    iend += endfix
	    print "JPG %d from %d to %d" % (njpg, istart, iend)
	    jpg = pdf[istart:iend]
	    f_name = re.findall(r"[\w']+", url)[-2]
	    jpgfile = codecs.open(settings.PDF2IMAGE_URL+f_name+"jpg%d.jpg" % njpg, encoding="ISO8859-1", mode="w")
	    jpgfile.write(jpg)
	    jpgfile.close()
	    njpg += 1
	    i = iend
	for file in sorted(os.listdir(settings.PDF2IMAGE_URL)):
	    print file
	    if file.startswith(f_name):
	        print "yes "+file
	        text = text + pytesseract.image_to_string(Image.open(settings.PDF2IMAGE_URL+file))
	# except:
	# 	print "error found"
	return text

def extractor(request, text):
	try:
		reload(sys)  
		sys.setdefaultencoding('utf8')
		buf = StringIO.StringIO(text)
		flag, conti, r, break_f, content, str_arr, all_val = True, 0, False, False, "", [], []
		while flag:
			if break_f == False:
				content = buf.readline()
			if content:
				content = content.strip()
				if content:
					if re.match(r'\d{1,}[.]', content):
						content = content.encode('ascii','ignore')
						content = re.sub(r'\d{1,}[.]', '', content.decode('utf-8'))
						content = re.sub(r'\n{1,}', '', content.encode('ascii','ignore')).lstrip()
						if content == "":
							title_r=0
							while content == "":
								content = buf.readline()
								content = re.sub(r'\d{1,}[.]', '', content.decode('utf-8'))
								content = re.sub(r'\n{1,}', '', content.encode('ascii','ignore').decode('utf-8')).lstrip()
						if '.' in content.decode('utf-8') or ':' in content.decode('utf-8') or ';' in content.decode('utf-8'):
							if ':' in content.decode('utf-8'):
								ind = content.index(':')
								title_r= 1	
							elif '.' in content.decode('utf-8'):
								ind = content.index('.')
							else:
								ind = content.index(';')	
							if ind < 40 or title_r:
								if len(str_arr):
									desc = " ".join(str_arr)
									del str_arr[:]
									all_val.append(desc)
								all_val.append(content[0:ind+1])
								str_arr.append(content[ind+1:])
								r = True
							else:
								if not content.isdigit():
									str_arr.append(content.strip())
						else:
							if len(str_arr):
								desc = " ".join(str_arr)
								del str_arr[:]
								all_val.append(desc)
							all_val.append(content.strip())
							r = True
					if r:
						content = buf.readline()
						prev_cont, count = ",",0
						while not re.match(r'\d{1,}[.]', re.sub(r'\n{1,}', '', content.encode('ascii','ignore')).lstrip()):
							if content:
								count = 0
								content = re.sub(r'\n{1,}', '', content.encode('ascii','ignore')).lstrip()
								if content.rstrip():
									if prev_cont[-1] != '.':
										if not content.isdigit(): 
											if "DATED" in content:
												flag = False
												break
											str_arr.append(content.strip())
									elif content[0].islower() or count < 2:
										if not content.isdigit():
											if "DATED" in content:
												flag = False
												break
											str_arr.append(content.strip())
									else:
										break
									r = False	
								else:
									count = count +1		
								if re.sub(r'\n{1,}', '', content.encode('ascii','ignore')).rstrip():
									prev_cont = re.sub(r'\n{1,}', '', content.encode('ascii','ignore')).rstrip()
								content = buf.readline()
								break_f = True
							else:
								flag = False
								break			
				else:
					break_f = False
					continue	
			else:
				flag = False
		val_prev, index_to_check=",", 0
		for val_check in str_arr:
			if val_check:
				if val_check[0].isupper() and val_prev.endswith("."):
					break				
				val_prev = val_check
				index_to_check = index_to_check + 1
		all_val.append(" ".join(str_arr[:index_to_check]))
		new_l = len(all_val)-1
		i=0
		while i < new_l:
			new = Clauses.objects.create(title=all_val[i], clause=all_val[i+1])
			new.save()
			i=i+2
	except:
		print "Some Error Occured."		
	return None	