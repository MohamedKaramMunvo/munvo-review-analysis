import ast
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
from .EmotionAnalysis import predictEmotion, extractKeywords
import pandas as pd
from .models import YourAIUser
from .SMTP import *

# constant varialble for coin price ($)
COIN_PRICE = 0.03


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
@login_required
def dataexamplePage(request):
    return render(request, 'dataexample.html')

# upload file
@login_required
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

            # checking if file is in correct format
            if not df.columns.isin(['Reviews']).any():
                context['error'] = True
                context['errorMessage'] = 'Please make sure to have the Reviews column on your file, and to upload a correct CSV file'
                return render(request, 'index.html', context=context)

            # checking if file rows < 100 , if 0 token and < 100 --> error message
            size = df.shape[0]
            if userAI.coins - 0.5 < 0 and size > 100 and df.columns.isin(['Reviews']).any():
                context['error'] = True
                context['errorMessage'] = 'You cannot upload a file of more than 100 rows while you have no enough coins, please purchase more coins'
                return render(request, 'index.html', context=context)


            # replace empty or nan values with ######
            df = df.replace(' ', '######')
            df = df.replace(np.nan, '######')

            # get number of positive & negative reviews & avg pos score
            count_positive = 0
            count_negative = 0
            avg_pos_score = 0

            total_text = ''

            for line in zip(df['Reviews']) :
                # get sentiment of review if not null
                if line != '######' :
                    # gathering all the text for keywords analysis
                    total_text += str(line)
                    sentiment = predictEmotion(line)
                    if 'Positive' in sentiment[0]:
                        count_positive += 1
                        avg_pos_score += int(sentiment[1])
                    elif 'Negative' in sentiment[0]:
                        count_negative += 1


            # keywords analysis of full text (-1 if none)
            keywords = -1
            keywords_counts = []
            try :
                keywords = []
                keywords,keywords_counts = extractKeywords(total_text)
            except Exception as e:
                print(e)

            avg_pos_score = int(avg_pos_score / count_positive)

            # counts of positive,negative reviews
            context['count_positive'] = count_positive
            context['count_negative'] = count_negative

            # avg score of positivity
            context['avg_pos_score'] = avg_pos_score

            # total number of reviews
            context['total_reviews'] = count_positive + count_negative

            # 10 keywords
            context['keywords'] = keywords
            context['keywords_counts'] = keywords_counts

            # delete file after finish
            fs.delete(str(userAI.email) + '/data.csv')

            # consuming 0.5 coins after making sure everything is good
            if size > 100:
                YourAIUser.objects.filter(id=userAI.id).update(coins=userAI.coins-0.5)


    except Exception as e:
       print(e)
       context['error'] = True
       context['errorMessage'] = 'Error during upload, please review the file format, make sure to have a CSV file, and to have the column Reviews'


    return render(request, 'index.html', context=context)

# trial page
def trialPage(request):
    return render(request, 'trial.html',context={
        'oldtext':'At first i was worried about the shipment, but later it arrived and it was good'
    })

# api description page
@login_required
def apiPage(request):
    return render(request, 'apidescription.html')

# api sentiment analysis
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

                # return error if no enough credits
                if user.coins - 0.5 < 0:
                    return HttpResponse(status="270",
                                        content="Not enough credits for the request")  # 270 user doesnt exist

                emotion = predictEmotion(text)

                # consuming 0.5 coins after making sure everything is good
                YourAIUser.objects.filter(id=user.id).update(coins=user.coins - 0.5)

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


# api sentiment analysis + summarize
@csrf_exempt
def apiv2(request):
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
                    phone=phone, # expiry date default is now,
                    pack='FREE',
                )
                user = User.objects.create_user(email, email, password)

                # user is inactive by default
                aiuser.is_active = False

                aiuser.save()
                user.save()

            # send confirmation email
            subject = "Welcome to YourAI Platform!"
            body = "Dear "+aiuser.first_name+", we are excited to welcome you to YourAI\n" \
                                             "To get started, please activate your email on the following link : https://app.youraiplatform.com/activate?user="+str(aiuser.id)+"\n" \
                                             "As a welcome gift, we offer you 20 free credits to use!\n"+\
                                             "If you have any questions or issues, please let us know at team@youraiplatform.com\n\n\n"+\
                                             "Best regards\nYourAI Team"

            sendEmail(aiuser.email,subject,body)

            return render(request, 'registration/register.html', context={
                'sent': True,
                'message': 'Your account has been created successfully, please check your email for activation (check spam also)'
            })

        except Exception as e:
            print(e)
            return render(request, 'registration/register.html', context={
                'sent': False,
                'message': 'Oops, Internal Error'
            })
    else :
        return render(request, 'error/404.html')


