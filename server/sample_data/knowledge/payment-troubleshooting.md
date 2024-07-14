# Payment Troubleshooting

## Card declined

Declines are decided by the customer's bank. Common reasons:

- insufficient funds or a card limit,
- the bank blocking an international or online payment,
- an expired card or wrong billing postcode.

Ask the customer to contact their bank or use a different card. We never see the full decline reason.

## Failed renewals

If a renewal payment fails we retry three times over seven days and email the billing contact each time. After the final failed attempt the workspace switches to read-only mode. Data is kept for 60 days.

To restore access the customer updates the card under **Settings → Billing → Payment method** and clicks **Retry payment**.

## 3-D Secure / SCA

Some European cards require an extra confirmation step. If the confirmation window does not appear, ask the customer to disable pop-up blockers and try again.

## Paying by invoice

Annual plans over 20 seats can pay by bank transfer. Payment terms are 30 days. Requests for invoice billing should be routed to the BILLING category.
