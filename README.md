# batch-python-ffmpeg-win
This is an updated version of the batch-python-ffmpeg-tutorial (https://github.com/Azure-Samples/batch-python-ffmpeg-tutorial) and also modified to run on a Windows OS.

To run this python application several prerequisits are required.  

# Prerequisits

- Azure Batch Account in User Subscription Mode and with a System Assigned managed Identity
- Dedicated General Purpose v2 Storage Account linked to the bAtch Account with a User Managed Identity assigned as a Node Identity Referenece.
- Entra ID RBAC Storage Blob Data Contributer role for the batch for the Batch System Managed Indentity and the User Managed Identity on the batch-linked Storage Account. 
- VNET with a subnet for the batch pool compute nodes.
- The ffmpeg application for Windows added as an Application Pakage available through information provided at https://ffmpeg.org/ .
  
   
