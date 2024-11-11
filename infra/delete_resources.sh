#!/bin/bash

echo "Starting Azure resource cleanup script..."

# Load values from infra_config.env
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

# Delete the storage queue
echo -e "\nDeleting storage queue: $QUEUE_NAME from storage account $STORAGE_ACCOUNT_NAME..."
az storage queue delete --name "$QUEUE_NAME" --account-name "$STORAGE_ACCOUNT_NAME"
if [ $? -ne 0 ]; then
  echo "Failed to delete storage queue: $QUEUE_NAME."
else
  echo "Storage queue $QUEUE_NAME deleted successfully."
fi

# Delete the storage account
echo -e "\nDeleting storage account: $STORAGE_ACCOUNT_NAME..."
az storage account delete --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP_NAME" --yes
if [ $? -ne 0 ]; then
  echo "Failed to delete storage account: $STORAGE_ACCOUNT_NAME."
else
  echo "Storage account $STORAGE_ACCOUNT_NAME deleted successfully."
fi

# Delete the resource group
echo -e "\nDeleting resource group: $RESOURCE_GROUP_NAME..."
az group delete --name "$RESOURCE_GROUP_NAME" --yes --no-wait
if [ $? -ne 0 ]; then
  echo "Failed to delete resource group: $RESOURCE_GROUP_NAME."
else
  echo "Resource group $RESOURCE_GROUP_NAME deletion initiated successfully."
fi

echo -e "\n\n - - - - | ALL RESOURCES WERE SUCCESSFULLY DELETED | - - - - \n\n"