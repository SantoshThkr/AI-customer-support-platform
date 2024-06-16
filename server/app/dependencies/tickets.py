from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Ticket, User


def get_accessible_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Ticket:
    """Load a ticket the current user is allowed to see.

    Customers get a 404 for other customers' tickets so ticket ids can't be probed.
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or (not user.is_staff and ticket.customer_id != user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket
