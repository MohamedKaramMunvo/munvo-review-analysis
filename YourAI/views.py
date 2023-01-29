from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from .EmotionAnalysis import predictEmotion




# home dashboard
@login_required
def home(request):
    context = {
        'test':'test'
    }
    permission_classes = (IsAuthenticated,)
    return render(request,'index.html',context=context)

# register page
def trialPage(request):
    return render(request, 'trial.html',context={
        'oldtext':'At first i was worried about the shipment, but later it arrived and it was good'
    })

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
