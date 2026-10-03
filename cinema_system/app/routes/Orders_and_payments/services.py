from app import db
from app.models import Ticket

def get_total_amount(tickets):
    total_amount = 0
    for ticket in tickets:
        total_amount += ticket.ticket_price
    return total_amount