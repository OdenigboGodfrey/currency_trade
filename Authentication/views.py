from currency_trade import settings
from django.conf import settings
from django.shortcuts import render, redirect, reverse
from requests import request
from . import base
from CTAdmin.base import KYC, Utilities as AdminUtilities
import os

BusinessAccount = settings.ACCOUNT_TYPES[1]


def GetUrlReverse(request, Url, PostExtras={}):
    if len(PostExtras) > 0:
        FinalURL = reverse(Url, current_app=request.resolver_match.namespace,kwargs=PostExtras)
    else:
        FinalURL = reverse(Url, current_app=request.resolver_match.namespace)

    return FinalURL


def UserInfo(request, dict):
    dict.update({'PhoneNo': request.session['PhoneNo'], 'Email': request.session['Email'], 'AccountNumber': request.session['AccountNumber'], 'FullName': request.session['FullName']})
    if 'HTTP_REFERRER' in request.META:
        dict['Referrer'] = request.META['HTTP_REFERRER']

    if 'UserId' in request.session:
        dict.update({'UserId': request.session['UserId']})


def Login(request):
    # Login
    context = {'ErrorMessage': [], 'NoNav': True}
    if request.method == 'GET':
        if 'UserId' in request.session:
            return redirect('Authentication:Index')
        # context["ErrorMessage"] = 'N/A GET'  and 'user' in request.session
        return render(request, 'Authentication/login.html', context)
    elif request.method == 'POST':
        Result = base.Login().Handler(email=request.POST['email'], password=request.POST['password'])
        if Result["Status"]:
            if 'UserId' not in request.session:
                request.session['UserId'] = Result['UserId']
                request.session['AccountNumber'] = Result['AccountNumber']
                request.session['FullName'] = Result['FullName']
                request.session['AccountType'] = Result['AccountType']
                request.session['Email'] = Result['Email']
                request.session['PhoneNo'] = Result['PhoneNumber']
            return redirect('Authentication:Index')
        else:
            context['ErrorMessage'].append(Result['Message'])
            return render(request, 'Authentication/login.html', context)


def Homepage(request):
    # index

    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {"Message": "N/A"}
    UserInfo(request, context)
    """Check if user has completed KYC"""
    Result = base.Login().CheckKYC(request.session['UserId'])
    if Result["All"] != 0 or Result['KYCStatus'] == -1:
        return redirect('Authentication:KYC')

    if Result['KYCStatus'] == 0:
        context['KYCStatus'] = "Waiting"
    if Result['KYCStatus'] == 1:
        context['KYCStatus'] = "Admin Processing"
    if Result['KYCStatus'] == 2:
        context['KYCStatus'] = "Accepted"
    """Mark KYC logs as read"""
    Res = base.Login().MarkKYCLogsAsRead(request.session['UserId'])
    if not Res['Status']:
        """an error occurred with getting logs"""

    return redirect('Transactions:Trades')


def Signup(request):
    context = {'ErrorMessage': [], 'NoNav': True, 'ExtraScript': True}

    context['AccountTypes'] = settings.ACCOUNT_TYPES

    if 'HTTP_REFERRER' in request.META:
        context['Referrer'] = request.META['HTTP_REFERRER']

    if request.method == 'POST':
        if request.POST['Terms'] == "True":
            if request.POST['Password'] == request.POST["PasswordConfirmation"]:

                if 'R' in request.GET:
                    Result = base.Signup().Handler(request.POST, base.Utilities().DecodeReferrerCode(request.GET['R']))
                else:
                    Result = base.Signup().Handler(request.POST)

                if 'UserObject' in Result:
                    if not bool(Result["Result"]["MessageStatus"]):
                        return redirect("/authentication/tfa/" + str(Result["UserObject"].pk) + "/")
                    else:
                        context["ErrorMessage"] = "Failed to send code to specified phone number, please try again."
                        """Roll back"""
                        base.Signup().RollBack(Result['UserObject'])
                else:
                    context['ErrorMessage'].extend(Result['ErrorMessage'])
            else:
                context["ErrorMessage"].append("Passwords do not match.")
        else:
            context['ErrorMessage'].append("Please accept Terms and Privacy Policy.")

    if 'R' in request.GET:
        context['URL'] = request.get_full_path()
    if 'AdId' in request.GET:
        context['URL'] = request.get_full_path()
    return render(request, 'Authentication/signup.html', context)


