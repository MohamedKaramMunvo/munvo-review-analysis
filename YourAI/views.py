import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from pyDes import triple_des
from .EmotionAnalysis import predictEmotion
import pandas as pd
from .models import YourAIUser


# home dashboard
@login_required
def home(request):
    # get the connected user
    connected_user = request.user
    userAI = YourAIUser.objects.get(email=connected_user.email)

    context = {
        'user':userAI
    }

    return render(request,'index.html',context=context)

# data example page
def dataexamplePage(request):
    return render(request, 'dataexample.html')

# upload file
def uploadFile(request):
    # get the connected user
    connected_user = request.user
    userAI = YourAIUser.objects.get(email=connected_user.email)

    context = {
        'user': userAI
    }

    try:
        # get the uploaded file
        if request.method == 'POST' and request.FILES['dataFile']:
            file = request.FILES['dataFile']
            fs = FileSystemStorage()
            if fs.exists('data.csv'):
                fs.delete('data.csv')
            filename = fs.save('data.csv', file)  # saving file with same name to overwrite it on each upload
            # uploaded_file_url = fs.url(filename)

            # reading the csv file
            df = pd.read_csv(filename,delimiter=';')
            total_reviews = df.shape[0]
            context['total_reviews'] = total_reviews

    except Exception as e:
       print(e)
       context['error'] = True


    return render(request, 'index.html', context=context)

# register page
def trialPage(request):
    return render(request, 'trial.html',context={
        'oldtext':'At first i was worried about the shipment, but later it arrived and it was good'
    })

# register
def register(request):
    if request.method == 'POST':
        try:
            firstname = request.POST['firstname']
            lastname = request.POST['lastname']
            email = request.POST['email']
            email2 = request.POST['email2']
            password = request.POST['password']
            password2 = request.POST['password2']
            phone = request.POST['phone']
            pack = request.POST['pack']

            # check password and confirm valid
            if password!=password2 :
                return render(request,'registration/register.html',context={
                    'sent':False,
                    'message':'Password and its confirmation doesnt match'
                })

            # check email and confirm valid
            elif email!=email2 :
                return render(request,'registration/register.html',context={
                    'sent':False,
                    'message':'Email and its confirmation doesnt match'
                })

            # we save User and YourAIUser (with encrypted password)
            else:
                cipherpassword = triple_des('ABCDEFRTGHJSKLDS').encrypt(password, padmode=2)
                aiuser = YourAIUser(
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    password=cipherpassword, # encrypted password is saved
                    phone=phone, # expiry date default is now
                    pack=pack
                )
                user = User.objects.create_user(email, email, password)

                aiuser.save()
                user.save()

            # if pack is not free --> go to paiement page + expiry date set + pack set

            # else

            # send confirmation email

            return render(request, 'registration/register.html', context={
                'sent': True,
                'message': 'Your account has been created successfully, please check your email'
            })

        except Exception as e:
            print(e)
            return render(request, 'registration/register.html', context={
                'sent': False,
                'message': 'Oops, Internal Error'
            })
    else :
        return render(request,'404.html')

# detect emotion from text
def detectEmotionTrial(request):
    if request.method == 'POST':

        text = request.POST['text']

        # if text is null
        if not text :
            return render(request, 'trial.html',context={
                'response':'Please fill the text',
                'responseType': 'error',
                'Emotion': '',
                'Score': ''
            })

        # if text is only numbers
        elif text.isnumeric():
            return render(request, 'trial.html', context={
                'response': 'You filled just number',
                'responseType':'error',
                'Emotion': '',
                'Score': ''
            })

        # return score and prediction
        else :
            prediction = predictEmotion(text)
            emotion = prediction[0]
            score = prediction[1]
            if prediction[0] == 'Error':
                return render(request, 'trial.html', context={
                    'response': 'Oops, an internal error occured',
                    'responseType': 'error',
                    'Emotion': '',
                    'Score': ''
                })
            else :
                return render(request, 'trial.html', context={
                    'response': '',
                    'responseType': 'success',
                    'Emotion':emotion,
                    'Score':score,
                    'oldtext':text
                })
    else :
        return render(request,'404.html')

# register page
def registerPage(request):
    return render(request, 'registration/register.html')

# login page
def loginPage(request):
    return render(request, 'registration/login.html')
