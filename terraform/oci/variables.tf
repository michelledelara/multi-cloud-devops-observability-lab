variable "region" {
  type    = string
  default = "sa-saopaulo-1"
}
variable "config_file_profile" {
  type    = string
  default = "DEFAULT"
}
variable "compartment_id" {
  description = "Existing compartment OCID; API signing keys stay outside the repository."
  type        = string
  validation {
    condition     = startswith(var.compartment_id, "ocid1.compartment.")
    error_message = "Use the OCID of an existing compartment."
  }
}
variable "project" {
  type    = string
  default = "multicloud-lab"
}
