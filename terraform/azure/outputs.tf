output "resource_group_name" {
  value = azurerm_resource_group.lab.name
}
output "vnet_id" {
  value = azurerm_virtual_network.lab.id
}
output "subnet_id" {
  value = azurerm_subnet.app.id
}
