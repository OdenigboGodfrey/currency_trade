import base64
from builtins import Exception, print
from datetime import datetime
from .models import *
import hashlib
from django.shortcuts import get_object_or_404, get_list_or_404
import random
from twilio.rest import Client
from CTAdmin import base as AdminUtilities
from CTAdmin.models import KYC, KYCLogs
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
import django.utils.http as UrlEncode
from sendgrid import sendgrid

PASSWORD_SALT = '$.2@7!29^Bc;a)f2:144f6$@_)5196b01.%6.FdD04dA0%'
TWOFACTORCODELENGTH = 6
ENCODE_KEY = '!@#$%'


class Login:
    def Handler(self, email, password):
        UtilitiesObject = Utilities()
        Data = {}
        UserObject = None
        Message = 'n/a'
        try:
            UserObject = get_object_or_404(User, Email=email, Password=UtilitiesObject.hash_password(password))
            if not UserObject.AccountNumber:
                UserObject = None
                Message = 'Two Factor verification not done.'
        except Exception as e:
            """"""

        if UserObject is not None:
            Data["Message"] = "Login Successful"
            Data["Status"] = True
            Data["UserId"] = UserObject.id
            Data["AccountNumber"] = UserObject.AccountNumber
            Data['FullName'] = UserObject.FullName
            Data['AccountType'] = UserObject.AccountType
            Data['Email'] = UserObject.Email
            Data['PhoneNumber'] = UserObject.PhoneNumber
        else:
            if Message == 'n/a':
                Data["Message"] = "Email or password incorrect"
            else:
                Data['Message'] = Message
            Data["Status"] = False
        return Data

    def MarkKYCLogsAsRead(self, Id):
        try:
            KYCLogsObject = get_list_or_404(KYCLogs, UserId=Id, UserNotified=False)
            for Log in KYCLogsObject:
                Log.UserNotified = True
                Log.save()
            return {'Status': True}
        except Exception as e:
            return {"Error": e, 'Status': False}

    def CheckKYC(self, Id):
        Data = {}
        try:
            KYCObject = get_object_or_404(KYC, UserId=Id)
            Data["All"] = 0
            Data['KYCStatus'] = KYCObject.Status
        except:
            """ KYC not done """
            Data["All"] = 4
            Data['KYCStatus'] = 0

        return Data

    def HandleKYC(self, Id):
        UserObject = User.objects.get(pk=Id)
        try:
            KYCObject = get_object_or_404(KYC, UserId=Id)
            Log = UserObject.AccountNumber + " updated files for KYC Review"
        except:
            KYCObject = KYC()
            Log = UserObject.AccountNumber + " uploaded files for KYC review."

        KYCObject.UserId = UserObject
        KYCObject.IsKYCDone = True
        KYCObject.save()

        LogObject = KYCLogs()
        LogObject.Log = Log

        LogObject.KYCId = KYC.objects.get(pk=KYCObject.pk)
        LogObject.save()


class Signup:
    def Handler(self, PostRequest, R='n/a'):
        Data = {"ErrorMessage": []}
        IsUnique = True

        try:
            """ check if email is alrwady used to register"""
            User.objects.get(Email=PostRequest['Email'])
            Data['ErrorMessage'].append("Email already registered. please reset your password if forgotten.")
            IsUnique = False
        except:
            """"""

        try:
            """ checki if phone no is already registered"""
            User.objects.get(PhoneNumber=PostRequest['PhoneNumber'])
            Data['ErrorMessage'].append("Phone Number Already registered. Please use a different number")
            IsUnique = False
        except:
            """"""

        if IsUnique:
            try:
                UserObject = User()

                UserObject.FullName = PostRequest['FullName']
                UserObject.Email = PostRequest['Email']
                UserObject.Sex = PostRequest['Sex']
                UserObject.State = PostRequest['State']
                UserObject.Country = PostRequest['Country']
                UserObject.DOB = PostRequest['DOB']
                UserObject.Password = Utilities().hash_password(PostRequest['PasswordConfirmation'])
                UserObject.PhoneNumber = PostRequest['PhoneNumber']
                UserObject.OnlineOffline = True
                UserObject.AccountType = PostRequest['AccountType']
                if R != 'n/a':
                    UserObject.Referrer = User.objects.get(AccountNumber=R)

                UserObject.save()

                UserObject = get_object_or_404(User, Email=PostRequest['Email'], Password=Utilities().hash_password(PostRequest['PasswordConfirmation']))
                Result = Utilities().Do2FA(UserObject)

                Data.update({"UserObject": UserObject, "Result": Result})
            except Exception as e:
                print(e)
                Data['ErrorMessage'].append('Failed to save information.')

        return Data

    def RollBack(self, UserObject):
        User.objects.filter(pk=UserObject.pk).delete()
        return True

    def ResetPassword(self, Password, Id, IsFromProfile = False):
        Data = {}
        UserObject = get_object_or_404(User, pk=Id)
        if not UserObject.IsVerified and not IsFromProfile:
            UserObject.Password = Utilities().hash_password(Password)
            UserObject.IsVerified = True
            UserObject.save()
            Data["Status"] = True
            Data["ErrorMessage"] = "n/a"
        elif UserObject.IsVerified and IsFromProfile:
            UserObject.Password = Utilities().hash_password(Password)
            UserObject.save()
            Data["Status"] = True
            Data["ErrorMessage"] = "n/a"
        else:
            Data["Status"] = False
            Data["ErrorMessage"] = "Unverified attempt to reset password."
        return Data

    def VerifyOldPassword(self, OldPassword, Id):
        UserObject = get_object_or_404(User, pk=Id)
        if UserObject.Password == Utilities().hash_password(password=OldPassword):
            return 2
        else:
            return 0


