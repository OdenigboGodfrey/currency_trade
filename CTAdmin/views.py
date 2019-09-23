from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from . import base
from Transactions.base import TransactionBaseClass as TransactionBase
import os
from datetime import datetime
import hashlib

app_name = "CTAdmin"


def GetStarInfo(request):
    return {"Star": int(request.session['Star']),
            'KY_ADMIN': int(settings.KY_ADMIN),
            'T_ADMIN': int(settings.T_ADMIN),
            'S_ADMIN': int(settings.S_ADMIN)
            }


def MessagesHandler(request, Context, Result, type="Add", PostExtras={}):
    if type == "Add":
        Context['Status'] = Result['Status']
    elif type == "Get":
        Context['Type'] = "Get"


def index(request):
    return redirect('CTAdmin:MyTasks')


def RegisterAdmin(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')
    
    context = {'Message': [], 'RegisterAdmin': True, 'show': True}
    context.update(GetStarInfo(request))
    if int(request.session['Star']) == int(settings.S_ADMIN):
        if request.method == 'POST':
            Result = base.AdminBaseClass().Signup(request.POST)
            if Result is not None:
                if Result['Status']:
                    context['Message'].append('New admin created successfully')
                else:
                    context['Message'].append('Failed to create Admin, please try again.')
    else:
        context['Message'].append("Unauthorised Access")
    return render(request, 'CTAdmin/RegisterAdmin.html', context)


def Login(request):
    if 'AdminId' in request.session:
        return redirect('CTAdmin:index')

    context = {'ErrorMessage': []}
    base.Tasks().SetDefaultTaskAssignmentType()
    if request.method == 'POST':
        Result = base.Login().Handler(request.POST)
        context['Status'] = Result['Status']
        if Result['Status']:
            if 'AdminId' not in request.session:
                request.session['AdminId'] = Result['AdminId']
                request.session['Star'] = Result['Star']
                request.session['AssignmentType'] = base.Tasks().GetTaskAssignmentType().Type
            return redirect('CTAdmin:MyTasks')
        else:
            context['ErrorMessage'].append(Result['ErrorMessage'])
    return render(request, 'CTAdmin/Login.html', context)


def Logout(request):
    if 'AdminId' in request.session:
        del request.session['AdminId']
    return redirect('CTAdmin:Login')


def AssignTask(request, TaskId):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'Assign': True, 'show': True}
    context.update(GetStarInfo(request))

    if 'KYC' in request.GET:
        Result = base.AdminBaseClass().GetAdmins(type='KYC')
        context['Admins'] = Result
        context['KYC'] = True
    elif 'Trans' in request.GET:
        Result = base.AdminBaseClass().GetAdmins(type='Trans')
        context['Admins'] = Result
        context['Trans'] = True
    else:
        Result = base.AdminBaseClass().GetAdmins()
        context['Admins'] = Result
        context['All'] = True

    if request.method == "POST":
        if 'KYC' in request.GET:
            if 'Admin' in request.POST:
                AdminId = request.POST['Admin']

                Result = base.KYC().Assign(AdminId, TaskId)
                if Result:
                    return redirect('CTAdmin:KYCTasks')
                else:
                    context['Message'].append(Result['Message'])

        elif 'Trans' in request.GET:
            if 'Admin' in request.POST:
                AdminId = request.POST['Admin']
                if int(AdminId) != 0:
                    Result = base.Transactions().Assign(TaskId, AdminId, True)
                    if Result['Status']:
                        return redirect('CTAdmin:TransactionTasks')
                    else:
                        context['Message'].append(Result['Message'])
                else:
                    context['Message'].append("Invalid request.")
        else:
            context['Message'].append("Invalid request.")
    return render(request, 'CTAdmin/Assign.html', context)


