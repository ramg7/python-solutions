# acme_bank.py
# Python Coding
#
# Created by Roberto Merlos on 3/29/19.
# Copyright © 2019 RAMG. All rights reserved.
#
# ACME Bank - A banking simulation using MongoDB and PyMongo

import pymongo
from pymongo.errors import ConnectionFailure
from prettytable import PrettyTable
import datetime


def connect(host="", port=""):
    client = None
    try:
        client = pymongo.MongoClient(host, port)
        print("Connected")
    except ConnectionFailure as e:
        print("Connection Failed", e)

    return client


class Bank:
    def __init__(self, bank_name, bank_db):
        self.bank_name = bank_name
        self.bank_db = bank_db
        self.a = bank_db.accounts
        self.c = bank_db.customers
        self.t = bank_db.transactions

    def menu(self):
        table = PrettyTable()
        # after installing 'ptable' the title is added
        table.title = self.bank_name
        table.field_names = ["Key", "Action"]
        table.add_row(["a", "Add a customer"])
        table.add_row(["c", "Display customers"])
        table.add_row(["d", "Deposit to an account"])
        table.add_row(["w", "Withdraw from an account"])
        table.add_row(["t", "Display transactions history for an account"])
        table.add_row(["q", "Quit [a task]"])
        table.add_row(["e", "Exit"])
        print(table)

    def add_customer(self, first_name, last_name, ssn, address, account_type,
                     initial_balance, interest_rate, overdraft_fee_rate, new=False):

        first_name = first_name.lower()
        last_name = last_name.lower()
        address = address.lower()
        account_type = account_type.lower()

        account = {"account_type": account_type, "balance": initial_balance,
                   "interest_rate": interest_rate, "overdraft_fee_rate": overdraft_fee_rate}

        account_number = 0
        if new:
            cc = self.c.aggregate([{"$group": {"_id": "$account_number", "maxAccount": {"$max": "$account_number"}}},
                                   {"$sort": {"maxAccount": -1}}])
            for i in cc:
                if i["maxAccount"] is not None:
                    print(i["maxAccount"])
                    account_number = i["maxAccount"] + 1
                break


            self.c.insert_one({"first_name": first_name, "last_name": last_name, "ssn": ssn, "address": address,
                               "account_number": account_number})
            self.c.update_one({"ssn": ssn}, {"$set": {"accounts": [account]}}, True)
            print("Customer added: " + first_name + " " + last_name + ".")
        else:
            customer = self.c.find({"ssn": ssn})
            for c in customer:
                account_number = c["account_number"]
                break
            self.c.update_one({"ssn": ssn}, {"$addToSet": {"accounts": account}})
            print("Customer updated: " + first_name + " " + last_name + ".")

        # insert transaction
        self.t.insert_one(
            {"ssn": ssn, "account_number": account_number, "account_type": account_type, "transaction_type": "deposit",
             "balance": initial_balance, "transaction_time": datetime.datetime.now()})

    def transaction(self, account, account_type, amount, transaction_type):

        customer = self.c.find({"$and": [{"account_number": account}, {"accounts.account_type": account_type}]})

        ssn = -1
        balance = 0
        overdraft_fee_rate = 0
        for doc in customer:
            ssn = doc['ssn']
            balance_list = doc["accounts"]
            for i in balance_list:
                if account_type == i['account_type']:
                    balance = i['balance']
                    overdraft_fee_rate = i['overdraft_fee_rate']
                    break

            break

        new_balance = balance
        if transaction_type == "deposit":
            new_balance += amount
            print(f"> New balance: {new_balance}.")
        elif transaction_type == "withdraw":
            new_balance -= amount
            if new_balance < 0:
                print(
                    f"> WARNING: Negative balance: {new_balance}.\n> Overdraft fee rate will be applied.\n"
                    f"> New balance: {new_balance - overdraft_fee_rate}.")
                new_balance -= overdraft_fee_rate

        # update balance
        self.c.update_one({"accounts": {"$elemMatch": {"account_type": account_type}}}, {"$set": {
            "accounts.$.balance": new_balance}})

        # insert transaction
        self.t.insert_one(
            {"ssn": ssn, "account_number": account, "account_type": account_type, "transaction_type": transaction_type,
             "balance": new_balance, "transaction_time": datetime.datetime.now()})
        pass

    def display_transactions(self, account_number):
        table = PrettyTable()
        table.title = f"Transactions for {account_number}"
        table.field_names = ["Account", "Transaction type", "Balance", "Transacted on"]

        customer = self.c.find({"account": account_number})
        transactions = self.t.find({"account_number": account_number})

        for t in transactions:
            table.add_row([t["account_type"], t["transaction_type"], t["balance"], t["transaction_time"]])

        print(table)

        last_access_time_stamp = None
        last_time_stamp = self.t.aggregate(
            [{"$match": {"account_number": account_number}},
             {"$group": {"_id": "$transaction_time", "maxDate": {"$max": "$transaction_time"}}},
             {"$sort": {"maxDate": -1}}])
        for d in last_time_stamp:
            last_access_time_stamp = d["maxDate"]
            break
        print(f"Last access time stamp: {last_access_time_stamp}.")

    def display_customers(self):
        table = PrettyTable()
        table.title = "Customers"
        table.field_names = ["Name", "SNN", "Account Number", "Accounts"]

        customers = self.c.find({});

        for c in customers:
            name = c["first_name"] + " " + c["last_name"]
            acc = c["account_number"]

            accs = self.c.aggregate(
                [{"$match": {"account_number": acc}}, {"$project": {"account_number": 1, "ssn": 1, "accounts": {
                    "$cond": {"if": {"$isArray": '$accounts'}, "then": {'$size': '$accounts'}, "else": 'NA'}}}}])
            ssn = c["ssn"]

            accs_n = 0
            for i in accs:
                accs_n = i["accounts"]
                break
   
            table.add_row([name, ssn, acc, accs_n])

        print(table)

    def account_available(self, var, account_type, flag):

        accounts = None
        if flag:
            accounts = self.c.find({"$and": [{"ssn": var}, {"accounts.account_type": account_type}]})
        else:
            accounts = self.c.find({"$and": [{"account_number": var}, {"accounts.account_type": account_type}]})

        accs = []
        for acc in accounts:
            accs.append(acc)

        if len(accs) > 0:
            return False

        return True

    def is_new(self, var, flag):

        result = None

        if flag:
            result = self.c.find({"ssn": var})
        else:
            result = self.c.find({"account_number": var})

        ssns = []
        for r in result:
            ssns.append(r)

        if len(ssns) > 0:
            return False

        return True


