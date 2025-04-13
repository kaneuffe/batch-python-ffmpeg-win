# batch-python-ffmpeg-win
This is an updated version of the batch-python-ffmpeg-tutorial (https://github.com/Azure-Samples/batch-python-ffmpeg-tutorial) and also modified to run on a Windows OS.

To run this python application several prerequisits are required.  

# Prerequisits

- Azure Batch Account in User Subscription Mode and with a System Assigned managed Identity
- Dedicated General Purpose v2 Storage Account linked to the Batch Account with a User Managed Identity assigned as a Node Identity Referenece.
- Entra ID RBAC Storage Blob Data Contributer role for the batch for the Batch System Managed Indentity and the User Managed Identity on the batch-linked Storage Account. 
- VNET with a subnet for the batch pool compute nodes.
- The ffmpeg application for Windows added as an Application Pakage available through information provided at https://ffmpeg.org/ .
- Python 3.12 version
- Entra ID RBAC role Azure Batch Account Contributer for the entity that runs the script e.g. a user after doing an <i>az login</i>.   

# Configuration file variables

All Variables to run the demo are defined in the <it>config.py</it> file within the <it>src</it> subdirectory.


| Variable | Value |
|-|-|
| SUBSCRIPTION_ID | Subscription ID |
| RESOURCE_GROUP_NAME | Name of the resource group |
| BATCH_ACCOUNT_NAME | Name of the batch account |
| BATCH_ACCOUNT_URL | URL of the batch account (= 'https://...') |
| STORAGE_ACCOUNT_NAME | Name of the storage account |
| POOL_ID | Name of the batch compute node pool (e.g. 'ffmpeg_pool') | 
| POOL_NODE_COUNT | Number of PAYG (Pay As You Go) compute nodes within the pool |
| LOW_PRIORITY_POOL_NODE_COUNT | Number of low priority compute nodes within the pool |
| POOL_VM_SIZE | Compute node VM SKU (e.g. 'STANDARD_F1') |
| JOB_ID | Name of the compute job (e.g. 'ffmpeg_job') |
| SUBNET_ID | Subnet Azure resource ID ('/subscription/.../virtualNetworks/.../subnets/...)' |
| USER_MANAGED_ID | User managed identity Azure resouce ('/subscription/.../userAssignedIdentities/...' |
| APP_NAME | Name of the application (e.g. 'ffmpeg') |
| APP_ID | Azure Application Resource ID ('/subscriptions/.../providers/Microsoft.Batch/batchAccounts/.../applications/...)' |
| APP_PATH_TO_EXECUTABLE | Part of the path to the executable between %AZ_BATCH_APP_PACKAGE_{APP_NAME}% and the executable, e.g. 'ffmpeg-master-l atest-win64-gpl-shared/bin' ) |
