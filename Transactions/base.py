from builtins import print
from json import JSONDecodeError
from django.shortcuts import get_object_or_404, get_list_or_404
import json
import requests
from .models import *
from Authentication.models import User, Banks as UserBanks
from CTAdmin.models import ReviewedTransactionLog, TransactionFile as AdminTransactionFile
import CTAdmin
from django.db.models import Q
from Authentication.base import Login as UserLoginClass

CURRENCY_API_KEY = "f2d58c8e435aee34bed9"


class TransactionBaseClass:

    def NewTradeAd(self, PostRequest, UserId):
        """
            first check if user has completed KYC
        params

        * PostRequest['BTID']- used in functions which pass data to NewTradeAdInfo.
            - BTID is ID for BulkTransactions passed from another function
            - while SellOnce is passed from HTML input
        """
        Result = UserLoginClass().CheckKYC(UserId)
        if Result['All'] != 0:
            return {'Status': False, 'Message': "Please complete KYC before proceeding."}
        try:
            ExchangeRate = float(PostRequest['ExchangeRate'])
            Amount = float(PostRequest['Amount'])
            Negotiable = PostRequest['Negotiable']
            FromCurrency = PostRequest['FromCurrency']
            ToCurrency = PostRequest['ToCurrency']
            Fee = float(PostRequest['CTFee'])

            if 'SellOnce' in PostRequest and PostRequest['SellOnce'] != "True":
                BTransactionObject = BulkTransaction()
                BTransactionObject.Seller = User.objects.get(pk=UserId)
                BTransactionObject.BitsPercentage = float(PostRequest['BitPercentage'])
                BTransactionObject.ExchangeRate = ExchangeRate
                BTransactionObject.Amount = Amount
                BTransactionObject.FromCurrency = FromCurrency
                BTransactionObject.ToCurrency = ToCurrency
                BTransactionObject.Negotiable = Negotiable
                BTransactionObject.CTFeePercentage = Fee

                """ recalculate the amount based on bits percentage"""
                # { CTFee.Percentage }}/100) * Amount.value))
                Amount = (float(BTransactionObject.BitsPercentage) / 100) * Amount
                Fee = (Fee/100) * Amount

                BTransactionObject.AmountLeft = BTransactionObject.Amount - Amount
                BTransactionObject.save()

            if float(PostRequest['Payout']) > Fee:
                """ place trade ad based on amount from percentage """
                TransactionsObject = Transactions()
                TransactionsObject.ExchangeRate = ExchangeRate
                TransactionsObject.Amount = Amount
                TransactionsObject.FromCurrency = FromCurrency
                TransactionsObject.ToCurrency = ToCurrency
                TransactionsObject.Negotiable = Negotiable
                TransactionsObject.Seller = User.objects.get(pk=UserId)
                TransactionsObject.CTFeePercentage = Fee
                TransactionsObject.Bank = UserBanks.objects.get(pk=PostRequest['Bank'])

                if 'SellOnce' in PostRequest and PostRequest['SellOnce'] != "True":
                    TransactionsObject.BTID = BTransactionObject
                elif 'BTID' in PostRequest:
                    TransactionsObject.BTID = BulkTransaction.objects.get(pk=PostRequest['BTID'])

                TransactionsObject.save()

                TransactionsLogObject = ReviewedTransactionLog()
                TransactionsLogObject.TransactionID = TransactionsObject
                TransactionsLogObject.Log = str(TransactionsObject.Seller.AccountNumber) + " created a new Trade Ad."
                TransactionsLogObject.save()

                if 'BTID' in PostRequest or PostRequest['SellOnce'] != "True":
                    return {'Status': True, 'BTID': BTransactionObject.pk}
                else:
                    return {'Status': True, 'AdId': TransactionsObject.pk}
            else:
                return {'Status': False, 'Message': "Payout is less than Fee, please input a higher amount."}
        except Exception as e:
            print(e)
            return {'Status': False, 'Message': "An error occurred. Please try again."}

    def ApproveTradeAd(self, AdId, Type="Transaction"):
        Data = {'Status': True}

        try:
            if Type == "Transaction":
                TransactionObject = Transactions.objects.get(pk=AdId)
                TransactionObject.Approved = 1
    
                TransactionObject.save()
            elif Type == "Bulk":
                BTObject = BulkTransaction.objects.get(pk=AdId)
                BTObject.Approved = 1
                
                BTObject.save()
        except:
            Data['Status'] = False
            Data['Message'] = "Failed to approve trade."
        return Data

    def GetMyAds(self, UserId):
        Data = {'TransactionsObject': [], 'TradesCount': 0}
        try:
            TransactionsObject = Transactions.objects.filter(Seller=UserId, Buyer=None, Approved=1).order_by('-id')
            if len(TransactionsObject) > 0:
                for Transaction in TransactionsObject:
                    try:
                        NegotiationResult = self.GetNegotiations(Transaction.pk)
                        PaymentObject = self.GetPaid(Transaction.pk)
                        """status to check if the negotiation query was successful"""

                        if NegotiationResult['Status']:
                            """other users have shown interest in this ad"""
                            if 'AcceptedOffer' in NegotiationResult:
                                tob = MyTradeObjectClass(Transaction, NegotiationResult, NegotiationResult['AcceptedOffer'],
                                                         self.GetNLog(Transaction.pk, True, 1), BuyerInfo=PaymentObject['Buyer'],
                                                         SellerInfo=PaymentObject['Seller'])
                            else:
                                tob = MyTradeObjectClass(TransactionObject=Transaction, NegObj=NegotiationResult,
                                                         NLog=self.GetNLog(Transaction.pk, True, 1))
                        else:
                            tob = MyTradeObjectClass(Transaction, NLog=self.GetNLog(Transaction.pk, True, 1))
                        Data['TransactionsObject'].append(tob)
                    except Exception as e:
                        """do nothing"""
                        continue
                Data['Status'] = True
        except:
            Data['Status'] = False
            Data['Message'] = ["You don't have any Trade Ads yet."]

        if len(Data['TransactionsObject']) == 0:
            Data['Status'] = False
            Data['Message'] = ["You don't have any Trade Ads yet."]
        return Data

    def GetMyCompletedAds(self, UserId):
        Data = {'TransactionsObject': [], 'TradesCount': 0}
        try:
            TransactionsObject = Transactions.objects.filter(~Q(Buyer=None),
                                                             (Q(Seller=UserId) | Q(Buyer=UserId)),
                                                             Approved=1).order_by('-id')
            for Transaction in TransactionsObject:
                NegotiationResult = self.GetNegotiations(Transaction.pk)
                PaymentObject = self.GetPaid(Transaction.pk)
                """status to check if the negotiation query was successful"""
                if NegotiationResult['Status']:
                    if 'AcceptedOffer' in NegotiationResult:
                        tob = MyTradeObjectClass(Transaction, NegotiationResult, NegotiationResult['AcceptedOffer'],
                                                 self.GetNLog(Transaction.pk, True, 1), BuyerInfo=PaymentObject['Buyer'],
                                                 SellerInfo=PaymentObject['Seller'])
                    else:
                        tob = MyTradeObjectClass(TransactionObject=Transaction, NegObj=NegotiationResult,
                                                 NLog=self.GetNLog(Transaction.pk, True, 1))
                    Data['TradesCount'] = Data['TradesCount'] + 1
                else:
                    tob = MyTradeObjectClass(Transaction, NLog=self.GetNLog(Transaction.pk, True, 1))
                Data['TransactionsObject'].append(tob)
                Data['Status'] = True
        except:
            Data['Status'] = False
            Data['Message'] = ["You don't have any completed Trade Ads yet."]
        return Data

    def GetMyOnGoingAds(self, UserId):
        Data = {'TransactionsObject': [], 'TradesCount': 0, 'Interests': [], 'InterestCount': 0}
        try:
            TransactionsObject = Transactions.objects.filter(Seller=UserId, Buyer=None, Approved=1).order_by('-id')

            for Transaction in TransactionsObject:
                NegotiationResult = self.GetNegotiations(Transaction.pk)

                PaymentObject = self.GetPaid(Transaction.pk)

                """status to check if the negotiation query was successful"""
                if NegotiationResult['Status']:
                    if 'AcceptedOffer' in NegotiationResult:
                        tob = MyTradeObjectClass(Transaction, NegotiationResult, NegotiationResult['AcceptedOffer'],
                                                 self.GetNLog(Transaction.pk, True, 1), BuyerInfo=PaymentObject['Buyer'],
                                                 SellerInfo=PaymentObject['Seller'])
                    else:
                        tob = MyTradeObjectClass(TransactionObject=Transaction, NegObj=NegotiationResult, NLog=self.GetNLog(Transaction.pk, True, 1))
                    Data['TradesCount'] = Data['TradesCount'] + 1
                else:
                    tob = MyTradeObjectClass(Transaction, NLog=self.GetNLog(Transaction.pk, True, 1))
                Data['TransactionsObject'].append(tob)

            Result = self.GetMyTradeInterests(UserId)
            Data['Interests'].extend(Result['TransactionsObject'])
            Data['InterestCount'] = Result['TradesCount']
            Data['Status'] = True
        except Exception as e:
            Data['Status'] = False
            Data['Message'] = ["You don't have any Trade Ads yet."]

        return Data

    def GetMyTradeInterests(self, UserId):
        Data = {'TransactionsObject': [], 'TradesCount': 0}
        try:
            NegotiationsObject = get_list_or_404(Negotiations, UserId=UserId, Approved=1)

            for Negotiation in NegotiationsObject:
                if Negotiation.TransactionsId.Buyer is not None:
                    """completed trade ad, skip"""
                    continue
                PaymentObject = self.GetPaid(Negotiation.TransactionsId.pk)
                if PaymentObject['Buyer']:
                    BuyerInfo = PaymentObject['Buyer']
                else:
                    BuyerInfo = 'n/a'

                if PaymentObject['Seller'] != 'n/a':
                    SellerInfo = PaymentObject['Seller']
                else:
                    SellerInfo = 'n/a'
                # if len(TransactionFile.objects.get(TransactionId=Negotiation.TransactionsId.pk,
                #                                    UploadedBy=UserId, Accepted=True)) == 0:
                # """completed"""

                """for this particular negotiation, has the seller accepted any offer? 
                if yes, transaction is taken out of my ongoing list if accepted is not me else put in"""
                if len(Negotiations.objects.filter(TransactionsId=Negotiation.TransactionsId.pk, Accepted=True)) != 0:
                    """seller has accepted an offer"""
                    if Negotiation.UserId.pk == UserId:
                        """seller accepted my offer"""
                        tob = MyTradeObjectClass(TransactionObject=Negotiation.TransactionsId,
                                                 NegObj=self.GetNegotiations(Negotiation.TransactionsId.pk),
                                                 AcceptedOffer=Negotiation.UserId,
                                                 NLog=self.GetNLog(Negotiation.TransactionsId.pk, True, 1), BuyerInfo=BuyerInfo,
                                                 BuyerAccepted=PaymentObject['BuyerApproved'], SellerInfo=SellerInfo,
                                                 SellerAccepted=PaymentObject['SellerApproved'])
                        Data['TransactionsObject'].append(tob)
                        Data['TradesCount'] = Data['TradesCount'] + 1
                else:
                    """seller hasn't accepted any offer yet"""
                    tob = MyTradeObjectClass(TransactionObject=Negotiation.TransactionsId,
                                             NegObj=self.GetNegotiations(Negotiation.TransactionsId.pk),
                                             NLog=self.GetNLog(Negotiation.TransactionsId.pk, True, 1))
                    Data['TransactionsObject'].append(tob)
                    Data['TradesCount'] = Data['TradesCount'] + 1
            Data['Status'] = True
        except Exception as e:
            print(e)
            Data['Status'] = False
            Data['Message'] = ["You don't have any Trade interest yet."]
        return Data

    def GetNegotiations(self, AdId):
        Data = {'NegotiationsObject': [], }
        try:
            NegotiationsObject = get_list_or_404(Negotiations, TransactionsId=AdId, Approved=1)

            try:
                """check if transaction has a potential buyer"""
                Data['AcceptedOffer'] = Negotiations.objects.filter(TransactionsId=AdId, Accepted=True).first()
            except:
                """do nothing"""

            for Negotiation in NegotiationsObject:
                NegObj = NegotiationObjectClass(Negotiation, Negotiation.UserId)
                Data['NegotiationsObject'].append(NegObj)
            Data.update({'NegotiationsObjectLength': len(NegotiationsObject)})
            Data['Status'] = True
        except Exception as e:
            Data['Status'] = False
            Data['Message'] = ['No views on this trade yet.']
        return Data

    def GetAllAdsActiveOrNot(self):
        Data = {'TransactionsObject': []}
        TransactionsObject = Transactions.objects.all()[:10]
        for Transaction in TransactionsObject:
            if not Transaction.Buyer:
                """
                Check if seller already started a transaction with a potential buyer if none, 
                add to the list of open transactions
                """
                NegotiationObjectLen = len(Negotiations.objects.filter(TransactionsId=Transaction.pk, Accepted=True))
                if NegotiationObjectLen == 0:
                    Data['TransactionsObject'].append(Transaction)
        return Data

    def GetAllAds(self):
        Data = {'TransactionsObject': []}
        TransactionsObject = Transactions.objects.filter(Buyer=None, Approved=1)
        for Transaction in TransactionsObject:
            if not Transaction.Buyer:
                """
                Check if seller already started a transaction with a potential buyer if none, 
                add to the list of open transactions
                """
                NegotiationObjectLen = len(Negotiations.objects.filter(TransactionsId=Transaction.pk, Accepted=True))
                if NegotiationObjectLen == 0:
                    Data['TransactionsObject'].append(Transaction)
        return Data

    def GetAdById(self, AdId):
        TransactionObject = get_object_or_404(Transactions, pk=AdId, Approved=1)
        return {"TransactionObject": TransactionObject}

    def BuyAd(self, AdId, UserId, Message = "n/a", ProposedRate = -666):
        try:
            """first check if user has completed KYC"""
            Result = UserLoginClass().CheckKYC(UserId)
            if Result['All'] != 0:
                return {'Status': False, 'Message': "Please complete KYC before proceeding."}
            Logs = []

            UserObject = User.objects.get(pk=UserId)
            TransactionObject = Transactions.objects.get(pk=AdId)

            try:
                # NegObject = Negotiations.objects.filter(UserId=UserId, TransactionsId=AdId)
                NegotiationObject = get_object_or_404(Negotiations, TransactionsId=AdId, UserId=UserId)
            except:
                """save new negotiation"""
                NegotiationObject = Negotiations()
                NegotiationObject.Accepted = False
                NegotiationObject.UserId = User.objects.get(pk=UserId)
                NegotiationObject.TransactionsId = TransactionObject

                Logs.append("Trade #" + str(
                    AdId) + " posted by " + TransactionObject.Seller.AccountNumber + " has a potential buyer " + UserObject.AccountNumber)

            if float(ProposedRate) != float(-666) or TransactionObject.ExchangeRate != float(ProposedRate):
                Logs.append(UserObject.AccountNumber + " proposed an Exchange Rate of " + str(ProposedRate) + TransactionObject.ToCurrency +
                            " for this Trade. (your rate: " + str(TransactionObject.ExchangeRate) +")")

            NegotiationObject.Message = Message
            NegotiationObject.ProposedRate = float(ProposedRate)
            NegotiationObject.save()

            """only save trade log if the log is not empty"""
            for Log in Logs:
                TradeLog = ReviewedTransactionLog()
                TradeLog.Log = Log
                TradeLog.TransactionID = TransactionObject
                TradeLog.save()

            return {"Status": True, "Message": 'Offer sent.', 'NId': NegotiationObject.pk}
        except Exception as e:
            print(e)
            return {"Status": False, "Message": 'Offer failed to send.'}

    def ApproveTradeInterest(self, NId):
        Data = {'Status': True}

        try:
            NegotiationObject = Negotiations.objects.get(pk=NId)
            NegotiationObject.Approved = 1

            NegotiationObject.save()
        except Exception as e:
            Data['Status'] = False
            Data['Message'] = "Failed to approve of trade interest."

        return Data

    def ActionOnNegotiation(self, Action, NegotiationId):
        try:
            NegotiationObject = get_object_or_404(Negotiations, pk=NegotiationId, Approved=1)
            if Action:
                """only accept an offer if none has been accepted yet."""
                if len(Negotiations.objects.filter(TransactionsId=NegotiationObject.TransactionsId, Accepted=True, Approved=1)) == 0:
                    NegotiationObject.Accepted = Action
                    NegotiationObject.save()

                    TradeLog = ReviewedTransactionLog()
                    TradeLog.Log = NegotiationObject.TransactionsId.Seller.AccountNumber + " accepted " + NegotiationObject.UserId.AccountNumber + "'s offer."
                    TradeLog.TransactionID = NegotiationObject.TransactionsId
                    TradeLog.save()

                    """send to T-Admin"""
                    AdminAssign = CTAdmin.base.Transactions().Assign(NegotiationObject.TransactionsId.pk)
                    if AdminAssign['Status']:
                        return {"Status": True, "Message": 'Action successful.'}
                    elif not AdminAssign['Status']:
                        return {'Message': AdminAssign['Message'], 'Status': False}
                    elif not AdminAssign['Status'] and 'Manual' in AdminAssign:
                        return {'Message': 'Action Successful, an admin would be assigned to this transaction soon.',
                                'Status': True}
                else:
                    return {"Status": False,
                            "Message": 'Already accepted another offer. Please reject that offer to accept this offer.'}
            else:
                if NegotiationObject.Accepted:
                    NegotiationObject.Accepted = Action
                    NegotiationObject.save()

                    TradeLog = ReviewedTransactionLog()
                    TradeLog.Log = NegotiationObject.TransactionsId.Seller.AccountNumber + " declined " + NegotiationObject.UserId.AccountNumber + "'s offer."
                    TradeLog.TransactionID = NegotiationObject.TransactionsId
                    TradeLog.save()
                    return {"Status": True, "Message": 'Action successful.'}
                else:
                    return {"Status": False, "Message": 'Action unsuccessful.'}

        except Exception as e:
            return {"Status": False, "Message": 'Action failed, please try again or contact Admin.'}

    def GetNLog(self, AdId, Limit=False, Len=1):
        try:
            Data = {'ReviewedTransactionLog': None, 'status': True}

            if Limit:
                ReviewedTransactionLogObj = ReviewedTransactionLog.objects.filter(TransactionID=AdId).order_by('-id').first()
                Data['ReviewedTransactionLogLen'] = Len
            else:
                ReviewedTransactionLogObj = ReviewedTransactionLog.objects.filter(TransactionID=AdId).order_by('-id')
                Data['ReviewedTransactionLogLen'] = len(ReviewedTransactionLogObj)

                RTLObj = ReviewedTransactionLog.objects.filter(TransactionID=AdId,
                                                               UserNotified=False).order_by('-id')
                """only mark log entries as read when all was loaded"""
                for RTL in RTLObj:
                    RTL.UserNotified = True
                    RTL.save()

            Data['ReviewedTransactionLog'] = ReviewedTransactionLogObj
            return Data
        except:
            return {'status': False}

    def GetNLogAndPaymentInfo(self, AdId, Limit=False, Len=1):
        Data = {'ReviewedTransactionLog': []}
        """
            RTL => []
            [0] => {}
            {} => RTL,AdminFileStatus,AdminFile
            RTL => LogDate, Log
            AdminFile => filename 
        """
        if Limit:
            ReviewedTransactionLogObj = ReviewedTransactionLog.objects.filter(TransactionID=AdId).order_by('-id')
            Data['ReviewedTransactionLogLen'] = Len
        else:
            ReviewedTransactionLogObj = ReviewedTransactionLog.objects.filter(TransactionID=AdId).order_by('-id')
            Data['ReviewedTransactionLogLen'] = len(ReviewedTransactionLogObj)
            RTLObj = ReviewedTransactionLog.objects.filter(TransactionID=AdId,
                                                           UserNotified=False).order_by('-id')
            """only mark log entries as read when all was loaded"""
            for RTL in RTLObj:
                RTL.UserNotified = True
                RTL.save()
        for Log in ReviewedTransactionLogObj:
            LogInfoDict = {'RTL': Log, 'AdminFileStatus': False}
            if ReviewedTransactionLogObj[0].TransactionID.HandledBy is not None:
                """ if admin has been assigned"""
                Condition1 = "Admin has made payments to " + str(
                    ReviewedTransactionLogObj[0].TransactionID.Seller.AccountNumber) + "."

                if ReviewedTransactionLogObj[0].TransactionID.Buyer is not None:
                    """ if buyer has paid """
                    Condition2 = "Admin has made payments to " + str(
                        ReviewedTransactionLogObj[0].TransactionID.Buyer.AccountNumber) + "."
                    UserObject = ReviewedTransactionLogObj[0].TransactionID.Buyer
                else:
                    UserObject = ReviewedTransactionLogObj[0].TransactionID.Seller
                    Condition2 = 'n/a'

                if Log.Log == Condition1 or Log.Log == Condition2:
                    """if admin uploaded a file for user"""
                    AdminTransactionFileObj = AdminTransactionFile.objects.filter(TransactionId=ReviewedTransactionLogObj[0].TransactionID, User=UserObject)
                    if len(AdminTransactionFileObj) > 0:
                        """ verify a file info for this User does exist in the db for the current Transaction """
                        LogInfoDict['AdminFile'] = AdminTransactionFileObj
                        LogInfoDict['AdminFileStatus'] = True

            Data['ReviewedTransactionLog'].append(LogInfoDict)
        return Data

    def Paid(self, AdId, UserId, FileName):
        try:
            TransactionObject = Transactions.objects.get(pk=AdId)
            if int(TransactionObject.Seller.pk) == int(UserId):
                """Seller paid"""
                TransactionObject.Paid = True
                TransactionObject.save()
                Log = TransactionObject.Seller.AccountNumber + " made payments."
                UserObject = TransactionObject.Seller
            else:
                NegotiationObject = get_object_or_404(Negotiations, TransactionsId=AdId, Accepted=True)
                NegotiationObject.Paid = True
                NegotiationObject.save()
                Log = NegotiationObject.UserId.AccountNumber + " made payments."
                UserObject = NegotiationObject.UserId

            """save to log"""
            RTLObject = ReviewedTransactionLog()
            RTLObject.TransactionID = TransactionObject
            RTLObject.Log = Log
            RTLObject.LogActionBy = UserObject
            RTLObject.save()

            """save proof of payment"""
            TransactionFileObj = TransactionFile()
            TransactionFileObj.TransactionId = TransactionObject
            TransactionFileObj.FileName = FileName
            TransactionFileObj.UploadedBy = UserObject
            TransactionFileObj.save()

            return True
        except:
            return False

    def GetPaid(self, AdId):
        """ sellerpaid and buyerpaid are used to check if the admin has paid."""

        Data = {'Seller': 'n/a', 'SellerApproved': False, 'Buyer': 'n/a',
                'BuyerApproved': False, 'SellerPaid': False, 'BuyerPaid': False}
        """ User Paid Info """
        try:
            """get seller info"""
            Data['Seller'] = get_object_or_404(Transactions, Paid=True, pk=AdId)
            try:
                """check if Seller's payment has been approved"""
                if len(TransactionFile.objects.filter(TransactionId=AdId,
                                                      UploadedBy=Data['Seller'].Seller.pk, Approved=1)) > 0:
                    Data['SellerApproved'] = True
            except Exception as e:
                """n/a"""

            try:
                """ if admin has paid seller, change status to true  """
                ATFObject = AdminTransactionFile.objects.filter(TransactionId=AdId,
                                                                User=Data['Seller'].Seller.pk).order_by('-id')[0]

                Data['SellerPaid'] = True
                Data['SellerPayment'] = ATFObject
            except Exception as e:
                print(e)
                """n/a"""
            
            """get buyer info"""
            Data['Buyer'] = get_object_or_404(Negotiations, Paid=True, TransactionsId=AdId)
            try:
                if len(TransactionFile.objects.filter(TransactionId=AdId,
                                                      UploadedBy=Data['Buyer'].UserId.pk, Approved=1)) > 0:
                    Data['BuyerApproved'] = True
            except:
                """n/a"""
            try:
                """ Admin Paid Info """
                ATFObject = AdminTransactionFile.objects.filter(TransactionId=AdId,
                                                                User=Data['Buyer'].UserId.pk).order_by('-id')[0]
                Data['BuyerPaid'] = True
                Data['BuyerPayment'] = ATFObject

            except:
                """n/a"""
        except Exception as e:
            print(e)
            """if crashed, try to get buyer's info"""
            try:
                Data['Buyer'] = get_object_or_404(Negotiations, Paid=True, TransactionsId=AdId)
                try:
                    if len(TransactionFile.objects.filter(TransactionId=AdId, UploadedBy=Data['Buyer'].UserId.pk,
                                                      Approved=1)) > 0:
                        Data['BuyerApproved'] = True
                    """ Admin Paid Info """
                    try:
                        ATFObject = AdminTransactionFile.objects.filter(TransactionId=AdId,
                                                                        User=Data['Buyer'].UserId.pk).order_by('-id')[0]
                        Data['BuyerPaid'] = True
                        Data['BuyerPayment'] = ATFObject
                    except:
                        """n/a"""
                except:
                    """n/a"""
            except Exception:
                """n/a"""
        return Data

    def GetCompleted(self, UserId = 0, AdId=0, AdminId=0):
        Data = {'TransactionsObject': [], 'TradesCount': 0}
        try:
            if AdId == 0:
                if AdminId != 0:
                    """Admin is requesting completed transaction"""
                    TransactionsObject = Transactions.objects.filter(~Q(Buyer=None), HandledBy=AdminId).order_by('-id')
                else:
                    TransactionsObject = Transactions.objects.filter(~Q(Buyer=None), Seller=UserId).order_by('-id')
            else:
                """"""
                if AdminId != 0:
                    """"""
                    TransactionsObject = Transactions.objects.filter(~Q(Buyer=None), HandledBy=AdminId, pk=AdId).order_by('-id')
                else:
                    TransactionsObject = Transactions.objects.filter(~Q(Buyer=None), Seller=UserId, pk=AdId).order_by('-id')

            for Transaction in TransactionsObject:
                NegotiationResult = self.GetNegotiations(Transaction.pk)
                PaymentObject = self.GetPaid(Transaction.pk)
                """status to check if the negotiation query was successful"""
                if NegotiationResult['Status']:
                    if 'AcceptedOffer' in NegotiationResult:
                        tob = MyTradeObjectClass(Transaction, NegotiationResult, NegotiationResult['AcceptedOffer'],
                                                 self.GetNLog(Transaction.pk, True, 1), PaymentObject['Buyer'],
                                                 BuyerAccepted=PaymentObject['BuyerApproved'], SellerInfo=PaymentObject['Seller'], SellerAccepted=PaymentObject['SellerApproved'])
                    else:
                        tob = MyTradeObjectClass(TransactionObject=Transaction, NegObj=NegotiationResult,
                                                 NLog=self.GetNLog(Transaction.pk, True, 1))
                    Data['TradesCount'] = Data['TradesCount'] + 1
                else:
                    tob = MyTradeObjectClass(Transaction, NLog=self.GetNLog(Transaction.pk, True, 1))
                Data['TransactionsObject'].append(tob)
                Data['Status'] = True

        except:
            Data['Status'] = False
            Data['Message'] = ["You don't have any completed Trade Ads yet."]
        return Data

    def GetReview(self, UserId, AdId=0):
        Data = {}
        if AdId == 0:
            ReviewsObject = Review.objects.filter(ReviewBy=UserId)
        else:
            ReviewsObject = Review.objects.filter(ReviewBy=UserId, TransactionId=AdId)
        Data['Reviews'] = ReviewsObject
        Data['ReviewsLen'] = len(ReviewsObject)
        return Data

    def PostReview(self, AdId, Message, UserId):
        ReviewObject = Review()
        ReviewObject.ReviewBy = User.objects.get(pk=UserId)
        ReviewObject.Message = Message
        ReviewObject.TransactionId = Transactions.objects.get(pk=AdId)
        ReviewObject.save()
        return True

    def GetDeclinedTransactions(self, UserId, AdId=0):
        Data = {'TransactionsObject': []}
        if AdId == 0:
            TradesObject = Negotiations.objects.filter(UserId=UserId)
        else:
            TradesObject = Negotiations.objects.filter(pk=AdId, UserId=UserId, Accepted=False)

        for Transaction in TradesObject:
            NegotiationObject = Negotiations.objects.filter(TransactionsId=Transaction.pk, Accepted=True)

            print(NegotiationObject)
            if len(NegotiationObject) > 0:
                """transaction has been accepted"""
                if NegotiationObject[0].UserId != UserId:
                    TransactionObject = Transactions.objects.get(pk=Transaction.pk)
                    """another request was accepted == declined"""
                    Data['TransactionsObject'].append(MyTradeObjectClass(TransactionObject))
        Data['TransactionsObjectLen'] = len(Data['TransactionsObject'])

        return Data

    def GetCTFee(self):
        return CTAdmin.base.AdminBaseClass().GetCTFee()

    def Close(self, ClosedBy, AdId, IsAdmin=False, Message='n/a'):
        TransactionObject = Transactions.objects.filter(pk=AdId).first()
        TransactionObject.Completed = True
        if IsAdmin:
            TransactionObject.Message = Message
        TransactionObject.save()

        """save to log"""
        RTLObject = ReviewedTransactionLog()
        RTLObject.TransactionID = TransactionObject
        if IsAdmin:
            if ClosedBy != TransactionObject.HandledBy.pk:
                return {'Status': False}
            if Message != 'n/a':
                RTLObject.Log = "Admin closed this transaction. Reason: " + Message
            else:
                RTLObject.Log = "Admin closed this transaction."
            RTLObject.LogActionBy = TransactionObject.HandledBy
        else:
            if ClosedBy != TransactionObject.Seller.pk:
                return {'Status': False}
            RTLObject.Log = RTLObject.Log = str(TransactionObject.Seller.AccountNumber) + " closed this transaction."
            RTLObject.LogActionBy = TransactionObject.Seller
        RTLObject.save()
        return {'Status': True}

    def GetBulk(self, UserId, OnlyIncompleted=False):

        try:
            if OnlyIncompleted:
                """"""
                BTsObject = BulkTransaction.objects.filter(Seller=UserId, Completed=False, Approved=1)
            else:
                BTsObject = BulkTransaction.objects.filter(Seller=UserId, Approved=1)

            return {'BTsObject': BTsObject, 'Status': True}

        except:
            return {'Status': False}

    def TotalReferrerBonus(self, UserId):
        try:
            APO = AffiliatePayment.objects.filter(Referrer=UserId, Paid=False)
            Total = 0
            for Object in APO:
                Total = Total + Object.Amount
            return {'Status': 1, 'APO': APO, 'Total': Total}
        except:
            return {'Status': 0, 'Message': 'Failed to get bonus information.'}

    def RequestBonus(self, UserId):
        try:
            APO = AffiliatePayment.objects.filter(Referrer=UserId, Paid=False)
            for Object in APO:
                Object.Flag = 1
                Object.save()
            return {'Status': 1}
        except:
            return {'Status': 0, 'Message': 'Failed to get bonus information.'}