# activate user with his id and return login page with message
def activate(request):
    if request.method == 'GET':
        # get user id
        if request.GET.get('user') :
            id = int(request.GET.get('user'))

            # if id doesnt exist then we raise an error
            if not YourAIUser.objects.filter(id=id).exists():
                return render(request, 'registration/login.html', context={
                    'successActivate': False,
                    'messageActivate': 'User not found'
                })

            aiuser = YourAIUser.objects.filter(id=id).update(is_active=True)

            return render(request, 'registration/login.html', context={
                'successActivate': True,
                'messageActivate': 'Your account has been activated!'
            })

        # if user not filled then we raise an error
        else :
            return render(request,'registration/login.html',context={
                'successActivate':False,
                'messageActivate':'User not filled'
            })
    else:
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


# http codes description
@login_required
def httpDescription(request):
    return render(request, 'httpDescription.html')

@login_required
def pricingPage(request):
    connected_user = request.user

    # get use available coins
    user = YourAIUser.objects.get(email=connected_user.email)

    return render(request,'pricing.html',context={
        "avail_coins":user.coins
    })

@login_required
def buycoins(request):

    if request.method == 'POST':

        price = request.POST['price']

        # if coins is null
        if not price :
            print("Price is null")
            return pricingPage(request)

        # if coins is not numbers
        elif not price.isnumeric():
            print("Price is not numeric")
            return pricingPage(request)

        # if coins are higher than 100 or less than 5
        elif float(price) > 100 or float(price) < 5:
            print("Price is not between 5 and 100")
            return pricingPage(request)

        # go to checkout page
        coins = int(float(price)/COIN_PRICE)+1
        print("Price : ",price," COINS : ",coins)

    else :
        return render(request, 'error/404.html')

# register page
def registerPage(request):
    return render(request, 'registration/register.html')

# login page
def loginPage(request):
    return render(request, 'registration/login.html')

# forgot password page
def forgotPasswordPage(request):
    return render(request, 'registration/forgotpassword.html')

def forgotPassword(request):
    if request.method == 'POST':
        # get user id
        if request.POST['email'] :
            # if id doesnt exist then we raise an error
            if not YourAIUser.objects.filter(email=str(request.POST['email'])).exists():
                return render(request, 'registration/forgotpassword.html', context={
                    'successActivate': False,
                    'messageActivate': 'User not found'
                })

            # retrieve decrypted password
            aiuser = YourAIUser.objects.get(email=str(request.POST['email']))
            password = aiuser.password
            decrypted_password = triple_des('ABCDEFRTGHJSKLDS').decrypt(ast.literal_eval(password), padmode=2)
            decrypted_password = str(decrypted_password, "utf-8")

            # retrieve activation link
            activation_link = "https://app.youraiplatform.com/activate?user="+str(aiuser.id)

            # resend email with password
            message = "Hey dear "+str(aiuser.first_name)+"\nPlease find your password (make sure to save it somewhere safe) : "+decrypted_password+"\n" \
                                                            "And the link to activate your account (if not) : "+activation_link+"\n\n\n"\
                                                            "Best regards\nYourAI Team"

            try:
                sendEmail(aiuser.email,"Resend password and activation link",message)
            except:
                return render(request, 'registration/forgotpassword.html', context={
                    'successActivate': False,
                    'messageActivate': 'Oops! internal error'
                })


            return render(request, 'registration/forgotpassword.html', context={
                'successActivate': True,
                'messageActivate': 'Your password and activation link were sent to your email, please also check spam'
            })


        # if user not filled then we raise an error
        else :
            return render(request,'registration/forgotpassword.html',context={
                'successActivate':False,
                'messageActivate':'User not filled'
            })
    else:
        return render(request, 'error/404.html')
    return render(request, 'registration/forgotpassword.html')

# error handler
@csrf_exempt
def handler404(request, *args, **argv):
    return render(request, 'error/404.html')

@csrf_exempt
def handler500(request, *args, **argv):
    return render(request, 'error/500.html')