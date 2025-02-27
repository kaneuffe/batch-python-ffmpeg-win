# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# The demo requires Azure Entra ID authentication and the Azure Batch Account Contributer role assigned to run the python script.
# The script requires and already created Autostorage Account for the batch account. 
# The script requires a subnet within a VNET to avoid public IPs.
# This deployment is compatible with a private endpoint for the Atorage Account within the same VNET.
# The System Managed ID of the batch account must have the Storage Blob Data Contributor role to the storage account.
# The User Managed ID used for the compute nodes must have the Storage Blob Data Contributor role to the storage account.
# The pool will be created within the pre-created subnet.
# The script assumes that the ffmpeg application package is already created in the batch account.
# The script assumes that the input files are in the InputFiles directory.
# The script requires the Azure Batch Management API access to be able to assign the user managed identity to the pool
# Due to the fact the the batch service client does not support Entra ID yet we will use the AzureIdentityCredentialAdapter as a work around.
"""
Create a pool of nodes to output text files from azure blob storage.
"""

import datetime
import os
import sys
import time

#from msrestazure.tools import resource_id
import config

from azure.identity import DefaultAzureCredential
from azure.mgmt.batch import BatchManagementClient

from azure_identity_credential_adapter import AzureIdentityCredentialAdapter
from azure.storage.blob import BlobServiceClient
#, ContainerClient, BlobBlock, BlobClient, StandardBlobTier

from azure.batch import BatchServiceClient
#from azure.batch.batch_auth import SharedKeyCredentials
import azure.batch.models as batchmodels
from azure.core.exceptions import ResourceExistsError


sys.path.append('.')
sys.path.append('..')

# Update the Batch and Storage account credential strings in config.py with values
# unique to your accounts. These are used when constructing connection strings
# for the Batch and Storage client objects.

def main():

    start_time = datetime.datetime.now().replace(microsecond=0)
    print(f'Sample start: {start_time}')
    print()

    # Create batch management client required fro the pool creation
    # # For other authentication approaches, please see: https://pypi.org/project/azure-identity/
    batch_client = BatchManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=config.SUBSCRIPTION_ID
    )
   
    # Create credential object for the Batch and Storage clients based on the az login credentials on the machine that runs the script.
    credential=DefaultAzureCredential()

    # Define storage account URL
    account_url = f"https://{config.STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
    
    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient(account_url, credential=credential)

    # Use the blob service client to create the containers in Azure Storage if they
    # don't yet exist.

    input_container_name = 'input'
    output_container_name = 'output'

    try:
        input_container_client = blob_service_client.create_container(input_container_name)
    except ResourceExistsError:
        print('Input container already exists!')
    except Exception as e:
        print(f'An error occurred: {e}')
    else:
        print(f'Container [{input_container_name}] created.')

    try:
        output_container_client = blob_service_client.create_container(output_container_name)
    except ResourceExistsError:
        print('Output container already exists!')
    except Exception as e:
        print(f'An error occurred: {e}')
    else:
        print(f'Container [{output_container_name}] created.')

    # Create a list of all MP4 files in the InputFiles directory.
    input_file_paths = []

    for folder, subs, files in os.walk(os.path.join(sys.path[0], 'InputFiles')):
        for filename in files:
            if filename.endswith(".mp4"):
                input_file_paths.append(os.path.abspath(
                    os.path.join(folder, filename)))

    # Upload the input files. This is the collection of files that are to be processed by the tasks.
    input_files = [
        upload_file_to_container(blob_service_client, input_container_name, file_path)
        for file_path in input_file_paths]

    # Create a batch service client.
    try:
        batch_account_url=f'{config.BATCH_ACCOUNT_URL}'
        batch_service_client = get_batch_client(credential, batch_account_url)        
    except Exception as e:
        print(f'An error occurred: {e}')
    
    # Crteate the pool, job and tasks
    try:
        # Create the pool that will contain the compute nodes that will execute the tasks.
        create_batch_pool(batch_client,config.POOL_ID)
        
        # Create the job that will run the tasks.
        create_job(batch_service_client, config.JOB_ID, config.POOL_ID)

        # Add the tasks to the job. Pass the input files and a blob service client
        # to the storage container for output files.
        add_tasks(batch_service_client, config.JOB_ID, input_files, blob_service_client, output_container_name)
        # Pause execution until tasks reach Completed state.
        wait_for_tasks_to_complete(batch_service_client,
                                   config.JOB_ID,
                                   datetime.timedelta(minutes=30))

        print("Success! All tasks reached the 'Completed' state within the "
              "specified timeout period.")

    except batchmodels.BatchErrorException as err:
        print_batch_exception(err)
        raise

    finally:
        # Clean up storage resources
        print(f'Deleting container [{input_container_name}]...')
        blob_service_client.delete_container(input_container_name)
 

        # Print out some timing info
        end_time = datetime.datetime.now().replace(microsecond=0)
        print()
        print(f'Sample end: {end_time}')
        print(f'Elapsed time: {end_time - start_time}')
        print()

        # Clean up Batch resources (if the user so chooses).
        if query_yes_no('Delete job?') == 'yes':
            batch_service_client.job.delete(config.JOB_ID)

        if query_yes_no('Delete pool?') == 'yes':
            pool = batch_client.pool.begin_delete(
                config.RESOURCE_GROUP_NAME,
                config.BATCH_ACCOUNT_NAME,
                config.POOL_ID
            ).result()
            print(f"Delete pool:\n{config.POOL_ID}") 

