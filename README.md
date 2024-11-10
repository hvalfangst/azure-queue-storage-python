# Python API integrated with Azure Storage Queues

## Requirements

- **Platform**: x86-64, Linux/WSL
- **Programming Language**: [Python 3](https://www.python.org/downloads/)
- **Cloud Account**: [Azure](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account)
- **Resource provisioning**: [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/)


## Allocate resources

The shell script [provision_resources.sh](infra/provision_resources.sh) provisions Azure resources by calling functions defined in the Azure CLI, which in turn
results in HTTP request being issued to the resource-specific API on Azure. 

The shell script expects that you have a file named **config.env** in the [client](client) root folder. Said
file has (naturally) been added to our [.gitignore](.gitignore) as it does contain some sensitive information. 

The below screen-dump illustrates the expected structure of aforementioned **config.env** file.

![screenshot](images/config_env.png)


