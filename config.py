# config.py

BOT_TOKEN = 'MTI1NTI3MjAyMDQ3NjgyMTUzNQ.GkVw5g.7xI6KrQtdkfhP2xAdCVcU75CdrGc_4ML-WACXU'
ADMIN_IDS = [170855291636809728]  # List of admin user IDs
DB_FILE = 'user_data.db'
MIN_TIP_AMOUNT = 0.1  # Minimum tip amount
MAX_TIP_AMOUNT = 1000  # Maximum tip amount
BOT_USER_ID = '1255272020476821535'
BOT_WALLET = 'stest1qqqqqqrvzt4wnvwumhxalcukr8v2tp0sfnym0rshcqkxt'
BOT_PUBKEY = 'Chs2pYW1Awr29xSN2uD4Vm8q1mTmp3v8oJiAMevthML7'

# Network configuration
USE_TESTNET = True  # Set to False for mainnet

# Network-specific configurations
MAINNET_CONFIG = {
    'HRP': 'sm',
    'ADDRESS_PREFIX': 'sm1',
    'ADDRESS_LENGTH': 48
}

TESTNET_CONFIG = {
    'HRP': 'stest',
    'ADDRESS_PREFIX': 'stest1',
    'ADDRESS_LENGTH': 51
}

# Use the appropriate config based on the network
NETWORK_CONFIG = TESTNET_CONFIG if USE_TESTNET else MAINNET_CONFIG