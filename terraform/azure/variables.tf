variable "subscription_id" {
  description = "Azure subscription ID. Authenticate separately with az login or OIDC."
  type        = string
}
variable "location" {
  type    = string
  default = "brazilsouth"
}
variable "project" {
  type    = string
  default = "multicloud-lab"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,24}$", var.project))
    error_message = "Use 3-25 lowercase letters, numbers or hyphens, starting with a letter."
  }
}
variable "environment" {
  type    = string
  default = "lab"
}
