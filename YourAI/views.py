import json
import numpy as np
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from more_itertools import take
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

            # with create the file with a folder with the user's name to avoid concurrent access
            if fs.exists(str(userAI.email)+'/data.csv'):
                fs.delete(str(userAI.email)+'/data.csv')
            filename = fs.save(str(userAI.email)+'/data.csv', file)  # saving file with same name to overwrite it on each upload
            # uploaded_file_url = fs.url(filename)

            # reading the csv file
            df = pd.read_csv(filename,delimiter=';')

            # replace empty or nan values with ######
            df = df.replace(' ', '######')
            df = df.replace(np.nan, '######')

            # number of positive & negative reviews & avg pos score
            count_positive = 0
            count_negative = 0
            avg_pos_score = 0

            prods = {}
            for line,line2 in zip(df['Reviews'],df['Products']):
                # get sentiment of review if not null
                if line != '######' and line2 != '######':
                    if line2 not in prods:
                        prods[line2] = 1
                    else:
                        prods[line2] += 1
                    sentiment = predictEmotion(line)
                    if 'Positive' in sentiment[0]:
                        count_positive += 1
                        avg_pos_score += int(sentiment[1])
                    elif 'Negative' in sentiment[0]:
                        count_negative += 1


            # avg of positive reviews
            avg_pos_score = int(avg_pos_score / count_positive)

            prods = dict(take(10,sorted(prods.items(), key=lambda x: x[1],reverse=True)))
            prod_list = []
            counts_list = []
            for p in prods:
                prod_list.append(p)
                counts_list.append(prods[p])

            context['count_positive'] = count_positive
            context['count_negative'] = count_negative
            context['avg_pos_score'] = avg_pos_score
            context['prod_list'] = prod_list
            context['counts_list'] = counts_list

            # total number of reviews
            context['total_reviews'] = count_positive + count_negative

            # delete file after finish
            fs.delete(str(userAI.email) + '/data.csv')


    except Exception as e:
       print(e)
       context['error'] = True


    return render(request, 'index.html', context=context)

# trial page
def trialPage(request):
    return render(request, 'trial.html',context={
        'oldtext':'At first i was worried about the shipment, but later it arrived and it was good'
    })

# api description page
def apiPage(request):
    return render(request, 'apidescription.html')

# api
@csrf_exempt
def api(request):
    # if POST
    if request.method == 'POST':
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            # we check existence or email and password
            if not body['email'] or not body['password'] or str(
                    body['email']).strip() == '' or str(body['password']).strip() == '':
                return HttpResponse(status="510",
                                    content="Email or password not provided with body parameters")  # 510 : email or password not filled

            elif not body['text'] or str(body['text']).strip() == '':
                return HttpResponse(status="515",
                                    content="Review text not provided with body parameters")  # 515 : text not filled

            else:
                email = body['email']
                password = body['password']
                text = body['text']
                u = YourAIUser.objects.filter(email=email)

                if not u.exists():
                    return HttpResponse(status="250",
                                        content="This user doesnt exist") # 250 user doesnt exist

                # encrypt user password and compare it
                user = YourAIUser.objects.get(email=email)
                if str(triple_des('ABCDEFRTGHJSKLDS').encrypt(password, padmode=2)) != str(user.password) :
                    return HttpResponse(status="255",
                                        content="Incorrect user password")  # 255 incorrect password

                # check if expiry date and pack (later)

                emotion = predictEmotion(text)

                return JsonResponse({
                    "sentiment":emotion[0],
                    "score":emotion[1]
                }) # 200 : good

        except Exception as e:
            print('Error : ',e)
            return HttpResponse(status="500", content="Internal Error, please make sure to have correct review text and credentials") # 500 : internal error

    # else another method was user
    else :
        return HttpResponse(status="414",content="POST method not used") # 414 : POST not used

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

            # check if email already exist
            u = YourAIUser.objects.filter(email=email).exists()
            if u:
                return render(request, 'registration/register.html', context={
                    'sent': False,
                    'message': 'Email already exist'
                })

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
        return render(request, 'error/404.html')

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
        return render(request, 'error/404.html')

# register page
def registerPage(request):
    return render(request, 'registration/register.html')

# login page
def loginPage(request):
    return render(request, 'registration/login.html')

# error handler
@csrf_exempt
def handler404(request, *args, **argv):
    return render(request, 'error/404.html')

@csrf_exempt
def handler500(request, *args, **argv):
    return render(request, 'error/500.html')