class CurrenciesBaseClass:

    def GetServerRate(self, From, To):
        try:
            url = 'https://free.currencyconverterapi.com/api/v5/convert?apiKey=' + CURRENCY_API_KEY + '&compact=y&q=' + From + "_" + To
            response = requests.get(url)
            JsonLoaded = json.loads(response.content)
            if 'error' in JsonLoaded:
                raise ServerRateError('Failed to fetch online rates.')
            return JsonLoaded
        except Exception or ServerRateError:
            Data = {'Message': ["Can't get online exchange rate at the moment."], 'Exception': 0}
            try:
                ExRObject = get_object_or_404(ExchangeRate, ShortForm=From + "_" + To)
                Data['ExRObject'] = ExRObject
            except:
                Data['Exception'] = 1
                Data['Message'].append("Cant't get a recent exchange rate at the moment, please input one manually.")

            return Data

    def GetCurrencies(self):
        try:
            url = 'https://free.currencyconverterapi.com/api/v6/currencies?apiKey=' + CURRENCY_API_KEY
            response = requests.get(url)
            JsonLoaded = json.loads(response.content)
            if 'error' in JsonLoaded:
                raise ServerRateError
            return JsonLoaded
        except Exception or ServerRateError:
            Data = {'ErrorMessage': "Can't get online exchange rate at the moment.", 'Exception': True}
            CurrenciesObject = get_list_or_404(Currencies)
            Data['CurrenciesObject'] = CurrenciesObject
            return Data

    def SaveCurrency(self, Currency, CurrencyName):
        if len(Currencies.objects.filter(CountryCurrencyShort=Currency, CurrencyName=CurrencyName)) == 0:
            CurrencyObject = Currencies()
            CurrencyObject.CountryCurrencyShort = Currency
            CurrencyObject.CurrencyName = CurrencyName
            CurrencyObject.save()

    def SaveExchangeRate(self, ShortForm, Rate):
        if len(ExchangeRate.objects.filter(ShortForm=ShortForm, ExchangeRate=Rate)) == 0:
            ExRObject = ExchangeRate()
            ExRObject.ShortForm = ShortForm
            ExRObject.ExchangeRate = Rate
        else:
            """Update existing"""
            ExRObject = get_object_or_404(ExchangeRate, ShortForm=ShortForm, ExchangeRate=Rate)
            ExRObject.ShortForm = ShortForm
            ExRObject.ExchangeRate = Rate
        ExRObject.save()


class ServerRateError(Exception):
    pass


class MyTradeObjectClass(object):
    def __init__(self, TransactionObject, NegObj = None, AcceptedOffer='n/a', NLog='n/a', BuyerInfo='n/a', BuyerAccepted=False, SellerInfo='n/a', SellerAccepted=False):
        self.Transaction = TransactionObject
        if NegObj is not None:
            self.NegotiationObject = NegObj
        self.AcceptedOfferStatus = False
        if AcceptedOffer != 'n/a' and AcceptedOffer is not None:
            self.AcceptedOffer = AcceptedOffer
            self.AcceptedOfferStatus = True
        if NLog != 'n/a' and NLog is not None:
            self.NLog = NLog
        if BuyerInfo != 'n/a' and BuyerInfo is not None:
            self.BuyerInfo = BuyerInfo
            self.BuyerAccepted = BuyerAccepted
        if SellerInfo != 'n/a'  and SellerInfo is not None:
            self.SellerInfo = SellerInfo
            self.SellerAccepted = SellerAccepted


class NegotiationObjectClass(object):
    def __init__(self, NegObj, UserObjectBuyer):
        self.NegotiationObject = NegObj
        self.UserObject = UserObjectBuyer