def TwoFactor(request, Id):
    context = {'NoNav': True, 'ExtraScript': True, 'UserId': Id}

    if request.method == 'POST':
        if request.POST['TwoFactor']:
            UObject = base.Utilities()
            Result = UObject.Verify2fa(request.POST['TwoFactor'], Id, True)
            if Result:
                if 'AdId' in request.GET and 'NId' not in request.GET:
                    return redirect(GetUrlReverse(request, 'Transactions:Place') + "?Approved=True&AdId=" +
                                    str(request.GET['AdId']))
                if 'BTID' in request.GET:
                    return redirect(GetUrlReverse(request, 'Transactions:Place') + "?Approved=True&BTID=" + str(
                        request.GET['BTID']))

                if 'NId' in request.GET and 'AdId' in request.GET:
                    return redirect(GetUrlReverse(request, 'Transactions:BuyAd', PostExtras={'AdId': request.GET['AdId']}) + "?Approved=True&NId=" + str(
                        request.GET['NId']))

                return redirect("Authentication:Index")
            else:
                context["ErrorMessage"] = 'Codes doesnt match'
                return render(request, 'Authentication/TwoFactor.html', context)
    return render(request, 'Authentication/TwoFactor.html', context)


def ResetPassword(request):
    context = {'NoNav': True, 'ExtraScript': True}
    if request.method == 'POST':
        UObject = base.Utilities()
        context['Email'] = request.POST['Email']
        context['EmailGotten'] = True
        if request.POST['Email'] is not None and 'TwoFactorCode' in request.POST:
            Result = UObject.Verify2fa(request.POST['TwoFactorCode'], int(request.POST['UserId']), IsFromLogin=False)
            if Result:
                return redirect("/authentication/newpassword/"+str(request.POST['UserId']))
            else:
                context["ErrorMessage"] = "Wrong code entered, please try again"
                context['UserId'] = request.POST['UserId']
        else:
            """Do 2fa"""
            Result = UObject.Do2FA(Email=request.POST['Email'])
            if Result["Status"]:
                context['UserId'] = Result['UserId']
                if Result["MessageStatus"]:
                    context['MessageStatus'] = "Code sent to phone."
                else:
                    context['MessageStatus'] = "Code failed to send to phone."
            else:
                context["ErrorMessage"] = "Failed to create code"
    return render(request, "Authentication/resetpassword.html", context)


def NewPassword(request, Id):
    context = {'NoNav': True, 'ExtraScript': True}
    if request.method == 'POST':
        OldPasswordStatus = 1
        if request.POST['Password'] == request.POST['ConfirmPassword']:
            if 'OldPassword' in request.POST:
                OldPasswordStatus = base.Signup().VerifyOldPassword(request.POST['OldPassword'], request.session['UserId'])
            else:
                context['ErrorMessage'] = "Invalid request."
            if OldPasswordStatus != 0:
                if OldPasswordStatus == 2:
                    Result = base.Signup().ResetPassword(request.POST['ConfirmPassword'], Id, request.GET['CP'])
                else:
                    Result = base.Signup().ResetPassword(request.POST['ConfirmPassword'], Id)

                if Result["Status"] and OldPasswordStatus == 1:
                    return redirect("/authentication/login/")
                elif Result['Status'] and OldPasswordStatus == 2:
                    return redirect("/profile/")
                else:
                    context["ErrorMessage"] = Result["ErrorMessage"]
            else:
                context['ErrorMessage'] = "Old password isn't correct. Please try again."
        else:
            context['ErrorMessage'] = "Passwords don't match."
    if 'CP' in request.GET:
        context['CP'] = request.GET['CP']
    context['UserId'] = Id
    return render(request, 'Authentication/newpassword.html', context)


