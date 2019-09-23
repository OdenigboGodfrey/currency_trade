from django.shortcuts import render, redirect, reverse
from . import base
import hashlib
from django.conf import settings
from datetime import datetime
import os
from CTAdmin import base as AdminBase
from Profile import base as ProfileBase
from Authentication import  base as AuthBase

app_name = "Transactions"
MaxAmount = float(10000)
BusinessAccount = settings.ACCOUNT_TYPES[1]
"""used in Buying and Placing a trade"""
BusinessCurrencies = ["USD", "EUR", "GBP"]
BusinessFee = 150
TwoFAUrl = "/authentication/tfa/"


def GetUrlReverse(request, Url, PostExtras={}):
    if len(PostExtras) > 0:
        FinalURL = reverse(Url, current_app=request.resolver_match.namespace,kwargs=PostExtras)
    else:
        FinalURL = reverse(Url, current_app=request.resolver_match.namespace)

    return FinalURL


def UserInfo(request, dict):
    dict.update({'PhoneNo': request.session['PhoneNo'], 'Email': request.session['Email'],
                 'AccountNumber': request.session['AccountNumber'], 'FullName': request.session['FullName'],
                 })

    if 'UserId' in request.session and 'UserId' not in dict:
        dict.update({'UserId': request.session['UserId']})


