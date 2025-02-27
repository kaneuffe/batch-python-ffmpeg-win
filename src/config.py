# -------------------------------------------------------------------------
#
# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
# ----------------------------------------------------------------------------------
# The example companies, organizations, products, domain names,
# e-mail addresses, logos, people, places, and events depicted
# herein are fictitious. No association with any real company,
# organization, product, domain name, email address, logo, person,
# places, or events is intended or should be inferred.
# --------------------------------------------------------------------------

# Global constant variables (Azure Storage account/Batch details)

# import "config.py" in "batch_python_ffmpeg_win.py"

# Update the Batch and Storage account credential strings below with the values
# unique to your accounts. These are used when constructing connection strings
# for the Batch and Storage client objects.

# subscription ID
SUBSCRIPTION_ID = ''
# Resource group name
RESOURCE_GROUP_NAME = ''
# Batch account details
BATCH_ACCOUNT_NAME = ''
BATCH_ACCOUNT_URL = 'https://'
# Storage account name
STORAGE_ACCOUNT_NAME = ''
# Pool name
POOL_ID = ''
# Compute node count
POOL_NODE_COUNT = 2
LOW_PRIORITY_POOL_NODE_COUNT = 0
# Compute VM size
POOL_VM_SIZE = 'ffmpeg_pool'
# Job name
JOB_ID = 'ffmpeg_job'
# Subnet ID Azure resource (/subscription/.../virtualNetworks/.../subnets/...)
SUBNET_ID = ''
# User managed identity Azure resouce (/subscription/.../userAssignedIdentities/...)
USER_MANAGED_ID=''
# Application name
APP_NAME='ffmpeg'
# Azure Application Resource ID (/subscriptions/.../providers/Microsoft.Batch/batchAccounts/.../applications/...)
APP_ID=''
# Part of the path to the executable between %AZ_BATCH_APP_PACKAGE_{APP_NAME}% and the executable 
# Example 'ffmpeg-master-latest-win64-gpl-shared/bin'
APP_PATH_TO_EXECUTABLE=''