class Utilities:
    def TwoFactor(self):
        TwoFaNumbers = ''
        for x in range(TWOFACTORCODELENGTH):
            TwoFaNumbers += str(random.randint(0, 9))
        return TwoFaNumbers

    def hash_password(self, password):
        return hashlib.md5(
            PASSWORD_SALT.encode() + (hashlib.sha1(password.encode()).hexdigest()).encode()).hexdigest()

    def Do2FA(self,  User_Object=None, Email=None):
        Data = {}
        try:
            if Email is not None:
                UserObject = User.objects.get(Email=Email)

                if UserObject is None:
                    raise Exception
            elif User_Object is not None:
                UserObject = User_Object
            else:
                raise Exception()

            GeneratedTwoFactor = self.TwoFactor()

            UserObject.TwoFactor = GeneratedTwoFactor
            UserObject.IsVerified = False
            UserObject.TwoFactorTime = datetime.now()
            UserObject.save()

            Data["Status"] = True
            Data["UserId"] = UserObject.pk

            # handle messaging and emailing here
            UsersPhoneNo = UserObject.PhoneNumber

            Result = self.send_sms(phone=UsersPhoneNo, message="Verification code is " + str(GeneratedTwoFactor))
            Data["MessageStatus"] = Result

            Result = self.SendMail([UserObject.Email], "Verification code is " + str(GeneratedTwoFactor))
            Data['EmailStatus'] = Result
            print('2fa Done')
        except Exception as e:
            print(e)
            Data['Status'] = False
            Data['EmailStatus'] = False
            Data["MessageStatus"] = False

        return Data

    def Verify2fa(self, TwoFactorValue, Id, IsFromSignup = False):
        UserObject = get_object_or_404(User, pk=Id)

        if UserObject.TwoFactor == TwoFactorValue:
            UserObject.IsVerified = IsFromSignup
            UserObject.save()
            if IsFromSignup:
                AdminUtilities.Utilities().GenerateCTAccountNumber(Id)
            return True
        else:
            return False

    def send_sms(self, phone, message):
        account_sid = 'AC12b068ccfbadde1d5d87001eea307a93'
        auth_token = 'dded41669b0640233c2e26d786993752'
        client = Client(account_sid, auth_token)
        #         currency_trade
        sender = '447480780189'
        try:
            Rr = client.messages.create(from_=sender, body=message, to=phone, provide_feedback=False)
            aa = Rr
            print(aa.__dict__, 'Rr')
            return True
        except Exception as e:
            print(e, 'sms Error')
            return False
    
    def SendMail(self, Email, Message):
        try:
            send_mail('currency_trade ', Message, 'no-reply@CT.com', Email, fail_silently=True)
            return True
        except Exception as e:
            print(e)
            return False

    def GetReferrerCode(self, AccountNumber):
        enc = []
        key = ENCODE_KEY
        for i in range(len(AccountNumber)):
            key_c = key[i % len(key)]
            enc_c = chr((ord(AccountNumber[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        return base64.urlsafe_b64encode("".join(enc).encode()).decode()

    def DecodeReferrerCode(self, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc).decode()
        key = ENCODE_KEY
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)


