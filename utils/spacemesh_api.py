import grpc
from config import API_ENDPOINT, BOT_WALLET, BOT_PUBKEY
from spacemesh.v1 import TransactionService_pb2_grpc, TransactionService_pb2
from spacemesh.v1 import GlobalStateService_pb2_grpc, GlobalStateService_pb2
from spacemesh.v1 import types_pb2
import binascii

def get_grpc_channel():
    return grpc.insecure_channel(API_ENDPOINT)

def send_transaction(recipient, amount):
    channel = get_grpc_channel()
    try:
        # Create transaction stub
        stub = TransactionService_pb2_grpc.TransactionServiceStub(channel)

        # Create transaction
        transaction = types_pb2.Transaction(
            principal=types_pb2.AccountId(address=BOT_WALLET),
            template=types_pb2.AccountId(address="sm1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqg56ypy7"),  # SingleSig template
            method=16,  # Spend method
            nonce=get_nonce(),
            gas_price=1,
            max_gas=36090,  # Fixed gas amount, can be made configurable
            max_spend=amount
        )

        # Sign transaction (placeholder, implement actual signing)
        signed_transaction = sign_transaction(transaction)

        # Submit transaction
        response = stub.SubmitTransaction(TransactionService_pb2.SubmitTransactionRequest(
            transaction=signed_transaction
        ))

        return response

    except grpc.RpcError as e:
        print(f"RPC error: {e}")
        return None
    finally:
        channel.close()

def get_nonce(): # Get the nonce for the bot's account (not sure about this yet)
    channel = get_grpc_channel()
    try:
        # Create global state stub
        stub = GlobalStateService_pb2_grpc.GlobalStateServiceStub(channel)

        # Get account state
        response = stub.GetAccount(GlobalStateService_pb2.GetAccountRequest(
            id=types_pb2.AccountId(address=BOT_WALLET)
        ))

        return response.account_state.nonce
    except grpc.RpcError as e:
        print(f"RPC error: {e}")
        return None
    finally:
        channel.close()
    pass

def sign_transaction(transaction):
    # Placeholder for actual signing logic
    pass