# tests/unit/test_transaction_service.py
# Unit tests for TransactionService.transfer, with the repositories mocked (see conftest.py).
#
# TODO: transfer failure scenarios (each must raise and leave balances untouched)
#   - insufficient funds in the source account
#   - negative amount
#   - zero amount
#   - same source and target account
#   - source or target account inactive
#   - source or target account does not exist (NotFoundError)
#
# TODO: successful transfer
#   - source debited, target credited by the amount
#   - a TRANSFER transaction is recorded via transaction_repo.add
