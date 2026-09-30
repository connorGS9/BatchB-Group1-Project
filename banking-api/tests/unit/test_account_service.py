# tests/unit/test_account_service.py
# Unit tests for AccountService, with the repositories mocked (see conftest.py).
#
# TODO: overdraft protection (AccountService.adjust_balance)
#   - withdrawing less than the balance succeeds and saves the new balance
#   - withdrawing exactly the balance leaves 0.00 and succeeds
#   - withdrawing more than the balance raises ValidationError, repo.update not called
#   - adjusting an inactive account raises ValidationError
#   - adjusting a missing account raises NotFoundError
#
# TODO: create_account
#   - negative opening balance raises ValidationError
#   - unknown customer_id raises ValidationError
