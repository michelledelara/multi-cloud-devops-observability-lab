terraform {
  required_version = ">= 1.9, < 2.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "9.1.0"
    }
  }
}
provider "oci" {
  region              = var.region
  config_file_profile = var.config_file_profile
}