def ChangeLevel(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {"Message": [], 'ChangeLevel': True, 'show': True}
    context.update(GetStarInfo(request))
    if request.method == 'POST':
        base.AdminBaseClass().ChangeLevel(request.POST['AdminEmail'], request.POST['Star'])
        context['Message'].append("Level Changed Successfully.")
    return render(request, 'CTAdmin/ChangeLevel.html', context)


def KYCTasks(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = GetStarInfo(request)
    context.update({'type': 'KYC'})
    context['KYCTasks'] = True
    Result = base.KYC().GetTasks()
    if 'KYCObject' in Result:
        context['KYCObject'] = Result['KYCObject']

    return render(request, 'CTAdmin/Tasks.html', context)


def TransactionTasks(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = GetStarInfo(request)
    context.update({'type': 'Trade'})
    context['TransactionTasks'] = True

    context['TransObject'] = base.Transactions().GetUnassigned()

    return render(request, 'CTAdmin/Tasks.html', context)


def MyTasks(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'MyTasks': True, 'show': True}
    context.update(GetStarInfo(request))

    if 'Task' not in request.GET:
        if 'stat' in request.GET and int(request.GET['stat']) != -1:
            context['Message'].append("Task #" + request.GET['stat'] + " Completed.")
        elif 'stat' in request.GET and int(request.GET['stat']) != -1:
            context['Message'].append("An error occurred. Please try again.")
        Result = base.AdminBaseClass().MyTasks(int(request.session['AdminId']), int(request.session['Star']))
        context.update(Result)
    elif 'Task' in request.GET:
        if int(request.session['Star']) == settings.KY_ADMIN or int(request.session['Star']) == settings.S_ADMIN:
            context['KYCFetchSingleTask'] = True
            Result = base.KYC().GetKYCFiles(request.GET['Task'])
            context.update(Result)
        else:
            context["Message"].append("Unauthorized Action.")

    if request.method == 'POST':
        MyTasksURL = reverse('CTAdmin:MyTasks', current_app=request.resolver_match.namespace)
        if 'Task' not in request.GET:
            return redirect(MyTasksURL + "?stat=-1")
        else:
            if int(request.session['Star']) == settings.KY_ADMIN or int(request.session['Star']) == settings.S_ADMIN:
                Action = True
                RejectionMessage = "n/a"
                if int(request.POST['Action']) == 1:
                    Action = False
                    RejectionMessage = request.POST['RejectionMessage']
                Result = base.KYC().ApproveKYC(request.session['AdminId'], request.GET['Task'], Action, RejectionMessage)
                if Result['Status']:
                    return redirect(MyTasksURL + "?stat=" + request.GET['Task'])
            else:
                context["Message"].append("Unauthorized Action.")
    return render(request, 'CTAdmin/MyTasks.html', context)


def Transaction(request, AdId):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'IsAdmin': True, 'Admin_Transaction': True, 'show': True}
    context.update(GetStarInfo(request))
    context.update(TransactionBase().GetNegotiations(AdId))
    if 'mid' in request.GET:
        if int(request.GET['mid']) == 0:
            context['Message'].append("Payment Approved Successfully.")
        elif int(request.GET['mid']) == 1:
            context['Message'].append("File rejected successfully.")

    """get this trade ad information"""
    context.update(TransactionBase().GetAdById(AdId))
    """get buyer/seller info if paid"""
    context.update(TransactionBase().GetPaid(AdId))
    context['AdId'] = AdId
    return render(request, 'Transactions/Negotiations.html', context)


def Approve(request, AdId):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'Approve': True, 'show': True}
    context.update(GetStarInfo(request))

    if 'Seller' not in request.GET and 'Buyer' not in request.GET:
        return redirect('CTAdmin:MyTasks')
    else:
        if request.method == 'POST':
            Message = 'n/a'
            if 'RejectionMessage' in request.POST:
                Message = request.POST['RejectionMessage']
            if 'Seller' in request.GET:
                Result = base.Transactions().Approve(AdId, request.GET['Seller'], request.POST['Action'],
                                                     request.session['AdminId'], Message=Message)
            elif 'Buyer' in request.GET:
                Result = base.Transactions().Approve(AdId, request.GET['Buyer'], request.POST['Action'],
                                                     request.session['AdminId'], False, Message=Message)

            if Result['Status']:
                URL = reverse('CTAdmin:Transaction', kwargs={'AdId': AdId}, current_app=request.resolver_match.namespace)
                if 'Action' in Result:
                    return redirect(URL + "?mid=1")
                else:
                    return redirect(URL + "?mid=0")
            else:
                context['Message'].append("Payment approval failed.")

        context['URL'] = request.get_full_path()
        if 'Seller' in request.GET:
            Result = base.Transactions().GetFiles(AdId, request.GET['Seller'])
        elif 'Buyer' in request.GET:
            Result = base.Transactions().GetFiles(AdId, request.GET['Buyer'])

        if Result['Status']:
            context['Files'] = []

            index = 0
            for File in Result['TFO']:
                StringPath = settings.TRANSACTIONPATH + File.FileName
                Res = base.Utilities().CheckIfFileExist([StringPath])
                if settings.LOCAL_UPLOAD:
                    context['Files'].append({'index': index, 'Status': Res[StringPath]['Status'],
                                             'FileName': "/static/" + app_name + "/Uploads/Transactions/"
                                                         + File.FileName, 'UserInfo': File.UploadedBy})
                else:
                    context['Files'].append({'index': index, 'Status': Res[StringPath]['Status'],
                                             'FileName': settings.STATIC_URL + app_name + "/Uploads/Transactions/"
                                                         + File.FileName, 'UserInfo': File.UploadedBy})
                index = index + 1
    return render(request, 'CTAdmin/Approve.html', context)


def Completed(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'Completed': True}
    context.update(GetStarInfo(request))
    if 'AdId' in request.GET:
        """ requesting particular ad"""
        context.update(base.Transactions().GetAdminCompleted(request.session['AdminId'], request.GET['AdId']))
    else:
        context.update(base.Transactions().GetAdminCompleted(request.session['AdminId']))

    return render(request, 'CTAdmin/Completed.html', context)


def CTFee(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'CTFee': True, 'show': True}
    context.update(GetStarInfo(request))
    if request.method == 'POST':
        if int(request.session['Star']) == settings.S_ADMIN:
            try:
                """ cast percentage to float"""
                Result = base.AdminBaseClass().SetCTFee(float(request.POST['Percentage']), request.session['AdminId'])
                context['CTFeeObject'] = Result
            except Exception as e:
                context['Message'].append('Please enter a valid CTFee.')
        else:
            context['Message'].append('Invalid request.')
    return render(request, 'CTAdmin/CTFee.html', context)


def Close(request, AdId):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'Close': True, 'show': True}
    context.update(GetStarInfo(request))

    if request.method == 'POST':
        Message='n/a'
        if 'Reason' in request.POST:
            Message = request.POST['Reason']
        TransactionBase().Close(request.session['Admin'], AdId, True, Message)
    return render(request, 'CTAdmin/Close.html', context)


