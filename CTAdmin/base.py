from builtins import print

from django.shortcuts import get_object_or_404, get_list_or_404
import random
from Authentication.models import User
from Authentication import base as UserBase
from .models import *
from django.conf import settings
import os
from django.db.models import Q
from datetime import datetime
from Transactions.models import Transactions as UserTransactions, TransactionFile, Negotiations, BulkTransaction, AffiliatePayment
import Transactions as TransactionBase
from CTAdmin.models import CTFee as TaxCTFee, TransactionFile as AdminTransactionFile
import boto3
from botocore.client import Config

CTKYC = KYC
RTL = ReviewedTransactionLog


class AdminBaseClass:

    def Signup(self,PostRequest):
        AdminObject = Admins()
        AdminObject.PhoneNumber = PostRequest['AdminPhoneNo']
        AdminObject.Email = PostRequest['AdminEmail']
        AdminObject.Password = UserBase.Utilities().hash_password(PostRequest['AdminConfirmPassword'])
        AdminObject.FullName = PostRequest['AdminFullName']
        AdminObject.Star = 0

        AdminObject.save()
        AdminObject = get_object_or_404(Admins, Email=PostRequest['AdminEmail'],
                                        Password=UserBase.Utilities().hash_password(PostRequest['AdminConfirmPassword']))

        Data = {'Status': True, 'AdminId': AdminObject.pk}

        if AdminObject is not None:
            Data['Status'] = False

        return Data

    def ChangeLevel(self, Email, Star):
        AdminObject = get_object_or_404(Admins, Email=Email)
        AdminObject.Star = Star
        AdminObject.save()

        AdminObject = get_object_or_404(Admins, Email=Email)
        Data = {'Status': False}

        if AdminObject.Star == Star:
            Data['Status'] = True
            Data['AdminObject'] = AdminObject
            """Re assign tasks based on total no of tasks"""
        return Data

    def GetAdmins(self, type='n/a', ExcludeS_ADMINs=False):
        try:
            if type == 'n/a':
                if ExcludeS_ADMINs:
                    AdminObject = get_list_or_404(Admins, (~Q(Star=settings.S_ADMIN)), IsActive=True)
                else:
                    AdminObject = get_list_or_404(Admins, IsActive=True)
            elif type == 'KYC':
                if ExcludeS_ADMINs:
                    AdminObject = get_list_or_404(Admins, Star=settings.KY_ADMIN, IsActive=True)
                else:
                    AdminObject = get_list_or_404(Admins, (~Q(Star=settings.T_ADMIN)), IsActive=True)
            elif type == 'Trans':
                if ExcludeS_ADMINs:
                    AdminObject = get_list_or_404(Admins, Star=settings.T_ADMIN, IsActive=True)
                else:
                    AdminObject = get_list_or_404(Admins, (~Q(Star=settings.KY_ADMIN)), IsActive=True)

            return AdminObject
        except:
            return False

    def GetAdminByEmail(self, Email):
        try:
            AdminObject = get_list_or_404(Admins, Email=Email)
            return AdminObject
        except:
            return {'Id': 0, 'Message': "Failed to get an Admin With that Email."}

    def MyTasks(self, Id, Star):
        Data = {"Count": 0}

        if Star == settings.KY_ADMIN or Star == settings.S_ADMIN:
            try:
                KYCObject = get_list_or_404(CTKYC, IsApproved=False, HandledBy=Id)
                Data['KYCObject'] = KYCObject
                Data['Count'] = len(KYCObject)
                Data['KYCFetchAll'] = True
            except Exception:
                Data['Message'] = ["No KYC Tasks assigned yet."]
                Data['KYCFetchAll'] = False

        if Star == settings.T_ADMIN or Star == settings.S_ADMIN:
            try:
                TransactionsObject = get_list_or_404(UserTransactions, HandledBy=Id, Buyer=None)
                Data['TransactionsObject'] = TransactionsObject
                Data['Count'] = len(TransactionsObject)
                Data['TransactionsFetchAll'] = True
            except:
                Data['Message'] = ["No Transaction Tasks assigned yet."]
                Data['TransactionsFetchAll'] = False

        return Data

    def SetCTFee(self, Percentage, Id):
        TaxCTFeeObject = TaxCTFee()
        TaxCTFeeObject.Percentage = Percentage
        TaxCTFeeObject.AdminId = Admins.objects.get(pk=Id)
        TaxCTFeeObject.save()

        return self.GetCTFee()

    def GetCTFee(self, Id=0):
        try:
            if Id != 0:
                """ Get tax CTFees saved by current admin"""
                TaxCTFeeObject = TaxCTFee.objects.filter(AdminId=Id).order_by('-id')
            else:
                TaxCTFeeObject = TaxCTFee.objects.all().order_by('-id').first()
            return TaxCTFeeObject.Percentage
        except AttributeError as e:
            """ failed to get fee"""
            CTFeeObject = TaxCTFee()
            CTFeeObject.Percentage = 3

            CTFeeObject.save()
            return 3.0


    def Deactivate(self, Id, S_AdminId):
        try:
            AdminObject = Admins.objects.get(pk=Id)
            AdminObject.IsActive = False
            AdminObject.save()

            AdminLogObject = AdminLog()
            AdminLogObject.LogContent = "Admin #" + str(S_AdminId) + " deativated Admin #" + str(Id) + "."
            AdminLogObject.AdminId = Admins.objects.get(pk=S_AdminId)
            AdminLogObject.save()
            return True
        except:
            return False

    def EagleWatch(self, Star, Type='n/a', Email='n/a', Id=0, AdminStar=-1):
        """
            Star -> Super admin star used for authorization
            AdminStar -> Current Admin being watched Star
        """
        if int(Star) != settings.S_ADMIN:
            return {'Status': False, 'Message': 'Invalid request.'}
        else:
            AdminId = 0
            if Email != 'n/a':
                AdminId = self.GetAdminByEmail(Email)
                if AdminId['Id'] == 0:
                    return {'Status': False, 'Message': AdminId['Message']}
                else:
                    AdminId = AdminId.pk
                    AdminStar = AdminId.Star

            if Id != 0:
                AdminObject = Admins.objects.filter(pk=Id).first()
                AdminId = Id
                AdminStar = AdminObject.Star

            Data = {}

            if Type == 'KYC' or int(AdminStar) == settings.KY_ADMIN or int(AdminStar) == settings.S_ADMIN:
                Data.update({'KYCsObject': []})
                try:
                    if AdminId != 0:
                        KYCObjects = CTKYC.objects.filter(~Q(Status=2), HandledBy=AdminId)
                    else:
                        """ get all open tasks"""
                        KYCObjects = CTKYC.objects.filter(~Q(Status=2), ~Q(HandledBy=None))
                    for Object in KYCObjects:
                        KYCObject = {'KYC': Object}
                        KYCObject['Log'] = KYC().GetLogs(Object.pk, True)
                        Data['KYCsObject'].append(KYCObject)

                    if len(Data['KYCsObject']) == 0:
                        Data['Status'] = False
                        Data['Message'] = "No  KYC information."
                        del Data['KYCsObject']
                    else:
                        Data['Status'] = True
                except:
                    """"""
                    Data['Status'] = False
                    Data['Message'] = "Failed to get KYC information."

            if Type == 'Transaction' or int(AdminStar) == settings.T_ADMIN or int(AdminStar) == settings.S_ADMIN:
                Data.update({'TransactionsObject': []})

                try:
                    if AdminId != 0:
                        TransactionsObject = UserTransactions.objects.filter(HandledBy=AdminId, Buyer=None).order_by('-id')
                    else:
                        TransactionsObject = UserTransactions.objects.filter((~Q(HandledBy=None)), Buyer=None).order_by('-id')

                    for Object in TransactionsObject:
                        """ single transaction """
                        TransactionObject = {'Transaction': Object}
                        TransactionObject['Log'] = Transactions().GetLog(Object.pk, True)
                        Data['TransactionsObject'].append(TransactionObject)

                    if len(Data['TransactionsObject']) == 0:
                        Data['Status'] = False
                        Data['Message'] = "No Transaction information."
                        del Data['TransactionsObject']
                    else:
                        Data['Status'] = True
                except Exception as e:
                    Data['Status'] = False
                    Data['Message'] = "Failed to get Transaction information."

            if Type == 'n/a' and AdminStar == -1:
                if AdminId != 0 and Type == 'n/a':
                    return self.EagleWatch(Star=Star,Id=AdminId, AdminStar=AdminStar)
                else:
                    return {'Status': False, 'Message': 'Invalid request.'}
            return Data