def main():
    client = connect("localhost", 27017)
    bank = Bank("ACME Bank", client.acme_bank)

    bank.menu()
    print("")
    while 1:
        choice = input("> ").lower()
        # -------------------------------------------------------------------------------------------------*
        if choice == "a":
            print("> * General info *")
            first_name = input("> First name: ")
            if first_name == "q":
                continue
            while first_name.isdigit():
                first_name = input("> First name: ")
                if first_name == "q":
                    break
            if first_name == "q":
                continue

            last_name = input("> Last name: ")
            if last_name == "q":
                continue
            while last_name.isdigit():
                last_name = input("> Last name: ")
                if last_name == "q":
                    break
            if last_name == "q":
                continue

            ssn_str = input("> SSN: ")
            if ssn_str == "q":
                continue
            while not ssn_str.isdigit():
                ssn_str = input("> SSN: ")
                if ssn_str == "q":
                    break
            if ssn_str == "q":
                continue
            ssn = int(ssn_str)

            address = input("> Address: ")
            if address == "q":
                continue
            while address.isdigit():
                address = input("> Address: ")
                if address == "q":
                    break
            if address == "q":
                continue

            print("\n> * Account info *")
            account_type = ""
            new_customer = False
            while 1:
                t = input("> Account type [Checking (c) / Savings (s)]: ").lower()
                # check account
                if t == "c" or t == "s":
                    if t == "c":
                        account_type = "checking"
                    else:
                        account_type = "savings"

                    if bank.account_available(ssn, account_type, True):
                        break
                    else:
                        print("> not available")
                elif t == "q":
                    break

            if t == "q":
                continue

            new_customer = bank.is_new(ssn, True)

            initial_balance_str = input("> Initial balance: ")
            if initial_balance_str == "q":
                continue
            initial_balance_str2 = initial_balance_str.replace(".", "", 1)
            while not initial_balance_str2.isdigit():
                initial_balance_str = input("> Initial balance: ")
                if initial_balance_str == "q":
                    break
                initial_balance_str2 = initial_balance_str.replace(".", "", 1)
            if initial_balance_str == "q":
                continue
            initial_balance = float(initial_balance_str)

            interest_rate_str = input("> Interest rate (%): ")
            if interest_rate_str == "q":
                continue
            interest_rate_str2 = interest_rate_str.replace(".", "", 1)
            while not interest_rate_str2.isdigit():
                interest_rate_str = input("> Interest rate (%): ")
                if interest_rate_str == "q":
                    break
                interest_rate_str2 = interest_rate_str.replace(".", "", 1)
            if interest_rate_str == "q":
                continue
            interest_rate = float(interest_rate_str)

            overdraft_fee_rate_str = input("> Overdraft fee rate: ")
            if overdraft_fee_rate_str == "q":
                continue
            overdraft_fee_rate_str2 = overdraft_fee_rate_str.replace(".", "", 1)
            while not overdraft_fee_rate_str2.isdigit():
                overdraft_fee_rate_str = input("> Overdraft fee rate: ")
                if overdraft_fee_rate_str == "q":
                    break
                overdraft_fee_rate_str2 = overdraft_fee_rate_str.replace(".", "", 1)
            if overdraft_fee_rate_str == "q":
                continue
            overdraft_fee_rate = float(overdraft_fee_rate_str)

            bank.add_customer(first_name, last_name, ssn, address, account_type,
                              initial_balance, interest_rate, overdraft_fee_rate, new_customer)

        # -------------------------------------------------------------------------------------------------*
        elif choice == "c":
            bank.display_customers()

        # -------------------------------------------------------------------------------------------------*
        elif choice == "d" or choice == "w":
            account_str = ""
            if choice == "d":
                account_str = input("> Deposit to: ")
                if account_str == "q":
                    continue
                while not account_str.isdigit():
                    account_str = input("> Deposit to: ")
                    if account_str == "q":
                        break
                if account_str == "q":
                    continue

            elif choice == "w":
                account_str = input("> Withdraw from: ")
                if account_str == "q":
                    continue
                while not account_str.isdigit():
                    account_str = input("> Withdraw from: ")
                    if account_str == "q":
                        break
                if account_str == "q":
                    continue

            account = int(account_str)
            account_type = ""
            while 1:
                t = input("> Account type [Checking (c) / Savings (s)]: ").lower()
                # check account
                if t == "c" or t == "s":
                    if t == "c":
                        account_type = "checking"
                    else:
                        account_type = "savings"

                    if not bank.account_available(account, account_type, False):
                        break
                    else:
                        print("> not available")
                elif t == "q":
                    break

            if t == "q":
                continue

            amount_str = input("> Amount: ")
            if amount_str == "q":
                continue
            amount_str2 = amount_str.replace(".", "", 1)
            while not amount_str2.isdigit():
                amount_str = input("> Amount: ")
                if amount_str == "q":
                    break
                amount_str2 = amount_str.replace(".", "", 1)
            if amount_str == "q":
                continue
            amount = float(amount_str)

            if choice == "d":
                bank.transaction(account, account_type.lower(), amount, "deposit")
            elif choice == "w":
                bank.transaction(account, account_type.lower(), amount, "withdraw")

        # -------------------------------------------------------------------------------------------------*
        elif choice == "t":
            account_str = input("> Account: ")
            if account_str == "q":
                continue
            while not account_str.isdigit():
                account_str = input("> Account: ")
                if account_str == "q":
                    break
            if account_str == "q":
                continue
            account = int(account_str)

            bank.display_transactions(account)

        # -------------------------------------------------------------------------------------------------*
        elif choice == "e":
            break

        # -------------------------------------------------------------------------------------------------*
        elif choice == "" or choice == "q":
            continue

        else:
            print(choice + ": command not found")


if __name__ == "__main__":
    main()
