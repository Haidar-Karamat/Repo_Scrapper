variable "resource_group_name" {
  type        = string
  default     = "repo-scrapper-rg"
  description = "Name of the Azure Resource Group"
}

variable "location" {
  type        = string
  default     = "East US"
  description = "Azure Region for deployment"
}

variable "acr_name" {
  type        = string
  default     = "reposcrapperacr"
  description = "Globally unique name for Azure Container Registry (lowercase alphanumeric only)"
}

variable "aks_cluster_name" {
  type        = string
  default     = "repo-scrapper-aks"
  description = "Name of the AKS Cluster"
}