class Login:

    def Handler(self, PostRequest):

        Data = {}
        AdminObject = None

        try:
            AdminObject = get_object_or_404(Admins, Email=PostRequest['Email'],
                                            Password=UserBase.Utilities().hash_password(PostRequest['Password']))

        except Exception as e:
            Data['ErrorMessage'] = 'Email or Password incorrect.'

        if AdminObject is not None:
            Data["Message"] = "Login Successful"
            Data['Status'] = True
            Data['AdminId'] = AdminObject.pk
            Data['Star'] = AdminObject.Star
        else:
            Data['ErrorMessage'] = "Email or password incorrect"
            Data['Status'] = False
        return Data


class KYC:
    """register users kyc for review"""
    def HanldeKYC(self, Id):
        KYCObject = CTKYC()

        KYCObject.IsKYCDone = True
        KYCObject.UserId = User.objects.get(pk=Id)
        KYCObject.save()

    """ approve kyc """
    def ApproveKYC(self, Id, TaskId, IsApproved, RejectionMessage = "n/a"):
        Data = {"Message": ""}
        try:
            KYCObject = get_object_or_404(CTKYC, pk=TaskId)
        except:
            Data['Message'] = "Error fetching KYC for User."
            Data['Status'] = False
            return Data

        KYCObject.IsApproved = IsApproved

        if RejectionMessage != "n/a":
            KYCObject.RejectionMessage = RejectionMessage
            """ 
            Status: -1 = rejected, 0 = waiting, 1 = admin processing, 2 = approved  
            """
            KYCObject.Status = -1

        LogObject = KYCLogs()
        if IsApproved:
            KYCObject.Status = 2
            LogObject.Log = "Admin has approved of your files."

            """register as an admin task completed"""
            Tasks().Complete(Id)

        else:
            KYCObject.Status = -1
            LogObject.Log = "Admin has rejected your files. Reason: " + RejectionMessage

        LogObject.IsAdminAction = True
        LogObject.LogDate = datetime.now()
        LogObject.KYCId = CTKYC.objects.get(pk=KYCObject.pk)

        LogObject.save()
        KYCObject.save()

        Data['Status'] = True

        return Data

    def CheckIfFileExist(self, FilePath, UserId):
        Data = {}
        for ext in settings.A:
            StringPath = settings.BASE_DIR + '\\' + FilePath + str(UserId).replace('/', "\\") + '.' + ext

            if os.path.isfile(StringPath):
                Data['Status'] = True
                Data['Ext'] = ext
                Data['UserId'] = UserId
                """"
                    Strip out the Application name e.g Authentication/static/Authentication/images/ ==  static/Authentication/images/
                """
                SlashIndex = FilePath.find('/')
                FilePath = FilePath[SlashIndex:]
                Data['FileURL'] = FilePath

                Data['Type'] = "Selfie"
                if "Address" in FilePath:
                    Data['Type'] = "Address"
                if "FrontId" in FilePath:
                    Data['Type'] = "Front Id"
                if "BackId" in FilePath:
                    Data['Type'] = "Back Id"
                break
            else:
                Data['Status'] = False
        return Data

    def GetTasks(self):
        Data = {"Message": ""}
        KYCObject = get_list_or_404(CTKYC, IsApproved=False)
        if KYCObject is not None:
            Data['KYCObject'] = []
            for Object in KYCObject:
                """only append unassigned tasks"""
                if not Object.HandledBy:
                    Data['KYCObject'].append(Object)
        else:
            Data['Message'] = 'No KYC Task unassigned.'
        return Data

    def Assign(self, KYCId, Id=0):
        Data = {}
        Log = []
        if Id == 0:
            Result = Utilities().AutoAssignAdmin(IsKYC=True)
            if Result['Status']:
                Id = Result['AdminObject'].pk
                Data['AdminObject'] = Result['AdminObject']

        KYCObject = get_object_or_404(CTKYC, pk=KYCId)

        KYCObject.HandledBy = Admins.objects.get(pk=Id)
        KYCObject.Status = 1
        KYCObject.save()

        """ add to list of tasks"""
        Tasks().Assign(Id, IsKYC=True, TaskId=KYCId)

        if not KYCObject.HandledBy:
            Log.append("Admin has been assigned to process your files.")
        else:
            Log.append("Previous Admin #" + str(KYCObject.HandledBy.pk) + " was unassigned from handling your files")
            Log.append("(Admin Change)A new Admin has been assigned to process your files.")
        for Child in Log:
            LogObject = KYCLogs()
            LogObject.LogDate = datetime.now()
            LogObject.KYCId = CTKYC.objects.get(pk=KYCId)
            LogObject.IsAdminAction = True
            LogObject.Log = Child
            LogObject.save()

        Data['Status'] = True
        return Data

    def GetLogs(self, KYCId, Limit=False):
        Data = {}
        if Limit:
            """ get only most recent log"""
            LogObject = KYCLogs.objects.filter(KYCId=KYCId).first()
            Data['LogObject'] = LogObject
        else:
            """"""
            LogObject = KYCLogs.objects.filter(KYCId=KYCId)
            Data['LogObject'] = LogObject

        Data['Limit'] = Limit
        return Data

    def GetKYCFiles(self, TaskId):
        Data = {"Paths": []}

        KYCObject = get_object_or_404(CTKYC, pk=TaskId)

        Data['Paths'].append(self.CheckIfFileExist(settings.SELFIEPATH, KYCObject.UserId.pk))
        Data['Paths'].append(self.CheckIfFileExist(settings.ADDRESSPATH, KYCObject.UserId.pk))
        Data['Paths'].append(self.CheckIfFileExist(settings.FRONTIDPATH, KYCObject.UserId.pk))
        Data['Paths'].append(self.CheckIfFileExist(settings.BACKIDPATH, KYCObject.UserId.pk))

        return Data


