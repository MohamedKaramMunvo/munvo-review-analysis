import ast
import hashlib
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
from .EmotionAnalysis import predictEmotion, extractKeywords, predictSummary
import pandas as pd
from .models import YourAIUser, TransactionLog
from .SMTP import *

# constant varialble for coin price ($)
COIN_PRICE = 0.03


# home dashboard
def home(request):
    return render(request,'index.html')

# data example page
def dataexamplePage(request):
    return render(request, 'dataexample.html')

# upload file
def uploadFile(request):
    context = {
    }

    try:
        # get the uploaded file
        if request.method == 'POST' and request.FILES['dataFile']:
            file = request.FILES['dataFile']
            fs = FileSystemStorage()

            # with create the file with a folder with the user's name to avoid concurrent access
            filename = fs.save('data.csv', file)  # saving file with same name to overwrite it on each upload
            # uploaded_file_url = fs.url(filename)

            # reading the csv file
            df = pd.read_csv(filename,delimiter=';')

            # checking if file is in correct format
            if not df.columns.isin(['Reviews']).any():
                context['error'] = True
                context['errorMessage'] = 'Please make sure to have the Reviews column on your file, and to upload a correct CSV file'
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
            fs.delete('data.csv')


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
def apiPage(request):
    return render(request, 'apidescription.html')

# api sentiment analysis
@csrf_exempt
def apisentiment(request):
    # if POST
    if request.method == 'POST':
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)
            # we check existence or text
            if not body['text'] or str(body['text']).strip() == '':
                return HttpResponse(status="515",
                                    content="Review text not provided with body parameters")  # 515 : text not filled

            else:
                text = body['text']

                emotion = predictEmotion(text)

                return JsonResponse({
                    "sentiment":emotion[0],
                    "score":emotion[1]
                }) # 200 : good

        except Exception as e:
            print('Error : ',e)
            return HttpResponse(status="500", content="Internal Error, please make sure to have correct review text") # 500 : internal error

    # else another method was user
    else :
        return HttpResponse(status="414",content="POST method not used") # 414 : POST not used


