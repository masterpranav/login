from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


# Create your models here.
class Clauses(models.Model):
	title = models.CharField(max_length=2000)
	clause = models.TextField()

	def __unicode__(self):
		return self.title

	def __str__(self):
		return self.title

class Document(models.Model):
	title = models.CharField(max_length=120)
	doc = models.FileField(null=False, blank=True)

class UserProfile(models.Model):
	user = models.OneToOneField(User)
	description= models.CharField(max_length=100, default='')
	city = models.CharField(max_length=100, default='')
	website = models.URLField(default='')
	phone = models.IntegerField(default=0)

def create_profile(sender,**kwargs):
	if kwargs['created']:
		user_profile = UserProfile.objects.create(user=kwargs['instance'])

post_save.connect(create_profile, sender=User)
