output "vcn_id" {
  value = oci_core_vcn.lab.id
}
output "subnet_id" {
  value = oci_core_subnet.app.id
}