def Paid(request, AdId):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'Paid': True, 'show': True}
    context.update(GetStarInfo(request))

    if request.method == 'POST':
        if 'UserId' in request.GET:
            UserId = request.GET['UserId']
            filename = hashlib.sha1(datetime.now().__str__().encode()).hexdigest()
            base_path = settings.TRANSACTIONPATH_ADMIN
            ext = os.path.splitext(str(request.FILES['file']))[1]
            Completed = False

            if ext[1::] not in settings.ACCEPTED_IMAGE_TYPES:
                context["Message"].append(
                    "Image format not supported, Please make sure image is of the type jpg, jpeg or png.")
            else:
                if not settings.LOCAL_UPLOAD:
                    Completed = base.Utilities().UploadToS3(request.FILES['file'], filename, base_path)
                else:
                    if 'file' not in request.FILES:
                        context['Message'].append('Please upload a file.')
                    else:
                        """upload file first then save"""

                        if not os.path.exists(base_path):
                            os.mkdir(base_path)

                        filename = filename + "." + ext[1::]

                        if ext[1::] not in ['jpg', 'png', 'jpeg']:
                            context["Message"].append(
                                "Image format not supported, Please make sure image is of the type jpg, jpeg or png.")
                        else:
                            file = request.FILES['file']
                            with open(base_path+filename, 'wb+') as destination:
                                for chunk in file.chunks():
                                    destination.write(chunk)
                            Completed = True

                if Completed:
                    if not base.Transactions().Paid(filename + "." + ext, AdId, UserId, request.session['AdminId']) and not Completed:
                        context['Message'].append("Unauthorised Action.")
                    else:
                        context['Message'].append("File uploaded.")
                else:
                    context['Message'].append("File upload failed.")
        else:
            context['Message'].append("Invalid request.")
    return render(request, 'CTAdmin/Paid.html', context)


