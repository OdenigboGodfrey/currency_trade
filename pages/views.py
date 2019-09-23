from django.shortcuts import render, redirect
from Transactions import base as TransactionBase
from .models import *

# Create your views here.


def UserInfo(request, dict):
    if 'UserId' in request.session:
        dict.update({'UserId': request.session['UserId']})


def index(request):
    context = {'Home': 1,'Currencies': []}
    UserInfo(request, context)

    Result = TransactionBase.TransactionBaseClass().GetAllAds()
    context.update(Result)

    Result = TransactionBase.CurrenciesBaseClass().GetCurrencies()
    if 'Exception' in Result:
        for Cur in Result['CurrenciesObject']:
            context['Currencies'].append({"Cur": Cur.CountryCurrencyShort, "Name": Cur.CurrencyName})
    else:
        for Cur in Result['results']:
            context['Currencies'].append({"Cur": Cur, "Name": Result['results'][Cur]["currencyName"]})
            TransactionBase.CurrenciesBaseClass().SaveCurrency(Cur, Result['results'][Cur]["currencyName"])

    if 'from' in request.GET and 'to' in request.GET:
        Result = TransactionBase.CurrenciesBaseClass().GetServerRate(request.GET['from'], request.GET['to'])
        if 'Exception' in Result and Result['Exception'] == 0:
            context['Rate'] = Result['ExRObject'].ExchangeRate
        elif 'Exception' in Result and Result['Exception'] == 1:
            context['Rate'] = 0.0
        else:
            context['Rate'] = Result[request.GET['from'] + "_" + request.GET['to']]['val']
            TransactionBase.CurrenciesBaseClass().SaveExchangeRate(request.GET['from'] + "_" + request.GET['to'],
                                                         context['Rate'])
        context['FromSelectedItem'] = request.GET['from']
        context['ToSelectedItem'] = request.GET['to']

    return render(request, 'pages/index.html', context)


def About(request):
    context = {'About': 1}

    UserInfo(request, context)

    return render(request, 'pages/about.html', context)


def Contact(request):
    context = {'Contact': 1}
    UserInfo(request, context)

    if request.method == 'POST':
        try:
            contact_object = contact()
            contact_object.FirstName = request.POST['FirstName']
            contact_object.LastName = request.POST['LastName']
            contact_object.Email = request.POST['Email']
            contact_object.Phone = request.POST['Phone']
            contact_object.Message = request.POST['Message']

            contact_object.save()

            context['message'] = "Information sent."
            context['message_type'] = 1
        except:
            context['message'] = "Information failed to send."
            context['message_type'] = 0

    return render(request, 'pages/contact.html', context)


def FAQ(request):
    context = {'FAQ': 1}
    UserInfo(request, context)

    return render(request, 'pages/faq.html', context)


def Services(request):
    context = {'Services': 1}
    UserInfo(request, context)

    return render(request, 'pages/service.html', context)


def NewsLetter(request):
    if request.method == 'POST':
        newsletter_object = newsletter()
        newsletter_object.Email = request.POST['Email']

        newsletter_object.save()

    return redirect('pages:index')