class Transactions:
    def Assign(self, AdId, Id=0, Now=False):
        Data = {}
        Log = []

        try:
            print('here')
            AssignmentType = Tasks().GetTaskAssignmentType()
            TransactionObject = get_object_or_404(UserTransactions, pk=AdId)

            if AssignmentType.Type == "Polling" or Now:
                print(Id)
                if Id == 0 and TransactionObject.HandledBy is None:
                    Result = Utilities().AutoAssignAdmin(IsTransaction=True)
                    if Result['Status']:
                        Id = Result['AdminObject'].pk
                        Data['AdminObject'] = Result['AdminObject']
                    else:
                        Data['Status'] = False
                        Data['Manual'] = True
                        Data['Message'] = "Transaction saved."
                        """ since no admin gotten, leave as unassigned"""
                        return Data

                if not TransactionObject.HandledBy:
                    Log.append("An Admin has been assigned to handle this Transaction")
                else:
                    # Log.append("Admin #" + str(TransactionObject.HandledBy.pk) +
                    #            " has been unassigned from handling this Transaction")
                    Log.append("(Admin Change) A new Admin has been assigned to handle this Transaction")
                TransactionObject.HandledBy = Admins.objects.get(pk=Id)
                TransactionObject.save()
    
                """ add to list of tasks """
                Tasks().Assign(Id, IsTransaction=True, TaskId=AdId)
    
                for Child in Log:
                    RTLObject = RTL()
                    RTLObject.TransactionID = TransactionObject
                    RTLObject.Log = Child
                    RTLObject.IsAdminAction = True
                    RTLObject.save()
    
                Data['Status'] = True
                Data['TransactionObject'] = TransactionObject
            elif AssignmentType.Type == "Queue":
                """"""
        except Exception as e:
            print(e)
            Data['Status'] = False
            Data['Message'] = "Failed to get a transaction with that Id."    
        
        return Data

    def Automate(self, BTID, Now=False):
        """ automate reselling of bulk transactions """
        try:
            BTObject = BulkTransaction.objects.get(pk=BTID)
            Amount = (BTObject.BitsPercentage / 100) * BTObject.Amount

            if BTObject.AmountLeft != 0:
                if not BTObject.Automate and not Now:
                    """"""
                    BTObject.Flag = True
                    BTObject.save()
                    return True

                if Amount > BTObject.AmountLeft:
                    Amount = BTObject.AmountLeft
                BTObject.AmountLeft = BTObject.AmountLeft - Amount

                Result = TransactionBase.base.TransactionBaseClass().NewTradeAd({
                    'Amount': Amount,
                    'ExchangeRate': BTObject.ExchangeRate,
                    'FromCurrency': BTObject.FromCurrency,
                    'ToCurrency': BTObject.ToCurrency,
                    'Negotiable': BTObject.Negotiable,
                    'Seller': BTObject.Seller.pk,
                    'CTFee': ((BTObject.CTFee/100) * Amount),
                    'BTID': BTID},
                    BTObject.Seller.pk)

                if Now and Result['Status']:
                    """ turn flagging off"""
                    BTObject.Flag = False
                BTObject.save()

                return True
            else:
                return False

        except Exception as e:
            return False

    def Approve(self, AdId, UserId, Action, Id, Seller=True, Message='n/a', AssignemntType='n/a'):
        Data = {'Message': []}
        Logs = []
        try:
            if Action:
                Action = 1
            else:
                Action = -1

            TransactionObject = get_object_or_404(UserTransactions, pk=AdId)
            BTObject = None
            if TransactionObject.BTID is not None:
                BTObject = TransactionObject.BTID
            if TransactionObject.HandledBy.pk != Id:
                Data['Message'].append("Unauthorised Action.")
                return Data
            TradeProof = get_object_or_404(TransactionFile, TransactionId=AdId, UploadedBy=UserId)

            UserObject = get_object_or_404(User, pk=UserId)
            NegotiationObject = Negotiations.objects.filter(TransactionsId=AdId, Accepted=True, Paid=True)

            if Action == 1:
                Logs.append("Admin Confirmed " + UserObject.AccountNumber + "'s payment")
                SellerPaid = len(TransactionFile.objects.filter(UploadedBy=TransactionObject.Seller.pk, TransactionId=AdId, Approved=1)) == 1

                if len(NegotiationObject) > 0:
                    BuyerPaid = len(TransactionFile.objects.filter(UploadedBy=NegotiationObject[0].UserId.pk, TransactionId=AdId, Approved=1)) == 1
                else:
                    BuyerPaid = False

                if not Seller and SellerPaid:
                    """Seller has paid, make potential buyer trade buyer"""
                    TransactionObject.Buyer = UserObject
                    TransactionObject.Completed = True
                    Logs.append(UserObject.AccountNumber + " bought " +
                                TransactionObject.Seller.AccountNumber + "'s Trade(Trade Ad #" + str(AdId) + ")")
                    ReviewedTransactionObject = ReviewedTransactions()
                    ReviewedTransactionObject.TransactionID = TransactionObject
                    ReviewedTransactionObject.Status = 2
                    ReviewedTransactionObject.StartDate = TransactionObject.TransactionDate
                    ReviewedTransactionObject.HandledBy = TransactionObject.HandledBy
                    ReviewedTransactionObject.save()

                    """ mark this task as completed and handle next task assignment """
                    Tasks().Complete(TransactionObject.HandledBy.pk)
                    if AssignemntType == "Queue":
                        """ get unassigned Tasks"""
                        Unassigned = self.GetUnassigned()
                        Result = self.Assign(Unassigned[0].pk, TransactionObject.HandledBy.pk, True)
                        if not Result['Status']:
                            print('Failed to queue')

                    """ handle selling next bit of the bulk trade """
                    if BTObject is not None:
                        self.Automate(BTObject.pk)

                    """ notify to pay referrals if any"""
                    Result = self.HandleReferrersPayment(TransactionObject)
                    if not Result['Status']:
                        Data['Message'].append(Result['Message'])
                elif Seller and BuyerPaid:
                    """if user is seller(paying) and buyer has paid, make potential buyer trade buyer"""
                    TransactionObject.Buyer = NegotiationObject[0].UserId
                    TransactionObject.Completed = True
                    Logs.append(UserObject.AccountNumber + " bought " +
                                TransactionObject.Seller.AccountNumber + "'s Trade(Trade Ad #" + str(AdId) + ")")
                    if BTObject is not None:
                        self.Automate(BTObject.pk)

                    """ mark this task as completed """
                    Tasks().Complete(TransactionObject.HandledBy.pk)
                    if AssignemntType == "Queue":
                        """ get unassigned Tasks"""
                        Unassigned = self.GetUnassigned()
                        Result = self.Assign(Unassigned[0].pk, TransactionObject.HandledBy.pk, True)
                        if not Result['Status']:
                            print('Failed to queue')

                    """ notify to pay referrals if any"""
                    Result = self.HandleReferrersPayment(TransactionObject)
                    if not Result['Status']:
                        Data['Message'].append(Result['Message'])
                TransactionObject.save()
            else:
                Logs.append("Admin Rejected " + UserObject.AccountNumber + "'s payment. Reason: " + Message)
                if int(UserId) == TransactionObject.Seller.pk:
                    TransactionObject.Paid = False
                    TransactionObject.save()
                else:
                    NegotiationObject.Paid = False
                    NegotiationObject.save()

            TradeProof.Approved = Action
            if Message != 'n/a':
                TradeProof.Message = Message
            TradeProof.save()

            for Log in Logs:
                RTLObject = ReviewedTransactionLog()
                RTLObject.Log = Log
                RTLObject.IsAdminAction = True
                RTLObject.TransactionID = TransactionObject
                RTLObject.save()

            Data['Status'] = True
            if Action != 1:
                Data['Action'] = False
        except Exception as e:
            print(e)
            Data['Message'].append("Failed to get proof of payment.")
            Data['Status'] = False

        return Data

    def GetFiles(self, AdId, UserId):
        Data = {}
        try:
            Data['TFO'] = get_list_or_404(TransactionFile, TransactionId=AdId, UploadedBy=UserId, Approved=0)
            Data['Status'] = True
        except:
            try:
                Data['TFO'] = get_list_or_404(TransactionFile, TransactionId=AdId, UploadedBy=UserId, Approved=1)
                Data['Status'] = True
                Data['Accepted'] = True
            except:
                Data['Status'] = False
                Data['Message'] = "Image not found."
                Data['Accepted'] = True

        return Data

    def GetAdminCompleted(self, Id, AdId=0):
        Data = {}
        if AdId == 0:
            Data.update(TransactionBase.base.TransactionBaseClass().GetCompleted(AdminId=Id))
        else:
            Data.update(TransactionBase.base.TransactionBaseClass().GetCompleted(AdId=AdId, AdminId=Id))
        return Data

    def Paid(self, filename, AdId, UserId, Id):
        TransactionObject = UserTransactions.objects.get(pk=AdId)
        UserObject = User.objects.get(pk=UserId)
        AdminObject = Admins.objects.get(pk=Id)

        if Id != TransactionObject.HandledBy.pk:
            return False

        TransactionFileObject = AdminTransactionFile()
        TransactionFileObject.FileName = filename
        TransactionFileObject.TransactionId = TransactionObject
        TransactionFileObject.User = UserObject
        TransactionFileObject.UploadedBy = AdminObject
        TransactionFileObject.save()

        RTLObject = ReviewedTransactionLog()
        RTLObject.Log = "Admin has made payments to " + str(UserObject.AccountNumber) + "."
        RTLObject.IsAdminAction = True
        RTLObject.TransactionID = TransactionObject
        RTLObject.save()
        return True

    def GetUnassigned(self):
        """ Gets unassigned tasks """
        return UserTransactions.objects.filter((Q(HandledBy=None)))

    def GetLog(self, AdId, Limit=False):
        if Limit:
            TransactionObject = ReviewedTransactionLog.objects.filter(TransactionID=AdId).first()

            return {'Status': True, 'TransactionObject': TransactionObject, 'Limit': Limit}
        else:
            TransactionsObject = ReviewedTransactionLog.objects.filter(TransactionID=AdId)
            return {'Status': True, 'TransactionsObject': TransactionsObject, 'Limit': Limit}

    def HandleReferrersPayment(self, Ad):
        Data = {'SellerReferred': False, 'BuyerReferred': False, 'Status': True}

        try:
            AffiliateObject = Affiliate.objects.all().order_by('-id').first()
            print(Ad)
            if Ad.Seller.Referrer is not None:
                Data['SellerReferred'] = True

                ServerRateObject = TransactionBase.base.CurrenciesBaseClass().GetServerRate(Ad.FromCurrency, 'USD')

                if 'Exception' in ServerRateObject and ServerRateObject['Exception'] == 0:
                    FromCurrencyToUsdRate = ServerRateObject['ExRObject'].ExchangeRate
                elif 'Exception' in ServerRateObject and ServerRateObject['Exception'] == 1:
                    FromCurrencyToUsdRate = 0.0
                else:
                    FromCurrencyToUsdRate = ServerRateObject[Ad.FromCurrency + '_USD']['val']


            if Ad.Buyer.Referrer is not None:
                Data['BuyerReferred'] = True
                ServerRateObject = TransactionBase.base.CurrenciesBaseClass().GetServerRate(Ad.ToCurrency, 'USD')

                if 'Exception' in ServerRateObject and ServerRateObject['Exception'] == 0:
                    ToCurrencyToUsdRate = ServerRateObject['ExRObject'].ExchangeRate
                elif 'Exception' in ServerRateObject and ServerRateObject['Exception'] == 1:
                    ToCurrencyToUsdRate = 0.0
                else:
                    ToCurrencyToUsdRate = ServerRateObject[Ad.ToCurrency + '_USD']['val']

            if Data['SellerReferred']:
                try:
                    APO = get_object_or_404(AffiliatePayment, Transaction=Ad, User=Ad.Seller)
                except:
                    APO = AffiliatePayment()

                APO.Referrer = Ad.Seller.Referrer
                APO.User = Ad.Seller

                Fee = ((Ad.CTFee/100) * (Ad.Amount))
                Fee = Fee * FromCurrencyToUsdRate

                Amount = (AffiliateObject.Percentage / 100) * Fee


                APO.Amount = Amount
                APO.Transaction = Ad
                APO.save()

            if Data['BuyerReferred']:
                try:
                    APO = get_object_or_404(AffiliatePayment, Transaction=Ad, User=Ad.Buyer)
                except:
                    APO = AffiliatePayment()

                APO.Referrer = Ad.Buyer.Referrer
                APO.User = Ad.Buyer

                AmountInToCurrency = Ad.ExchangeRate * Ad.Amount
                Fee = ((Ad.CTFee / 100) * AmountInToCurrency) * ToCurrencyToUsdRate
                Amount = (AffiliateObject.Percentage / 100) * Fee


                APO.Amount = Amount
                APO.Transaction = Ad
                APO.save()

        except Exception as e:
            # exc_type, exc_obj, exc_tb = sys.exc_info()
            # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            # print(exc_type, fname, exc_tb.tb_lineno)
            # print(e)
            Data['Status': False]
            Data['Message'] = "An error occurred. Please try again later."
        return Data

    def GetUnpaidReferrers(self, Id):
        Data = {'APsObject': [], 'Status': True}
        try:
            TransactionsObject = UserTransactions.objects.filter((~Q(Buyer=None)), HandledBy=Id)

            for Transaction in TransactionsObject:
                """ check if seller's referer  has been paid """
                APO = {'Transaction': Transaction}

                if Transaction.Seller.Referrer is not None:
                    APO['SellerReferred'] = True
                    try:
                        APObject = AffiliatePayment.objects.filter(Transaction=Transaction, User=Transaction.Seller).first()

                        if not APObject.Paid:
                            APO['SR_PaymentStatus'] = 0
                    except:
                        print('here 1')
                        APO['SR_PaymentStatus'] = -1
                        """ referrer bonus not saved for current trade and seller"""
                        Result = self.HandleReferrersPayment(Transaction)
                        if Result['Status']:
                            APO['SR_Created'] = True
                        else:
                            APO['SR_Created'] = False
                else:
                    APO['SellerReferred'] = False

                if Transaction.Buyer.Referrer is not None:
                    APO['BuyerReferred'] = True
                    try:
                        APObject = AffiliatePayment.objects.filter(Transaction=Transaction, User=Transaction.Buyer).first()
                        if not APObject.Paid:
                            APO['BR_PaymentStatus'] = 0
                    except:
                        print('here 2')
                        APO['BR_PaymentStatus'] = -1
                        """ referrer bonus not saved for current trade and buyer"""
                        Result = self.HandleReferrersPayment(Transaction)
                        if Result['Status']:
                            APO['BR_Created'] = True
                        else:
                            APO['BR_Created'] = False
                else:
                    APO['BuyerReferred'] = False

                Data['APsObject'].append(APO)
        except Exception as e:
            """"""
            Data['Status'] = False

        if len(Data['APsObject']) == 0:
            Data['Status'] = False
        return Data

    def PayReferrer(self, Id, UserId, AdId):
        try:
            APObject = AffiliatePayment.objects.filter(Transaction=AdId, User=UserId).first()
            APObject.Paid = True
            APObject.PayDate = datetime.now()
            APObject.save()
            return {'Status': True}
        except:
            return {'Status': False, 'Message': 'An error occurred with updating payment.'}