def Deactivate(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'Deactivate': True, 'show': True}
    context.update(GetStarInfo(request))

    if request.method == 'POST':
        if request.POST['AdminEmail'] or request.POST['Admin']:
            AdminId = int(request.POST['Admin'])
            if request.POST['AdminEmail'] and AdminId == 0:
                AdminId = base.AdminBaseClass().GetAdminByEmail(request.POST['AdminEmail'])
                if 'Id' in AdminId and AdminId['Id'] == 0:
                    context['Message'].append(AdminId['Message'])
                else:
                    AdminId = AdminId.pk

            if AdminId == int(request.session['AdminId']) or AdminId == 0:
                context['Message'].append("Invalid request.")
            else:
                Result = base.AdminBaseClass().Deactivate(AdminId, request.session['AdminId'])
                if Result:
                    context['Message'].append("Admin deactivated.")
                else:
                    context['Message'].append("Failed to deactivate admin.")

    Result = base.AdminBaseClass().GetAdmins()

    if Result is not False:
        context['Admins'] = Result

    return render(request, 'CTAdmin/Assign.html', context)


def EagleWatch(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'EagleWatch': True}
    context.update(GetStarInfo(request))

    if int(request.session['Star']) == settings.S_ADMIN:
        context['Admins'] = base.AdminBaseClass().GetAdmins()
        context['type'] = "KYC"
        if request.method == 'POST':
            Type = request.POST['type']
            context['type'] = Type
            if request.POST['Email'] or int(request.POST['Admin']) != 0:
                if request.POST['Email']:
                    """Get this specific admin's task info"""
                    Result = base.AdminBaseClass().EagleWatch(Star=request.session['Star'],
                                                              Email=request.POST['Email'])
                elif request.POST['Admin']:
                    """"""
                    Result = base.AdminBaseClass().EagleWatch(Star=request.session['Star'],
                                                              Id=request.POST['Admin'])
            else:
                Result = base.AdminBaseClass().EagleWatch(Star=request.session['Star'], Type=Type)
        else:
            Result = base.AdminBaseClass().EagleWatch(request.session['Star'], Type='KYC')
        context.update(Result)
    else:
        return redirect('CTAdmin:MyTasks')
    return render(request, 'CTAdmin/EagleWatch.html', context)


def UPReferrers(request):
    # Unpaid referrers
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')

    context = {'Message': [], 'show': True}
    if 'R' in request.GET and 'AdId' in request.GET:
        """update payment status"""
        Result = base.Transactions().PayReferrer(request.session['AdminId'], request.GET['R'], request.GET['AdId'])

        context['Message'].append(Result['Message'])
    context.update(base.Transactions().GetUnpaidReferrers(request.session['AdminId']))
    return render(request, 'CTAdmin/UnpaidReferrers.html', context)


def AssignmentType(request):
    if 'AdminId' not in request.session:
        return redirect('CTAdmin:Login')
    context = {'Type': ['Polling', 'Queue']}
    if request.method == 'POST':
        """"""
        base.Tasks().SetTaskAssignmentType(request.POST['Type'], request.session['AdminId'])
    return render(request, 'CTAdmin/AssignmentType.html', context)