# api sentiment analysis + summarize
@csrf_exempt
def apisummary(request):
    # if POST
    if request.method == 'POST':
        try:
            body_unicode = request.body.decode('utf-8')
            body = json.loads(body_unicode)

            if not body['text'] or str(body['text']).strip() == '':
                return HttpResponse(status="515",
                                    content="Review text not provided with body parameters")  # 515 : text not filled

            else:
                text = body['text']

                summary = predictSummary(text)

                # in case of error
                if summary == '-1':
                    return HttpResponse(status="500",
                                        content="Internal Error, please make sure to have correct review text")  # 500 : internal error


                return JsonResponse({
                    "summary":summary
                }) # 200 : good

        except Exception as e:
            print('Error : ',e)
            return HttpResponse(status="500", content="Internal Error, please make sure to have correct review text") # 500 : internal error

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
                )
                user = User.objects.create_user(email, email, password)

                # we generate a hash token for this user
                token = hashlib.shake_128(str(email).encode('utf-8')).hexdigest(4)
                aiuser.token = str(token)

                # user is inactive by default
                aiuser.is_active = False

                aiuser.save()
                user.save()

            # send confirmation email
            subject = "Welcome to YourAI Platform - Please Confirm Your Email"
            body = "Dear "+aiuser.first_name+"\n\n" \
                                             "We are thrilled to welcome you to the YourAI Platform! To get started, please confirm your email address by clicking on the following link:\nhttps://app.youraiplatform.com/activate?user="+str(aiuser.token)+"\n\n" \
                                             "As a welcome gift, we would like to offer you 20 free coins to use on the platform. You can start exploring the many features of the YourAI Platform right away!\n"+\
                                             "If you have any questions or run into any issues, please do not hesitate to reach out to us at team@youraiplatform.com. We are always here to help you.\n\n"+\
                                             "Best regards\nYourAI Team"

            sendEmail(aiuser.email,subject,body)

            return render(request, 'registration/register.html', context={
                'sent': True,
                'message': 'Your account has been created successfully, please check your email for activation, CHECK SPAM AND PROMOTION'
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
            id = str(request.GET.get('user'))

            # if id doesnt exist then we raise an error
            if not YourAIUser.objects.filter(token=id).exists():
                return render(request, 'registration/login.html', context={
                    'successActivate': False,
                    'messageActivate': 'User not found'
                })

            aiuser = YourAIUser.objects.filter(token=id).update(is_active=True)

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

        # log that user went to checkout page (pending operation)
        try:
            connected_user = request.user
            userAI = YourAIUser.objects.get(email=connected_user.email)
            log = TransactionLog(
                email=userAI.email,
                price=float(price),
                status="pending"
            )
            log.save()
        except Exception as e:
            print("Transaction Log Exception:",e)

        return render(request,'checkout.html',context={
            "price":float(price),
            "coins":coins,
            "acceptPage":True
        })

    else :
        return render(request, 'error/404.html')

# successful payment action ( should only be accessible from the website )
## that is why we treat the current session used and not retrieve email id from the request
## csrf token is also used to make sure that we use the web app form
@login_required
def paymentSuccess(request):

    if request.method == 'POST':

        # getting purchased coins
        data = json.loads(request.body)
        coins = data['coins']

        # checking if coins value is correct
        try:
            coins = int(coins)
        except:
            return JsonResponse('Coins value is not supported', safe=False, status="500")

        # getting actual user
        connected_user = request.user
        userAI = YourAIUser.objects.get(email=connected_user.email)

        # log that payment is successful
        try:
            log = TransactionLog(
                email=userAI.email,
                price=int(coins) * COIN_PRICE,
                status="success"
            )
            log.save()
        except Exception as e:
            print("Transaction Log Exception:", e)

        # adding coins to account
        YourAIUser.objects.filter(id=userAI.id).update(coins=userAI.coins+coins)

        # send confirmation email
        message = "Dear "+str(userAI.first_name)+",\n\nWe hope this email finds you well. We wanted to take a moment to thank you for choosing the YourAI Platform and to let you know that your recent purchase has been successfully processed.\n\n" \
                  "According to our records, you have purchased "+str(coins)+" coins that you can use to access and explore our features of the YourAI Platform.\n\n"\
                  "If you have any questions or concerns about your purchase, please do not hesitate to reach out to us at team@youraiplatform.com. Alternatively, you can use the \"Contact Us\" section on our website at https://youraiplatform.com to get in touch with us.\n\n"\
                  "We are always here to help you, so please don't hesitate to contact us if you need any assistance.\n\n"\
                  "Thank you again for choosing the YourAI Platform. We look forward to serving you in the future.\n\n"\
                  "Best regards\nYourAI Team"
        try:
            sendEmail(userAI.email, "Payment Confirmation - YourAI Platform", message)
        except:
            pass


        return JsonResponse('OK', safe=False,status="200")

    else:
        return JsonResponse('METHOD NOT SUPPORTED', safe=False,status="417")

@login_required
# payment done page
def paymentDone(request):
    return render(request,'payment_success.html')

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
            activation_link = "https://app.youraiplatform.com/activate?user="+str(aiuser.token)

            # resend email with password
            message = "Hello "+str(aiuser.first_name)+"\n\nWe hope this message finds you well. We are writing to provide you with your login credentials for the YourAI Platform. Please find your password below:\nPassword: "+decrypted_password+"\n\n" \
                                                            "Please make sure to save your password in a secure location.\n\n"\
                                                            "In addition, if you have not yet activated your account, please use the following link:\n"+activation_link+"\n\n"\
                                                            "Thank you for choosing the YourAI Platform. If you have any questions or issues, please do not hesitate to contact us.\n\n"\
                                                            "Best regards\nYourAI Team"

            try:
                sendEmail(aiuser.email,"Your Password and Account Activation for YourAI Platform",message)
            except Exception as e:
                print(e)
                return render(request, 'registration/forgotpassword.html', context={
                    'successActivate': False,
                    'messageActivate': 'Oops! internal error'
                })


            return render(request, 'registration/forgotpassword.html', context={
                'successActivate': True,
                'messageActivate': 'Your password and activation link were sent to your email, CHECK SPAM AND PROMOTION'
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