def query_yes_no(question: str, default: str = "yes") -> str:
    """
    Prompts the user for yes/no input, displaying the specified question text.

    :param str question: The text of the prompt for input.
    :param str default: The default if the user hits <ENTER>. Acceptable values
    are 'yes', 'no', and None.
    :return: 'yes' or 'no'
    """
    valid = {'y': 'yes', 'n': 'no'}
    if default is None:
        prompt = ' [y/n] '
    elif default == 'yes':
        prompt = ' [Y/n] '
    elif default == 'no':
        prompt = ' [y/N] '
    else:
        raise ValueError(f"Invalid default answer: '{default}'")

    choice = default

    while 1:
        user_input = input(question + prompt).lower()
        if not user_input:
            break
        try:
            choice = valid[user_input[0]]
            break
        except (KeyError, IndexError):
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

    return choice

def print_batch_exception(batch_exception: batchmodels.BatchErrorException):
    """
    Prints the contents of the specified Batch exception.

    :param batch_exception:
    """
    print('-------------------------------------------')
    print('Exception encountered:')
    if batch_exception.error and \
            batch_exception.error.message and \
            batch_exception.error.message.value:
        print(batch_exception.error.message.value)
        if batch_exception.error.values:
            print()
            for mesg in batch_exception.error.values:
                print(f'{mesg.key}:\t{mesg.value}')
    print('-------------------------------------------')

def get_batch_client(credentials: DefaultAzureCredential, batch_end_point: str):
    """Get the Batch client for a specified subscription and resource group.
 
    :param credentials: Azure credentials object
    :param batch_end_point : The Batch account URL
    :return: Batch client
    :rtype: :class:`azure.mgmt.batch.BatchManagementClient`
    """
    client = BatchServiceClient(
        AzureIdentityCredentialAdapter(
            credentials, resource_id="https://batch.core.windows.net/"
        ),
        batch_end_point,
    )
    return client

