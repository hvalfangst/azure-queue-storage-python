#!/bin/bash

echo "Starting Azure resource provisioning script..."

# Load values from config.env
CONFIG_FILE="$(dirname "$0")/infra_config.env"
if [ -f "$CONFIG_FILE" ]; then
  echo "Loading configuration from $CONFIG_FILE..."
  source "$CONFIG_FILE"
else
  echo "Configuration file $CONFIG_FILE not found!"
  exit 1
fi

echo -e "\nSetting subscription context to $SUBSCRIPTION_ID..."
az account set --subscription "$SUBSCRIPTION_ID"
if [ $? -ne 0 ]; then
  echo "Failed to set subscription context."
  exit 1
fi
echo "Subscription context set successfully."

# Create the resource group
echo -e "\nCreating resource group: $RESOURCE_GROUP_NAME in location $LOCATION..."
az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION"
if [ $? -ne 0 ]; then
  echo "Failed to create resource group: $RESOURCE_GROUP_NAME."
  exit 1
fi
echo "Resource group $RESOURCE_GROUP_NAME created successfully."

# Create the storage account
echo -e "\nCreating storage account: $STORAGE_ACCOUNT_NAME in resource group $RESOURCE_GROUP_NAME..."
az storage account create --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --location "$LOCATION" --sku Standard_LRS
if [ $? -ne 0 ]; then
  echo "Failed to create storage account: $STORAGE_ACCOUNT_NAME."
  exit 1
fi
echo "Storage account $STORAGE_ACCOUNT_NAME created successfully."


# Get the storage account key
echo -e "\nRetrieving account key for storage account $STORAGE_ACCOUNT_NAME..."
ACCOUNT_KEY=$(az storage account keys list --resource-group "$RESOURCE_GROUP_NAME" --account-name "$STORAGE_ACCOUNT_NAME" --query "[0].value" -o tsv)
if [ $? -ne 0 ]; then
  echo "Failed to retrieve account key for storage account: $STORAGE_ACCOUNT_NAME."
  exit 1
fi

# Create the storage queue
echo -e "\nCreating storage queue: $QUEUE_NAME in storage account $STORAGE_ACCOUNT_NAME..."
az storage queue create --name "$QUEUE_NAME" --account-name "$STORAGE_ACCOUNT_NAME" --account-key "$ACCOUNT_KEY"
if [ $? -ne 0 ]; then
  echo "Failed to create storage queue: $QUEUE_NAME."
  exit 1
fi
echo "Storage queue $QUEUE_NAME created successfully."

echo -e "\n\n - - - - | ALL RESOURCES WERE SUCCESSFULLY PROVISIONED | - - - - \n\n"

# Get and output the storage account connection string
echo -e "\nRetrieving connection string for storage account $STORAGE_ACCOUNT_NAME..."
CONNECTION_STRING=$(az storage account show-connection-string --resource-group "$RESOURCE_GROUP_NAME" --name "$STORAGE_ACCOUNT_NAME" --query "connectionString" -o tsv)
if [ $? -ne 0 ]; then
  echo "Failed to retrieve connection string for storage account: $STORAGE_ACCOUNT_NAME."
  exit 1
fi

# It goes without saying that you should ONLY do this LOCALLY as the connection string grants you access to **EVERYTHING** in your storage account!
echo -e "\nStorage account connection string: \n\n$CONNECTION_STRING"