class Tasks:
    def GetTaskAssignmentType(self):
        return TaskAssignmentType.objects.get(pk=1)

    def SetTaskAssignmentType(self, Type, Id):
        try:
            AssignmentType = get_object_or_404(TaskAssignmentType, pk=1)
            AssignmentType.Type = Type
            AssignmentType.Admin = Admins.objects.get(pk=Id)
            AssignmentType.save()

            TATLog = TaskAssignmentTypeLog()
            TATLog.Admin = AssignmentType.Admin
            TATLog.LogContent = 'Admin #' + str(TATLog.Admin.pk) + ' changed the Task Assignment Type to ' + Type
            TATLog.save()

            return True
        except:
            return False

    def SetDefaultTaskAssignmentType(self):
        try:
            """"""
            get_object_or_404(TaskAssignmentType, pk=1)
            return False
        except:
            """"""
            AssignmentType = TaskAssignmentType()
            AssignmentType.Type = 'Polling'
            AssignmentType.save()
            return True

    def Complete(self, Id):
        AdminObject = Admins.objects.get(pk=Id)
        AdminObject.CompletedTasks = AdminObject.CompletedTasks + 1
        AdminObject.save()

    def Assign(self, Id, IsKYC=False, IsTransaction=False, TaskId=0):
        AdminObject = Admins.objects.get(pk=Id)
        AdminObject.Tasks = AdminObject.Tasks + 1
        AdminObject.save()


        if IsKYC:
            TaskType = "KYC"
        elif IsTransaction:
            TaskType = "Transaction"
        AdminTaskObject = AdminTask()
        AdminTaskObject.TaskType = TaskType
        AdminTaskObject.TaskId = TaskId
        AdminTaskObject.AdminId = AdminObject
        AdminTaskObject.save()

    def GetAllTasks(self, Id, Star):
        Data = {'Message': []}
        try:
            if Star == settings.KY_ADMIN or Star == settings.S_ADMIN:
                Data['TaskObject'] = get_list_or_404(CTKYC, HandledBy=Id)
            elif Star == settings.T_ADMIN or Star == settings.S_ADMIN:
                Data['TaskObject'] = get_list_or_404(UserTransactions, HandledBy=Id)
            Data['Status'] = True
        except Exception:
            Data['Status'] = False
            Data['Message'].append("No tasks found for Admin #" + str(str))
        return Data

    def MyActiveTasks(self, Id, Star):
        Data = {"Count": 0}

        if Star == settings.KY_ADMIN or Star == settings.S_ADMIN:
            try:
                KYCObject = get_list_or_404(CTKYC, IsApproved=False, HandledBy=Id)
                Data['KYCObject'] = KYCObject
                Data['Count'] = len(KYCObject)
            except Exception:
                Data['Message'] = ["No Tasks assigned yet"]

        elif Star == settings.T_ADMIN or Star == settings.S_ADMIN:
            try:
                TransactionsObject = UserTransactions.objects.filter(pk=Id).exclude(Q(Buyer__isnull=False)
                                                                                    | ~Q(Buyer__exact=''))
                Data['TransactionsObject'] = TransactionsObject
                Data['Count'] = len(TransactionsObject)
            except:
                Data['Message'] = ["No tasks assigned yet"]
        return Data

    def GetCompletedTasks(self, Id, Star):
        Data = {'Message': [], 'TaskObject': []}
        try:
            TasksObject = get_list_or_404(AdminTask, AdminId=Id, Completed=True)
            for TaskObject in TasksObject:
                if Star == settings.KY_ADMIN or Star == settings.S_ADMIN:
                    Data['TaskObject'].append(get_object_or_404(CTKYC, pk=TaskObject.pk))
                elif Star == settings.T_ADMIN or Star == settings.S_ADMIN:
                    Data['TaskObject'].append(get_object_or_404(UserTransactions, pk=TaskObject.pk))
            Data['Status'] = True
        except Exception:
            Data['Status'] = False
            Data['Message'].append("No tasks found for Admin #" + str(str))
        return Data