def upload_file_to_container(blob_service_client: BlobServiceClient, container_name: str, local_file_path: str):
    """Upload input file to blob container
 
    :param blob_service_client: Azure credentials object
    :param comtainer_name: Input container name on the storage account  
    :param local_file_path : Local file path for the input file
    :return: ResourceFile object 
    """


    blob_name = os.path.basename(local_file_path)
    
    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container_name, blob_name)
 
    # Upload the file to the blob container
    with open(file=local_file_path, mode="rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    print(f"\nUploading file {local_file_path} to Azure storage container {container_name} as blob:\n")
    
    return batchmodels.ResourceFile(auto_storage_container_name=container_name, blob_prefix=blob_name)

def create_batch_pool(my_batch_client, pool_id: str):
    """ Create a pool of compute nodes.
    param: my_batch_client: BatchManagementClient object
    param: pool_id: The ID of the pool to create
    return: None
    """
    pool = my_batch_client.pool.create(
        config.RESOURCE_GROUP_NAME,
        config.BATCH_ACCOUNT_NAME,
        pool_id, 
        {
            "properties": {
                "vmSize": "STANDARD_F1s",
                "deploymentConfiguration": {
                    "virtualMachineConfiguration": {
                        "imageReference": {
                            "publisher": "microsoftwindowsserver",
                            "offer": "windowsserver",
                            "sku": "2019-datacenter",
                            "version": "latest" 
                        },
                        "nodeAgentSkuId": "batch.node.windows amd64"
                    }
                },
                "scaleSettings": {
                    "autoScale": {
                        "formula": "$TargetDedicatedNodes=2",
                        "evaluationInterval": "PT5M"
                    }
                }
            },
            "networkConfiguration": {
                "subnetId": config.SUBNET_ID,
                "dynamicVNetAssignmentScope": None,
                "publicIPAddressConfiguration": {
                    "provision": "nopublicipaddresses"
                },
                "enableAcceleratedNetworking": True
            },         
            "startTask": {
                "commandLine": "cmd /c SET",
                "userIdentity": {
                "username": None,
                "autoUser": {
                    "scope": "pool",
                    "elevationLevel": "nonadmin"
                    }
                },
                "maxTaskRetryCount": 3,
                "waitForSuccess": True
            },
            "applicationPackages": [
                {
                    "id": f"{config.APP_ID}",
                    "version": "2025-02-13"
                },                  
            ],
            "taskSlotsPerNode": 2,
            "taskSchedulingPolicy": {
                "nodeFillType": "pack"
            },
            "identity": {
                "type": "UserAssigned",
                "userAssignedIdentities": {
                    config.USER_MANAGED_ID: {}
                }         
            },
            "targetNodeCommunicationMode": "simplified"
        }
    ),
    print(f"Create pool:\n{pool_id}")
        
def create_job(batch_service_client: BatchServiceClient, job_id: str, pool_id: str):
    """
    Creates a job with the specified ID, associated with the specified pool.

    :param batch_service_client: A batch service client.
    :param str job_id: The ID for the job.
    :param str pool_id: The ID for the pool.
    """
    print(f'Creating job [{job_id}]...')

    job = batchmodels.JobAddParameter(
        id=job_id,
        pool_info=batchmodels.PoolInformation(pool_id=pool_id))

    batch_service_client.job.add(job)

def add_tasks(batch_service_client: BatchServiceClient, job_id: str, resource_input_files: list, blob_service_client: BlobServiceClient, output_container_name: str):
    """
    Adds a task for each input file in the collection to the specified job.

    :param batch_service_client: A Batch service client.
    :param str job_id: The ID of the job to which to add the tasks.
    :param list resource_input_files: A collection of input files. One task will be
     created for each input file.
    """

    print(f'Adding {resource_input_files} tasks to job [{job_id}]...')

    tasks = []

    for idx, input_file in enumerate(resource_input_files):
        input_file_path = input_file.blob_prefix
        output_file_path = "".join((input_file_path).split('.')[:-1]) + '.mp3'
        command = f"cmd /v /c \"%AZ_BATCH_APP_PACKAGE_{config.APP_NAME}%/{config.APP_PATH_TO_EXECUTABLE}/ffmpeg.exe -i {input_file_path} {output_file_path}\""
        tasks.append(batchmodels.TaskAddParameter(
            id=f'Task{idx}',
            command_line=command,
            resource_files=[input_file],
            output_files=[batchmodels.OutputFile(
                file_pattern=output_file_path,
                destination=batchmodels.OutputFileDestination(container=batchmodels.OutputFileBlobContainerDestination(container_url=f"{blob_service_client.url}/{output_container_name}", identity_reference=batchmodels.ComputeNodeIdentityReference(resource_id=config.USER_MANAGED_ID))),
                upload_options=batchmodels.OutputFileUploadOptions(
                    upload_condition=batchmodels.OutputFileUploadCondition.task_success)
            )]
        ))

    # upload_file_to_container(blob_service_client, output_container_name, file_path)

    batch_service_client.task.add_collection(job_id, tasks)

def wait_for_tasks_to_complete(batch_service_client: BatchServiceClient, job_id: str, timeout: datetime.timedelta):
    """
    Returns when all tasks in the specified job reach the Completed state.

    :param batch_service_client: A Batch service client.
    :param job_id: The id of the job whose tasks should be to monitored.
    :param timeout: The duration to wait for task completion. If all
    tasks in the specified job do not reach Completed state within this time
    period, an exception will be raised.
    """

    timeout_expiration = datetime.datetime.now() + timeout

    print(f"Monitoring all tasks for 'Completed' state, timeout in {timeout}...", end='')

    while datetime.datetime.now() < timeout_expiration:
        print('.', end='')
        sys.stdout.flush()
        tasks = batch_service_client.task.list(job_id)

        incomplete_tasks = [task for task in tasks if
                            task.state != batchmodels.TaskState.completed]
        if not incomplete_tasks:
            print()
            return True
        else:
            time.sleep(1)

    print()
    raise RuntimeError("ERROR: Tasks did not reach 'Completed' state within "
                       "timeout period of " + str(timeout))


if __name__ == '__main__':
    main()