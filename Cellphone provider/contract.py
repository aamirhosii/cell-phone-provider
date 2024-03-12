"""
CSC148, Winter 2022
Assignment 1

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

All of the files in this directory and all subdirectories are:
Copyright (c) 2022 Bogdan Simion, Diane Horton, Jacqueline Smith
"""
from typing import Union
from typing import Optional
import datetime
from math import ceil
from bill import Bill
from call import Call


# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class TermContract(Contract):
    """A term contract is a type of Contract with a
    specific start date and end date, and which requires a commitment until
    the end date. A term contract comes with an initial large term deposit
    added to the bill of the first month of the contract."""

    start: datetime.date
    bill: Optional[Bill]
    end: datetime.date
    year: int
    month: int

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive """
        Contract.__init__(self, start)
        self.end = end
        self.month = None
        self.year = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost."""
        self.bill = bill
        self.month = month
        self.year = year
        Bill.add_fixed_cost(bill, TERM_MONTHLY_FEE)
        Bill.set_rates(bill, 'term', TERM_MINS_COST)
        Bill.add_free_minutes(bill, 0)
        if self.start.month == month and self.start.year == year:
            Bill.add_fixed_cost(bill, TERM_DEPOSIT)

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        if ceil(call.duration / 60.0) <= (100 - self.bill.free_min):
            self.bill.add_free_minutes(ceil(call.duration / 60.0))

        elif ceil(call.duration / 60.0) > (100 - self.bill.free_min):
            self.bill.add_free_minutes((100 - self.bill.free_min))

        self.bill.add_billed_minutes(ceil(call.duration / 60.0)
                                     - self.bill.free_min)

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        if self.end.year < self.year:
            return self.bill.get_cost() - TERM_DEPOSIT

        elif self.end.month <= self.month and self.end.year == self.year:
            return self.bill.get_cost() - TERM_DEPOSIT
        else:
            return self.bill.get_cost()


class MTMContract(Contract):
    """
    The month-to-month contract is a Contract with no end date and
    no initial term deposit.
    This type of contract has higher rates for calls than a term contract,
    and comes with no free minutes included, but also
    involves no term commitment.
    Have a look at contract.py for all
    he rates per minute for each type of contract."""

    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive """
        Contract.__init__(self, start)

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost."""
        self.bill = bill
        Bill.add_fixed_cost(bill, MTM_MONTHLY_FEE)
        Bill.set_rates(bill, 'mtm', MTM_MINS_COST)


class PrepaidContract(Contract):
    """A prepaid contract has a start date but does not have an end date,
    and it comes with no included minutes. It has an associated balance,
    which is the amount of money the customer owes.
    If the balance is negative, this indicates that the customer has
    this much credit, that is, has prepaid this much. The customer must
    prepay some amount when signing up for the prepaid contract,
    but it can be any amount."""

    start: datetime.date
    balance: Union[int, float]
    bill: Optional[Bill]

    def __init__(self, start: datetime.date, balance: Union[int, float])\
            -> None:
        """ Create a new Contract with the <start> date, starts as inactive """
        Contract.__init__(self, start)
        self.balance = -balance

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost."""
        self.bill = bill
        Bill.set_rates(bill, 'prepaid', PREPAID_MINS_COST)
        if self.balance > -10:
            self.balance = self.balance - 25
            Bill.add_fixed_cost(bill, self.balance)
        else:
            Bill.add_fixed_cost(bill, self.balance)

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))
        x = ceil(call.duration / 60.0)
        self.balance = self.balance + x * PREPAID_MINS_COST

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        if self.balance > 0:
            return self.balance
        else:
            return 0


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
