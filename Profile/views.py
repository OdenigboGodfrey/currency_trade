from django.shortcuts import render, redirect
from . import base
from django.conf import settings
from CTAdmin.base import Utilities as AdminUtilities

# Create your views here.
APP_NAME = 'Profile'


def UserInfo(request, dict):
    dict.update({'PhoneNo': request.session['PhoneNo'], 'Email': request.session['Email'],
                 'AccountNumber': request.session['AccountNumber'], 'FullName': request.session['FullName'],
                 })
    if 'UserId' in request.session and 'UserId' not in dict:
        dict.update({'UserId': request.session['UserId']})


def index(request):
    context = {}
    if 'HTTP_REFERER' in request.META:
        context['Referrer'] = request.META.get('HTTP_REFERER')

    if 'UserId' not in request.session:
        return redirect('/authentication/login')

    UserInfo(request, context)

    Result = base.Edit().GetInfo(request.session['UserId'])
    print(Result)
    if 'DP' in Result:
        Result['DP'] = "." + Result['DP']
        if settings.LOCAL_UPLOAD:
            Result['DP'] = "/static/" + APP_NAME + "/Uploads/Display/" + str(request.session['UserId']) + Result['DP']
        else:
            Result['DP'] = settings.STATIC_URL + APP_NAME + "/Uploads/Display/" + str(request.session['UserId']) + Result['DP']

    context.update(Result)
    context['UserId'] = request.session['UserId']
    return render(request, 'Profile/index.html', context)


def Edit(request):
    context = {}

    if 'HTTP_REFERER' in request.META:
        context['Referrer'] = request.META.get('HTTP_REFERER')

    if 'UserId' not in request.session:
        return redirect('/authentication/login')

    UserInfo(request, context)

    if request.method == 'POST':
        base.Edit().PostInfo(request.POST, request.session['UserId'])
        """Retrieve Updated info from the db"""
    Result = base.Edit().GetInfo(request.session['UserId'])
    context.update(Result)
    return render(request, 'Profile/Edit.html', context)


def Bank(request):
    context = {}
    if 'HTTP_REFERER' in request.META:
        context['Referrer'] = request.META.get('HTTP_REFERER')

    if 'UserId' not in request.session:
        return redirect('/authentication/login')

    UserInfo(request, context)

    context['Message'] = []
    if 'remstat' in request.GET:
        context['Message'].append('Bank removed successfully.')
    """Get all the banks for this user"""
    context.update(base.Bank().Banks(request.session['UserId']))
    return render(request, 'Profile/viewbanks.html', context)


def BankAdd(request):
    context = {'Message': [], 'NoNav': True, 'ExtraScript': True}
    if 'HTTP_REFERER' in request.META:
        context['Referrer'] = request.META.get('HTTP_REFERER')

    if 'UserId' not in request.session:
        return redirect('/authentication/login')

    UserInfo(request, context)

    if request.method == 'POST':
        Result = base.Bank().AddBank(request.POST, request.session['UserId'])
        if Result is not None:
            return redirect('Profile:Bank-Accounts')

    return render(request, 'Profile/addbank.html', context)


def RemoveBank(request):
    context = {'Message': ''}
    if 'UserId' not in request.session:
        return redirect('/authentication/login')

    UserInfo(request, context)

    if 'User' in request.GET and 'Bank' in request.GET:
        Result = base.Bank().RemoveBank(request.GET['User'], request.GET['Bank'])
        context['Message'] = Result['Message']
    return redirect('/profile/bank/?remstat='+str(Result['Status']))


def CheckLogin(request):
    Status = False
    if 'UserId' not in request.session:
        return redirect('/authentication/login/')
    else:
        Status = False
    return Status


def DisplayUpload(request):
    if 'UserId' not in request.session:
        return redirect('/authentication/login')

    Data = {"ErrorMessage": [], "UserId": request.session['UserId']}

    UserInfo(request, Data)

    if 'HTTP_REFERER' in request.META:
        Data['Referrer'] = request.META['HTTP_REFERER']

    Result = base.Edit().GetInfo(request.session['UserId'])
    if 'DP' in Result:
        Data['DP'] = "." + Result['DP']
        Data['DP'] = "/static/" + APP_NAME + "/Uploads/Display/" + str(request.session['UserId']) + Result['DP']
    if request.method == 'POST':
        FileData = {}
        if 'DP' in request.FILES:
            DP = request.FILES.getlist('DP')
            FileData['DP'] = DP
        else:
            Data["ErrorMessage"].append("Please Upload a picture")

        if len(Data['ErrorMessage']) == 0:
            for Key in FileData:
                for file in FileData[Key]:
                    filename = request.session['UserId']
                    base_path = settings.PROFILEPATH
                    ext = str(file).split(sep=".")[-1].lower()
                    filename = str(filename) + "." + ext

                    if ext not in ['jpg', 'png', 'jpeg']:
                        Data[
                            "ErrorMessage"] += "Image format not supported, " \
                                               "Please make sure image is of the type .jpg,.jpeg or png."
                    else:
                        if not settings.LOCAL_UPLOAD:
                            rs = AdminUtilities().UploadToS3(file, filename, base_path)
                            print(rs)
                        else:
                            with open(base_path+filename, 'wb+') as destination:
                                for chunk in file.chunks():
                                    destination.write(chunk)
            return redirect('Profile:index')
    return render(request, 'Profile/Display.html', Data)