class Utilities:
    K_AccountNumber = "K-"

    def GenerateCTAccountNumber(self, UserId):
        """"K-000000000"""
        for x in range(9):
            self.K_AccountNumber += str(random.randint(0, 9))
        UserObject = User.objects.filter(AccountNumber=self.K_AccountNumber)
        if len(UserObject) == 1:
            self.GenerateCTAccountNumber(UserId)
        elif len(UserObject) == 0:
            UserObject = get_object_or_404(User, pk=UserId)
            UserObject.AccountNumber = self.K_AccountNumber
            UserObject.save()

    def AutoAssignAdmin(self, IsKYC=False, IsTransaction=False):
        Data = {}
        if IsKYC:
            """ select * where the admin is active and is not a T-Admin """
            AdminsObject = Admins.objects.filter(~(Q(Star=int(settings.T_ADMIN))), IsActive=True).order_by('Tasks')
            if len(AdminsObject) > 0:
                Data['Status'] = True
                Data['AdminObject'] = AdminsObject[0]
            else:
                Data['Message'] = "No KY-Admin registered"
                Data['Status'] = False
        if IsTransaction:
            AdminsObject = Admins.objects.filter((~Q(Star=int(settings.KY_ADMIN))),
                                                 IsActive=True).order_by('Tasks')
            if len(AdminsObject) > 0:
                Data['Status'] = True
                Data['AdminObject'] = AdminsObject[0]
            else:
                Data['Message'] = "No T-Admin registered"
                Data['Status'] = False
        return Data

    def UploadToS3(self,File, filename, base_path):
        try:
            ext = os.path.splitext(str(File))[1]
            base_path = 'static/' + base_path
            filename = filename + ext
            ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
            ACCESS_SECRET_KEY = settings.AWS_SECRET_ACCESS_KEY
            BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
            data = File

            s3 = boto3.resource(
                's3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=ACCESS_SECRET_KEY,
                config=Config(signature_version='s3v4')
            )
            s3.Bucket(BUCKET_NAME).put_object(Key=base_path + filename, Body=data, ACL='public-read')
            return True
        except:
            return False

    def CheckIfFileExist(self, FilePaths):
        Data = {}
        index = 1

        for File in FilePaths:
            StringPath = settings.BASE_DIR + '\\' + File
            if os.path.isfile(StringPath):
                Data[File] = {'Status': True, 'FileName': File, 'index': index}
            else:
                Data[File] = {'Status': False, 'FileName': File, 'index': index}
            index = index + 1

        return Data