def index(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {}
    UserInfo(request, context)
    return render(request, 'Transactions/index.html', context)


def Place(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {"Currencies": [], "Rate": "1.82", "Message": [], 'AccountType': request.session['AccountType'],
               'BusinessAccount': BusinessAccount, 'MaxAmount': MaxAmount, 'BusinessCurrencies': BusinessCurrencies}
    UserInfo(request, context)
    # Set Account type details

    if 'Approved' in request.GET and ('AdId' in request.GET or 'BTID' in request.GET):
        print('redirected')
        """ otp verification successful. """
        if 'AdId' in request.GET:
            Result = base.TransactionBaseClass().ApproveTradeAd(request.GET['AdId'])
        elif 'BTID' in request.GET:
            Result = base.TransactionBaseClass().ApproveTradeAd(request.GET['BTID'], Type="Bulk")

        if Result['Status']:
            return redirect('Transactions:Trades')

    if request.method == 'POST':
        if float(request.POST['Amount']) > MaxAmount:
            if request.POST['FromCurrency'] in BusinessCurrencies:
                if context['AccountType'] == context['BusinessAccount']['val']:
                    if float(request.POST['ExchangeRate']) != 0:
                        """ save trade offer """
                        Result = base.TransactionBaseClass().NewTradeAd(request.POST, request.session['UserId'])

                        if Result['Status']:
                            print('Trade Placed.')
                            """ handle 2fa"""
                            TFAResult = AuthBase.Utilities().Do2FA(Email=request.session['Email'])

                            if TFAResult['MessageStatus'] or TFAResult['EmailStatus']:
                                """ do OTP """
                                if request.POST['SellOnce'] != "True":
                                    """ if Bulk send different ID """
                                    return redirect(
                                        TwoFAUrl + str(request.session['UserId']) + "/?BTID=" + str(Result['BTID']))
                                else:
                                    return redirect(
                                        TwoFAUrl + str(request.session['UserId']) + "/?AdId=" + str(Result['AdId']))
                            else:
                                context['Messages'].append("Failed to send OTP")
                        else:
                            context['Message'].append(Result['Message'])
                    else:
                        context['Message'].append('Please enter a valid exchange rate.')
        else:
            """
                not a business account or amount not high enough or 
                currency not in business currencies(business account currencies) 
            """
            Result = base.TransactionBaseClass().NewTradeAd(request.POST, request.session['UserId'])

            if Result['Status']:
                TFAResult = AuthBase.Utilities().Do2FA(Email=request.session['Email'])
                if TFAResult['MessageStatus'] or TFAResult['EmailStatus']:
                    """ otp sent """
                    if request.POST['SellOnce'] != "True":
                        """ if Bulk send different ID """
                        return redirect(
                            TwoFAUrl + str(request.session['UserId']) + "/?BTID=" + str(Result['BTID']))
                    else:
                        return redirect(
                            TwoFAUrl + str(request.session['UserId']) + "/?AdId=" + str(Result['AdId']))

    Result = base.CurrenciesBaseClass().GetCurrencies()
    if 'Exception' in Result:
        for Cur in Result['CurrenciesObject']:
            context['Currencies'].append({"Cur": Cur.CountryCurrencyShort, "Name": Cur.CurrencyName})
    else:
        for Cur in Result['results']:
            context['Currencies'].append({"Cur": Cur, "Name": Result['results'][Cur]["currencyName"]})
            base.CurrenciesBaseClass().SaveCurrency(Cur, Result['results'][Cur]["currencyName"])

    if 'from' in request.GET and 'to' in request.GET:
        Result = base.CurrenciesBaseClass().GetServerRate(request.GET['from'], request.GET['to'])
        if 'Exception' in Result and Result['Exception'] == 0:
            context['Rate'] = Result['ExRObject'].ExchangeRate
        elif 'Exception' in Result and Result['Exception'] == 1:
            context['Rate'] = float(0.0)
        else:
            context['Rate'] = Result[request.GET['from'] + "_" + request.GET['to']]['val']
            base.CurrenciesBaseClass().SaveExchangeRate(request.GET['from'] + "_" + request.GET['to'],
                                                         context['Rate'])
        context['FromSelectedItem'] = request.GET['from']
        context['ToSelectedItem'] = request.GET['to']
    context['CTFee'] = float(base.TransactionBaseClass().GetCTFee())
    context.update(ProfileBase.Bank().Banks(request.session['UserId']))
    return render(request, 'Transactions/Place.html', context)


def MyTrades(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'Message': []}
    UserInfo(request, context)

    if 'eid' in request.GET and int(request.GET['eid']) == 0:
        context['Message'].append('Unauthorized Action.')
    elif 'eid' in request.GET and int(request.GET['eid']) == 1:
        context['Message'].append('Transaction Closed.')

    Result = base.TransactionBaseClass().GetMyAds(request.session['UserId'])
    context.update(Result)
    context['UserId'] = int(request.session['UserId'])
    return render(request, 'Transactions/MyTrades.html', context)


def Trades(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'Trades': 1}
    UserInfo(request, context)

    Result = base.TransactionBaseClass().GetAllAds()
    context.update(Result)

    context['UserId'] = int(request.session['UserId'])
    return render(request, 'Transactions/Trades.html', context)


def BuyAd(request, AdId):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')



    if 'sid' not in request.GET and 'NId' not in request.GET:
        return redirect('Transactions:Trades')
    if 'NId' in request.GET:
        Result = base.TransactionBaseClass().ApproveTradeInterest(request.GET['NId'])

        if Result['Status']:
            return redirect('Transactions:OnGoing')
        else:
            Message = 'Failed to approve Trade Interest.'

    context = {'UserId': request.session['UserId'], 'SellerId': request.GET['sid'], 'Message': [],
               'BusinessCurrencies': BusinessCurrencies}
    UserInfo(request, context)

    if Message:
        context['Messages'].append(Message)

    Result = base.TransactionBaseClass().GetAdById(AdId)
    context.update(Result)
    Messages = ["I am willing to pay immediately.", "I am interested but can't pay immediately."]

    # Set Transaction Details
    context['AccountType'] = request.session['AccountType']
    context['BusinessAccount'] = BusinessAccount
    context['MaxAmount'] = MaxAmount
    context['BusinessFee'] = BusinessFee

    if Result['TransactionObject'].Amount >= context['MaxAmount'] and str(Result['TransactionObject'].FromCurrency) in BusinessCurrencies:
        context['Fee'] = str(BusinessFee) + Result['TransactionObject'].FromCurrency
    else:
        context['Fee'] = str(Result['TransactionObject'].CTFee) + "%"

    if request.method == 'POST' and request.POST['Buy']:
        if request.POST['Message'] in Messages:
            if 'ProposedRate' in request.POST:
                try:
                    Result = base.TransactionBaseClass().BuyAd(AdId=AdId, UserId=request.session['UserId'],
                                                               Message=request.POST['Message'],
                                                               ProposedRate=float(request.POST['ProposedRate']),
                                                               SellerId=request.GET['sid'])
                except ValueError:
                    context['Message'].append("Please enter a valid rate.")
            else:
                Result = base.TransactionBaseClass().BuyAd(AdId=AdId, UserId=request.session['UserId'],
                                                           Message=request.POST['Message'],
                                                           SellerId=request.GET['sid'])
            if Result['Status']:
                """ do 2fa """
                TFAResult = AuthBase.Utilities().Do2FA(Email=request.session['Email'])
                if TFAResult['MessageStatus'] or TFAResult['EmailStatus']:
                    """ otp sent """
                    return redirect(TwoFAUrl + str(request.session['UserId']) + "/?AdId=" + str(AdId) + "&NId=" + str(Result['NId']))
                else:
                    context['Message'].append("Failed to sent OTP.")
            if 'Message' in Result:
                context['Message'].append(Result['Message'])
        else:
            context['Message'].append("Selected Message is invalid")
    elif request.method == 'POST' and not request.POST['Buy']:
        return redirect('Transactions:Trades')

    context['Messages'] = Messages
    context['CTFee'] = float(base.TransactionBaseClass().GetCTFee())
    context.update(ProfileBase.Bank().Banks(request.session['UserId']))

    return render(request, 'Transactions/BuyAd.html', context)


def Negotiations(request, AdId):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'Message': []}
    UserInfo(request, context)

    if 'Accept' in request.GET or 'Decline' in request.GET:
        if 'N' in request.GET:
            if 'Accept' in request.GET:
                Result = base.TransactionBaseClass().ActionOnNegotiation(True, request.GET['N'])
            if 'Decline' in request.GET:
                Result = base.TransactionBaseClass().ActionOnNegotiation(False, request.GET['N'])
            context['Message'].append(Result['Message'])
        else:
            context['Message'].append("Invalid request. Please try again.")
    context.update(base.TransactionBaseClass().GetNegotiations(AdId))
    """get this trade ad information"""
    context.update(base.TransactionBaseClass().GetAdById(AdId))
    """get buyer/seller info if paid"""
    PaymentObject = base.TransactionBaseClass().GetPaid(AdId)
    """ mini context to be used to get filename for admin upload of proof of payment."""
    MiniContext = {}
    if PaymentObject['SellerPaid']:
        if settings.LOCAL_UPLOAD:
            MiniContext['S_FileName'] = "/static/CTAdmin/Uploads/" + app_name + "/Admin/" + PaymentObject[
                'SellerPayment'].FileName
        else:
            MiniContext['S_FileName'] = settings.STATIC_URL + "CTAdmin/Uploads/" + app_name + "/Admin/" + PaymentObject[
                'SellerPayment'].FileName
        context.update(MiniContext)
    if PaymentObject['BuyerPaid']:
        if settings.LOCAL_UPLOAD:
            MiniContext['B_FileName'] = "/static/CTAdmin/Uploads/" + app_name + "/Admin/" + PaymentObject['BuyerPayment'].FileName
        else:
            MiniContext['B_FileName'] = settings.STATIC_URL + "CTAdmin/Uploads/" + app_name + "/Admin/" + PaymentObject[
                'BuyerPayment'].FileName
        context.update(MiniContext)
    context.update(PaymentObject)

    """get reviews if any"""
    ReviewsObject = base.TransactionBaseClass().GetReview(request.session['UserId'], AdId)
    if ReviewsObject['ReviewsLen'] > 0:
        context.update(ReviewsObject)
    context['AdId'] = AdId
    context['UserId'] = int(request.session['UserId'])
    context['AccountNumber'] = request.session['AccountNumber']
    context['IsAdmin'] = False
    context['CTFee'] = base.TransactionBaseClass().GetCTFee()
    return render(request, 'Transactions/Negotiations.html', context)


def NLog(request, AdId):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'Message': []}
    UserInfo(request, context)

    return render(request, 'Transactions/NLog.html', base.TransactionBaseClass().GetNLog(AdId))


