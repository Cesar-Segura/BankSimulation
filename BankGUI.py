from calendar import month
from curses.ascii import isdigit
from os import stat
import tkinter as tk 
from tkinter import Button, Label, messagebox
from tkcalendar import Calendar
import sys
import logging
from decimal import Decimal, InvalidOperation
from datetime import datetime, date 

#from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy.orm.session import sessionmaker


from Bank import Bank
from Transactions import Transaction
from Accounts import OverdrawError, TransactionLimitError, TransactionSequenceError
from baseImport import Base


logging.basicConfig(filename='bank.log', level=logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# use option menu for a drop down 
# message box is for pop ups 
# you have to install tkCalendar 

class BankCLI:

# def handle_exception(exception, value, traceback):
#     print("Sorry! Something unexpected happened. If this problem persists please contact our support team for assistance.")
#     logging.error(f"{exception.__name__}: {repr(value)}")
#     sys.exit(1)
# ...
# self._window = tk.Tk()
# self._window.report_callback_exception = handle_exception
# ...

    def __init__(self):
        def handle_exception(exception, value, traceback):
            messagebox.showwarning("showwarning", 
            "Sorry! Something unexpected happened. If this problem persists please contact our support team for assistance.")
            logging.error(f"{exception.__name__}: {repr(value)}")
            sys.exit(1)

        self._isNew = False 
        self._session = Session() 
        self._bank = self._session.query(Bank).first() 
        logging.debug("Loaded from bank.db") 
        self._accts = {} 
        if not self._bank:
            self._isNew = True 
            new = Bank() 
            self._bank = new 
            self._session.add(new) 
            self._session.commit() 
            logging.debug("Saved to bank.db")  

         
        self._selected_account = None  

        self._window = tk.Tk()
        self._window.title("MY BANK"); 

        self._options_frame = tk.Frame(self._window)
        tk.Button(self._options_frame, 
                text="open account",  
                command=self._open_account).grid(row=1, column=1, columnspan=2)
        tk.Button(self._options_frame, 
                text="add transaction",  
                command=self._add_transaction).grid(row=1, column=3)
        tk.Button(self._options_frame, 
                text="interest and fees", 
                command=self._monthly_triggers).grid(row=1, column=4)

        self._options_frame.grid(row=0, column=1, columnspan=2)

        self._accounts_frame = tk.Frame(self._window) 
        self.display_accounts()
        # testbutton = Button(self._accounts_frame, text="test").grid(row=1, column=1) 
        self._accounts_frame.grid(row=1, column=1, columnspan=2) 

        self._trans_frame = tk.Frame(self._window) 

        self._window.report_callback_exception = handle_exception
        
        self._window.mainloop() 

    def display_accounts(self):
        if (self._accounts_frame):
            self._accounts_frame.destroy() 
        self._accounts_frame = tk.Frame(self._window) 
        all = self._bank.show_accounts() 
        row = 0 
        for account in all:  
            if account == self._selected_account: 
                self._accts[account._account_number] = tk.StringVar(value=account.__str__())
                this_butt = tk.Button(self._accounts_frame, text=account,  
                textvariable=self._accts[account._account_number],
                command= lambda acc=account: self._select(acc))
                this_butt.configure(fg="blue")
                this_butt.grid(row=row, column=1)
            elif account._account_number not in self._accts: 
                self._accts[account._account_number] = tk.StringVar(value=account.__str__())
                this_butt = tk.Button(self._accounts_frame, text=account,  
                textvariable=self._accts[account._account_number],
                command= lambda acc=account: self._select(acc))
                this_butt.configure(fg="white")
                this_butt.grid(row=row, column=1)
            else:
                self._accts[account._account_number].set(account.__str__())
                this_butt = tk.Button(self._accounts_frame, text=account,  
                textvariable=self._accts[account._account_number],
                command= lambda acc=account: self._select(acc))
                this_butt.configure(fg="white")
                this_butt.grid(row=row, column=1)
            row +=1 
        self._accounts_frame.grid(row=1, column=1, columnspan=2)


    # def _summary(self):
    #     for x in self._bank.show_accounts():
    #         print(x)


    # def _quit(self):
    #     sys.exit(0)

    @staticmethod
    def change_date(total, tup):
        finaldate = ""
        i = 0
        month = ""
        while total[i] != '/':
            month += total[i] 
            i += 1
        if (len(month) == 1):
            month = "0" + month
        k = i + 1
        day = ""
        while total[k] != '/':
            day += total[k]
            k += 1
        if len(day) == 1:
            day = "0" + day 
        
        year = (str) (tup[1])
        finaldate = year + "-" + month + "-" + day 
        return finaldate 
        

    def _add_transaction(self):

        def get_trans():
            amt = None
            while not amt:
                try:
                    amt = Decimal(amount.get()) 
                except InvalidOperation:
                    messagebox.showwarning("showwarning", "Please try again with a valid dollar amount.")
                    return 
                    # print("Please try again with a valid dollar amount.")
            
            date = None 
            while not date:
                try:
                    temp = BankCLI.change_date(cal.get_date(), cal.get_displayed_month())  
                    date = datetime.strptime(temp, "%Y-%m-%d").date()
                except ValueError:
                    messagebox.showwarning("showwarning", "Please try again with a valid date in the format YYYY-MM-DD.")
                    return 
                    # print("Please try again with a valid date in the format YYYY-MM-DD.")

            try:
                self._selected_account.add_transaction(amt, self._session, date)
                self._session.commit() 
                logging.debug("Saved to bank.db") 
            except AttributeError:
                messagebox.showwarning("showwarning", "This command requires that you first select an account.")
                return 
                # print("This command requires that you first select an account.")
            except OverdrawError:
                messagebox.showwarning("showwarning", "This transaction could not be completed due to an insufficient account balance.")
                return 
                # print("This transaction could not be completed due to an insufficient account balance.")
            except TransactionLimitError:
                messagebox.showwarning("showwarning", "This transaction could not be completed because the account has reached a transaction limit.")
                return 
                #print("This transaction could not be completed because the account has reached a transaction limit.")
            except TransactionSequenceError as e:
                messagebox.showwarning("showwarning", f"New transactions must be from {e.latest_date} onward.")
                return 
                # print(f"New transactions must be from {e.latest_date} onward.")
            
            l1.destroy()
            e1.destroy()
            choosedate.destroy()
            datelabel.destroy()
            enter.destroy()
            cal.destroy() 
            if self._selected_account:
                self._list_transactions() 
            self.display_accounts() 

        def in_handler(event):
            event = event.char
            if len(event) == 0:
                return 
            if isdigit(event) or event == '.' or event == '-':
                enter['state'] = tk.NORMAL 
            else:
                enter['state'] = tk.DISABLED

        cal = Calendar(self._options_frame, selectmode = 'day', year = 2022, month = 3, day = 13)
        cal.grid(row=4, column=3) 

        def grab_date():
            datelabel.config(text=cal.get_date())   
        

        amount = tk.StringVar()   
        l1 = tk.Label(self._options_frame, text="Amount:")
        l1.grid(row=2, column=3)
        e1 = tk.Entry(self._options_frame, textvariable=amount)   
        e1.grid(row=2, column=4) 
        e1.bind('<Key>', lambda i: in_handler(i))

        choosedate = Button(self._options_frame, text="Choose Date", command=grab_date)
        choosedate.grid(row=4, column=4) 
        datelabel = Label(self._options_frame, text="") 
        datelabel.grid(row=5, column=4) 

        enter = tk.Button(self._options_frame, text="Enter", command=get_trans, state=tk.DISABLED) 
        enter.grid(row=5, column=4)  


    def _open_account(self):
        self._isNew == False 
        def open():
            acct_type = select
            amt = None
            while not amt:
                # initial_deposit = input("Initial deposit amount?\n>")
                try:
                    amt = Decimal(init_amt.get())  
                except InvalidOperation:
                    messagebox.showwarning("showwarning", "Please try again with a valid dollar amount.")
            try:  
                self._bank.add_account(acct_type.get(), amt, self._session)
                self._session.commit() 
                logging.debug("Saved to bank.db") 
            except OverdrawError:
                messagebox.showwarning("showwarning", "This transaction could not be completed due to an insufficient account balance.")
            l1.destroy()
            e1.destroy()
            enter.destroy()
            menu.destroy() 
            self.display_accounts()

        def in_handler(event):
            event = event.char
            if len(event) == 0:
                return 
            if isdigit(event) or event == '.' or event == '-':
                enter['state'] = tk.NORMAL 
            else:
                enter['state'] = tk.DISABLED

        init_amt = tk.StringVar()   
        l1 = tk.Label(self._options_frame, text="Initial deposit:")
        l1.grid(row=2, column=1)
        e1 = tk.Entry(self._options_frame, textvariable=init_amt)  
        e1.grid(row=3, column=1) 
        e1.bind('<Key>', lambda i: in_handler(i)) 
        options = ("checking", "savings") 
        select = tk.StringVar(value="") 
        enter = tk.Button(self._options_frame, text="Enter", command=open)
        enter.grid(row=4, column=2)  

        menu = tk.OptionMenu(self._options_frame, select, *options)  
        menu.grid(row=4, column=1) # sticky=tk.W


    def _select(self, account):
        # num = int(input("Enter account number\n>"))
        # self._selected_account = self._bank.get_account(num)
        self._selected_account = account 
        self._list_transactions()  
        self.display_accounts() 
        



    def _monthly_triggers(self):
        try:
            self._selected_account.assess_interest_and_fees(self._session)
            self._session.commit()  
            logging.debug("Saved to bank.db") 
            logging.debug("Triggered fees and interest")
            self._list_transactions() 
            self.display_accounts() 
        except AttributeError as e:
            messagebox.showwarning("showwarning", "This command requires that you first select an account.")
            return 
            # print("This command requires that you first select an account.")
        except TransactionSequenceError as e:
            messagebox.showwarning("showwarning", f"Cannot apply interest and fees again in the month of {e.latest_date.strftime('%B')}.")
            return 
            # print(f"Cannot apply interest and fees again in the month of {e.latest_date.strftime('%B')}.")


    def _list_transactions(self):
        try:
            # for x in self._selected_account.get_transactions():
            #     print(x) 
            if (self._trans_frame):
                self._trans_frame.destroy() 
            self._trans_frame = tk.Frame(self._window) 
            for i, x in enumerate(self._selected_account.get_transactions()):
                if x._amt < 0:
                    color = "red"
                else:
                    color = "green" 
                tk.Label(self._trans_frame, bg=color, text=x.__str__()).grid(row=i, column=3) 
            self._trans_frame.grid(row=1, column=4, columnspan=2)
        except AttributeError as e:
            messagebox.showwarning("showwarning", "This command requires that you first select an account.")
            return 
            # print("This command requires that you first select an account.")




if __name__ == "__main__":
    try:
        engine = sqlalchemy.create_engine(f"sqlite:///bank.db")
        Base.metadata.create_all(engine)

        Session = sessionmaker()
        Session.configure(bind=engine) 
        BankCLI() 
    except Exception as e: 
        # print("Sorry! Something unexpected happened. If this problem persists please contact our support team for assistance.")
        messagebox.showwarning("showwarning", 
        "Sorry! Something unexpected happened. If this problem persists please contact our support team for assistance.")
        logging.error(str(e.__class__.__name__) + ": " + repr(str(e)))

