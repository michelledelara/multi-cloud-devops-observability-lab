locals {
  tags = {
    Project     = var.project
    Environment = "lab"
    ManagedBy   = "Terraform"
  }
}
resource "oci_core_vcn" "lab" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.30.0.0/16"]
  display_name   = "vcn-${var.project}"
  dns_label      = "multilab"
  freeform_tags  = local.tags
}
resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.lab.id
  display_name   = "rt-private"
  freeform_tags  = local.tags
}
resource "oci_core_security_list" "app" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.lab.id
  display_name   = "sl-app"
  freeform_tags  = local.tags
  ingress_security_rules {
    protocol = "6"
    source   = "10.30.0.0/16"
    tcp_options {
      min = 8080
      max = 8080
    }
  }
  egress_security_rules {
    protocol    = "all"
    destination = "10.30.0.0/16"
  }
}
resource "oci_core_subnet" "app" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.lab.id
  cidr_block                 = "10.30.1.0/24"
  display_name               = "subnet-app"
  dns_label                  = "app"
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.app.id]
  freeform_tags              = local.tags
}