def OnGoing(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'Message': []}
    UserInfo(request, context)

    if 'stat' in request.GET:
        if int(request.GET['stat']) == 1:
            context['Message'].append("Payment saved.")
        else:
            context['Message'].append("Invalid request.")
    Result = base.TransactionBaseClass().GetMyOnGoingAds(request.session['UserId'])
    context.update(Result)
    context['UserId'] = int(request.session['UserId'])
    context['AccountNumber'] = request.session['AccountNumber']
    return render(request, 'Transactions/OnGoing.html', context)


def Completed(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'Message': []}
    UserInfo(request, context)

    Result = base.TransactionBaseClass().GetMyCompletedAds(request.session['UserId'])
    context.update(Result)
    context['UserId'] = request.session['UserId']
    context['AccountNumber'] = request.session['AccountNumber']
    context['Completed'] = True
    return render(request, 'Transactions/Completed.html', context)


def Paid(request, AdId):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    OngoingTransactionURL = reverse('Transactions:OnGoing', current_app=request.resolver_match.namespace)
    context = {'Message': []}
    UserInfo(request, context)
    
    if 'bid' not in request.GET or request.GET['bid'] == '' or 'from' not in request.GET:
        return redirect(OngoingTransactionURL + "?stat=-1")
    else:
        if request.method == 'POST':

            """upload file first then save"""
            filename = hashlib.sha1(datetime.now().__str__().encode()).hexdigest()
            base_path = settings.TRANSACTIONPATH
            if not os.path.exists(base_path):
                os.mkdir(base_path)

            ext = os.path.splitext(str(request.FILES['file']))[1]

            filename = filename + '.' + ext[1::]

            if ext[1::] not in ['jpg', 'png', 'jpeg']:
                context["Message"].append(
                    "Image format not supported, Please make sure image is of the type jpg, jpeg or png.")
            else:
                file = request.FILES['file']
                with open(base_path+filename, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
            """save to db """
            base.TransactionBaseClass().Paid(AdId, request.GET['bid'], filename)
            if request.GET['from'] == 'ongoing':
                return redirect(OngoingTransactionURL + "?stat=1")
            elif request.GET['from'] == 'mytrades':
                return redirect(OngoingTransactionURL + "?stat=1")
    return render(request, 'Transactions/Paid.html', context)


def PlaceReview(request, AdId):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')
    
    context = {'Message': []}
    UserInfo(request, context)
    
    if request.method == 'POST':
        base.TransactionBaseClass().PostReview(AdId, request.POST['Review'], request.session['UserId'])

    context['ReviewOptions'] = ['Transaction was okay.', 'Too much time was taken to pay.', 'Slow response time.']
    return render(request, 'Transactions/PlaceReview.html', context)


def Rejected(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'Message': []}
    UserInfo(request, context)

    Result = base.TransactionBaseClass().GetDeclinedTransactions(request.session['UserId'])
    context.update(Result)
    context['UserId'] = request.session['UserId']
    context['AccountNumber'] = request.session['AccountNumber']
    context['Completed'] = False
    return render(request, 'Transactions/Completed.html', context)


def Close(request, AdId):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'Message': []}
    UserInfo(request, context)

    Result = base.TransactionBaseClass().Close(request.session['UserId'], AdId)
    URL = reverse('Transactions:MyTrades', current_app=request.resolver_match.namespace)
    if not Result['Status']:
        return redirect(URL + "?eid=0")
    else:
        return redirect(URL + "?eid=1")


def BTransactions(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')
    context = {'Message': []}
    UserInfo(request, context)

    if 'resell' in request.GET:
        Result = AdminBase.Transactions().Automate(request.GET['resell'], Now=True)
        print(Result)
        if not Result:
            context['Message'].append('Failed to sell trade bit.')

    context.update(base.TransactionBaseClass().GetBulk(request.session['UserId']))
    return render(request, 'Transactions/BulkTransactions.html', context)


def Bonus(request):
    return