def KYCUpload(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    Data = {"ErrorMessage": [], 'AccountType': request.session['AccountType'],
            'BusinessAccount': BusinessAccount}

    UserInfo(request, Data)

    if request.method == 'POST':
        Result = base.Login().CheckKYC(request.session['UserId'])

        if 'KYCStatus' in Result and int(Result['KYCStatus']) == 2:
            Data['ErrorMessage'].append("Invalid request.")
            return render(request, 'Authentication/kyc.html', Data)

        FileData = {}
        if 'Selfie' in request.FILES:
            FileData['Selfie'] = request.FILES.getlist('Selfie')
        else:
            Data["ErrorMessage"].append("A selfie Showing you holding your ID is required.")
        if 'BackId' in request.FILES:
            BackId = request.FILES.getlist('BackId')
            FileData['BackId'] = BackId
        else:
            Data["ErrorMessage"].append("A picture of your ID's back page is required.")
        if 'FrontId' in request.FILES:
            FileData['FrontId'] = request.FILES.getlist('FrontId')
        else:
            Data["ErrorMessage"].append("A picture of your ID's front page is required.")
        if 'Address' in request.FILES:
            FileData['Address'] = request.FILES.getlist('Address')
        else:
            Data["ErrorMessage"].append("A proof of address is required.")

        if Data['AccountType'] == Data['BusinessAccount']['val']:
            if 'MEMAT' in request.FILES:
                FileData['MEMAT'] = request.FILES.getlist('MA_Cert')
            else:
                Data["ErrorMessage"].append("A proof of MEMAT is required.")

            if 'CAC' in request.FILES:
                FileData['CAC'] = request.FILES.getlist('CAC')
            else:
                Data["ErrorMessage"].append("A proof of CAC is required.")

        if len(Data['ErrorMessage']) == 0:
            for Key in FileData:
                for file in FileData[Key]:
                    filename = request.session['UserId']
                    base_path = settings.SELFIEPATH
                    if Key == "BackId":
                        base_path = settings.BACKIDPATH
                    elif Key == "FrontId":
                        base_path = settings.FRONTIDPATH
                    elif Key == "Address":
                        base_path = settings.ADDRESSPATH
                    elif Key == "MEMAT":
                        base_path = settings.MEMAT
                    elif Key == "CAC":
                        base_path = settings.CAC

                    ext = str(file).split(sep=".")[-1].lower()
                    filename = str(filename) + "." + ext
                    if ext not in ['jpg', 'png', 'jpeg']:
                        Data["ErrorMessage"].append("Image format not supported, "
                                                    "Please make sure image is of the type jpg, jpeg or png.")
                    else:
                        if not settings.LOCAL_UPLOAD:
                            AdminUtilities().UploadToS3(file, filename, base_path)
                        else:
                            if not os.path.exists(base_path):
                                os.mkdir(base_path)

                            with open(base_path+filename, 'wb+') as destination:
                                for chunk in file.chunks():
                                    destination.write(chunk)

                        KYC().HanldeKYC(request.session['UserId'])
        return redirect('Transactions:Trades')
    return render(request, 'Authentication/kyc.html', Data)


def Referred(request, Code):
    SignupURL = reverse('Authentication:Signup', current_app=request.resolver_match.namespace)
    return redirect(SignupURL + "?R=" + Code)


def Logout(request):
    if 'UserId' in request.session:
        del request.session['UserId']
        del request.session['AccountNumber']
        del request.session['FullName']
        del request.session['AccountType']
        del request.session['Email']
        del request.session['PhoneNo']
    return redirect('pages:index')


def More(request):
    if 'UserId' not in request.session:
        return redirect('Authentication:Login')

    context = {'More': 1}
    UserInfo(request, context)

    return render(request, 'Authentication/More.html', context)


