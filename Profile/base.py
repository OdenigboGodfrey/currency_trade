from Authentication.models import User, Banks as UsersBank
from django.shortcuts import get_object_or_404, get_list_or_404
from CTAdmin.base import KYC
from django.conf import settings
import boto3
import botocore
from botocore.client import Config


class Edit:

    def GetInfo(self, Id):
        Data = {'Message': ''}
        try:
            UserObject = get_object_or_404(User, pk=Id)
            Data['FullName'] = UserObject.FullName
            Data['State'] = UserObject.State
            Data['Country'] = UserObject.Country
            Data['DOB'] = UserObject.DOB
            Data['PhoneNo'] = UserObject.PhoneNumber
            Data['Sex'] = UserObject.Sex
            Data['Email'] = UserObject.Email
            Data['AccountNumber'] = UserObject.AccountNumber
            if not settings.LOCAL_UPLOAD:
                s3 = boto3.resource('s3',
                                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                    config=Config(signature_version='s3v4'))
                for ext in settings.ACCEPTED_IMAGE_TYPES:
                    try:
                        ImgPath = 'static/' + settings.PROFILEPATH + str(Id) + '.' + ext
                        print(ImgPath)

                        s3.Object(settings.AWS_STORAGE_BUCKET_NAME, ImgPath).load()
                    except botocore.exceptions.ClientError as e:
                        if e.response['Error']['Code'] == "404":
                            continue
                        else:
                            print(e)
                            raise Exception()

                    Data['DP'] = ext
                    Data['Status'] = True
                    break
            else:
                UserDP = KYC().CheckIfFileExist(settings.PROFILEPATH, Id)
                if UserDP['Status']:
                    Data['DP'] = UserDP['Ext']
                Data['Status'] = True
        except Exception as e:
            print(e)
            Data['Status'] = False
            Data['Message'] = "Failed to get User's Info"
        return Data

    def PostInfo(self, PostRequest, Id):
        UserObject = get_object_or_404(User, pk=Id)
        if 'FullName' in PostRequest and PostRequest['FullName']:
            UserObject.FullName = PostRequest['FullName']
        if 'State' in PostRequest and PostRequest['State']:
            UserObject.State = PostRequest['State']
        if 'Country' in PostRequest and PostRequest['Country']:
            UserObject.Country = PostRequest['Country']
        if 'DOB' in PostRequest and PostRequest['DOB']:
            UserObject.DOB = PostRequest['DOB']
        if 'PhoneNo' in PostRequest and PostRequest['PhoneNo']:
            UserObject.PhoneNumber = PostRequest['PhoneNo']
        if 'Sex' in PostRequest and PostRequest['Sex']:
            UserObject.Sex = PostRequest['Sex']

        UserObject.save()


class Bank:
    def AddBank(self, PostRequest, UserId):
        BankObject = UsersBank()
        BankObject.BankName = PostRequest['BankName']
        BankObject.AccountName = PostRequest['AccountName']
        BankObject.AccountNumber = PostRequest['AccountNumber']
        BankObject.UserId = UserId

        BankObject.save()
        BankObject = get_list_or_404(UsersBank, UserId=UserId)

        return {'BankObject': BankObject}

    def Banks(self, UserId):
        Data = {'Message': []}
        try:
            BankObject = get_list_or_404(UsersBank, UserId=UserId, IsActive=True)
            Data['BankObject'] = BankObject
        except Exception:
            Data['Message'].append("You don't have any banks saved yet.")
        return Data

    def RemoveBank(self, UserId, BankId):
        Data = {'Message': ''}
        try:
            BankObject = get_object_or_404(UsersBank, UserId=UserId, pk=BankId)
            BankObject.IsActive = False
            BankObject.save()
            Data['Message'] = 'Bank Successfully removed.'
            Data['Status'] = True
        except Exception:
            Data['Message'] = "Bank not found"
            Data['Status'] = False
        return Data

