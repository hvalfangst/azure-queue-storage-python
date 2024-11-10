# Python API integrated with Azure Storage Queues

## Requirements

- **Platform**: x86-64, Linux/WSL
- **Programming Language**: [Python 3](https://www.python.org/downloads/)
- **Cloud Account**: [Azure](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account)
- **Resource provisioning**: [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/)


## Allocate resources

The shell script [provision_resources.sh](infra/provision_resources.sh) provisions Azure resources by calling functions defined in the Azure CLI, which in turn
results in HTTP request being issued to the resource-specific API on Azure. 

It will create the following hierarchy of resources:

```mermaid
graph TD
    A[Subscription]
    A --> B[Resource Group]
    B --> C[Storage Account]
    C --> D[Container]
    C --> E[Queue]

    A -->|Contains| B
    B -->|Contains| C
    C -->|Contains| D
    C -->|Contains| E
```

The script expects that you have a file named **config.env** in the root of your [client](client) directory. Said
file has been added to our [.gitignore](.gitignore) as it does contain sensitive information. **Please** create this file. The below snippet illustrates its structure. Naturally. 


### 'client/config.env' expected structure
```bash
LOCATION=northeurope
RESOURCE_GROUP_NAME=hvalfangstresourcegroup
STORAGE_ACCOUNT_NAME=hvalfangststorageaccount
STORAGE_CONTAINER_NAME=hvalfangstcontainer
QUEUE_NAME=hvalfangstqueue
TENANT_ID={TO_BE_SET_BY_YOU_MY_FRIEND}
SUBSCRIPTION_ID={TO_BE_SET_BY_YOU_MY_FRIEND}
USER_PRINCIPAL_NAME={TO_BE_SET_BY_YOU_MY_FRIEND}
```




## Running API

The shell script [run_client](client/run_client.sh) creates a new virtual environment based on our [requirements](client/requirements.txt) file and serves our 
API on port 8000 using uvicorrn.



A [Postman Collection](client/postman/hvalfangst-azure-queue-storage.postman_collection.json) has been provided,
which contains example requests for the CRUD operations that are defined in our [queue router](client/routers/queue.py).


