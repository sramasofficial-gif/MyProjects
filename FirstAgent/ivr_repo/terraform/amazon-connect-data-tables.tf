### Flatten each table's attributes into a single collection we can for_each over
locals {
  flattened_attrs = flatten([
    for table_key, table_cfg in var.data_tables : [
      for a in table_cfg.attributes : {
        table_key   = table_key
        name        = a.name
        value_type  = a.value_type
        primary     = try(a.primary, false)
        description = try(a.description, null)
      }
    ]
  ])
}

resource "awscc_connect_data_table" "this" {
  for_each = var.data_tables

  instance_arn     = var.connect_instance_arn                   
  name             = each.value.name
  description      = try(each.value.description, null)
  status           = "PUBLISHED"                         
  time_zone        = try(each.value.time_zone, "UTC")   
  value_lock_level = try(each.value.value_lock_level, "NONE")

  tags = [
    for k, v in var.tags : {
      key   = k
      value = v
    }
  ]

}



resource "awscc_connect_data_table_attribute" "this" {
  for_each = {
    for a in local.flattened_attrs :
    "${a.table_key}.${a.name}" => a
  }

  instance_arn   = var.connect_instance_arn
  data_table_arn = awscc_connect_data_table.this[each.value.table_key].arn  # dependency on the table

  name        = each.value.name
  value_type  = each.value.value_type        # TEXT|NUMBER|BOOLEAN|TEXT_LIST|NUMBER_LIST
  primary     = each.value.primary
  description = each.value.description
}
