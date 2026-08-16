from django.db import models

# Create your models here.
class Student(models.Model):
    name = models.CharField(max_length=20)
    surname = models.CharField(max_length=20)
    graduated = models.BooleanField(default=False)
    age = models.IntegerField(default=15)

    def __str__(self):
        return f"{self.name} {self.surname}"

from django.db import models



class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    pages = models.IntegerField()
    price = models.IntegerField()
    published = models.BooleanField(default=False)


    def __str__(self):
        return self.title