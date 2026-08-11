/*
#Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service Terms and the SOW between the parties dated 2024.
*/

resource "aws_connect_hours_of_operation" "hours_of_operation" {
  for_each = local.decode_operating_hours

  instance_id = aws_connect_instance.saml_instance.id
  name        = each.value.Name
  description = each.value.Description
  time_zone   = each.value.TimeZone

  dynamic "config" {
    for_each = each.value.Config

    content {
      day = config.value.Day
      start_time {
        hours   = config.value.StartTime.Hours
        minutes = config.value.StartTime.Minutes
      }
      end_time {
        hours   = config.value.EndTime.Hours
        minutes = config.value.EndTime.Minutes
      }
    }
  }
}


#Load the connect_resource.json data
data "local_file" "connect_resources" {
  filename = "${path.module}/bin/connect_resources.json"
}

locals {
  connect_resources = jsondecode(data.local_file.connect_resources.content)
}

resource "aws_connect_routing_profile" "routing_profiles" {
  for_each = local.decode_routing_profiles

  instance_id               = aws_connect_instance.saml_instance.id
  name                      = each.value.name
  description               = each.value.description
  default_outbound_queue_id = lookup(local.connect_resources["queues"], each.value.outboundQueue, null)["id"]
  tags                      = each.value.tags

  dynamic "media_concurrencies" {
    for_each = each.value.media
    content {
      channel     = media_concurrencies.value.Channel
      concurrency = media_concurrencies.value.Concurrency
    }
  }

  dynamic "queue_configs" {
    for_each = each.value.queues
    content {
      queue_id = lookup(local.connect_resources["queues"], queue_configs.value.QueueName, null)["id"]
      channel  = queue_configs.value.Channel
      priority = queue_configs.value.Priority
      delay    = queue_configs.value.Delay
    }
  }

  #dynamic "manual_assignment_queue_configs" {
  #for_each = lookup(each.value, "QueueConfigsForManualAssignment", [])
 
 # content {
  #  queue_id = lookup(local.connect_resources["queues"], manual_assignment_queue_configs.value.QueueName, null)["id"]
   # channel = manual_assignment_queue_configs.value.Channel
    #}
  #}
}



resource "awscc_connect_routing_profile" "this" {
  for_each = local.awscc_routing_profiles

  name                       = each.value.name
  description                = each.value.description
  instance_arn               = var.connect_instance_arn
  default_outbound_queue_arn = each.value.default_outbound_queue_arn

  media_concurrencies = each.value.media_concurrencies

  queue_configs = each.value.queue_configs

  # AWSCC-Specific manual assignment configs
  manual_assignment_queue_configs = each.value.manual_assignment_queue_configs

  tags = each.value.tags
}




resource "aws_connect_queue" "queues" {
  depends_on = [resource.aws_connect_hours_of_operation.hours_of_operation]
  for_each   = local.decode_queues

  instance_id = aws_connect_instance.saml_instance.id
  name        = each.value.Name
  description = each.value.Description
  #hours_of_operation_id     = local.default_hours_of_operation_id
  hours_of_operation_id = try(resource.aws_connect_hours_of_operation.hours_of_operation[each.value.HoursOfOperationId].hours_of_operation_id, split(":", data.aws_connect_hours_of_operation.basic_hours.id)[1])
  status                = each.value.Status
  tags                  = each.value.Tags

  dynamic "outbound_caller_config" {
    for_each = [each.value.OutboundCallerConfig]

    content {
      #outbound_caller_id_name       = outbound_caller_config.value.OutboundCallerIdName
      outbound_caller_id_name       = try(outbound_caller_config.value.OutboundCallerIdName, null)
      outbound_caller_id_number_id = try(lookup(local.outbound_caller_id_number_map, outbound_caller_config.value.OutboundCallerIdNumberId, null), null)
      #outbound_flow_id              = outbound_caller_config.value.OutboundFlowId
      #outbound_flow_id              = split(":", lookup(data.aws_connect_contact_flow.retrieve_cf_id, outbound_caller_config.value.OutboundFlowId, null).id)[1]
      #outbound_caller_id_number_id   = lookup(local.outbound_caller_id_number_map, outbound_caller_config.value.OutboundCallerIdNumberId, null)
      #outbound_flow_id              = try(resource.aws_connect_contact_flow.contact_flows[outbound_caller_config.value.OutboundFlowId], split(":", data.aws_connect_contact_flow.basic_outbound.id)[1])
      outbound_flow_id = try(split(":", lookup(local.outbound_flow_map, replace(lower(outbound_caller_config.value.OutboundFlowId), " ", "_"), ""))[1], null)
    }
  }

  //quick_connect_ids = each.value.QuickConnects
  quick_connect_ids = [
    for name in each.value.QuickConnects : lookup(local.connect_resources["quick_connect"], name, null)["id"]
    if lookup(local.connect_resources["quick_connect"], name, null) != null
  ]
}

/*
resource "awscc_connect_queue" "email_enabled" {
  for_each = local.awscc_queues

  instance_arn = var.connect_instance_arn
  name         = each.value.name
  description  = each.value.description
  status       = each.value.status

  hours_of_operation_arn = each.value.hours_of_operation_arn

  outbound_caller_config = {
    outbound_caller_id_name       = each.value.outbound_caller_id_name
    outbound_caller_id_number_arn = each.value.outbound_caller_id_number_arn
    outbound_flow_arn             = each.value.outbound_flow_arn
  }

  outbound_email_config = {
    email_address              = each.value.email_address
    outbound_flow_arn         = each.value.email_outbound_flow_arn
    additional_email_addresses = each.value.additional_email_addresses
  }

  #quick_connect_arns = each.value.quick_connect_arns

  tags = each.value.tags
}
*/

resource "aws_connect_quick_connect" "quick_connects" {
  depends_on = [aws_connect_instance.saml_instance]
  for_each   = local.decode_quick_connect

  instance_id = aws_connect_instance.saml_instance.id
  name        = each.value.name
  description = each.value.description

   tags = try(each.value.tags, {})

  dynamic "quick_connect_config" {
    for_each = [each.value] # This will iterate once, allowing us to access the `quick_connect_type`.

    content {
      quick_connect_type = quick_connect_config.value.type

      dynamic "phone_config" {
        for_each = quick_connect_config.value.type == "PHONE_NUMBER" ? [1] : []
        content {
          phone_number = quick_connect_config.value.number
        }
      }

      dynamic "queue_config" {
        for_each = quick_connect_config.value.type == "QUEUE" ? [1] : []
        content {
          queue_id = aws_connect_queue.queues["${quick_connect_config.value.queue}.json"].queue_id //ApplicationStatus_EN
          //queue_id = data.aws_connect_queue.BasicQueue.queue_id
          //queue_id = quick_connect_config.value.queue_id
          //contact_flow_id = quick_connect_config.value.flow
          contact_flow_id = lookup(local.qc_flows_map, quick_connect_config.value.flow, "")
        }
      }

      dynamic "user_config" {
        for_each = quick_connect_config.value.type == "USER" ? [1] : []
        content {
          user_id         = quick_connect_config.value.user
          contact_flow_id = quick_connect_config.value.flow
        }
      }
    }
  }
}



data "aws_connect_user_hierarchy_group" "user_hierarchy" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "RogersBank"
} 

output "user_hierarchy" {
  value = data.aws_connect_user_hierarchy_group.user_hierarchy.hierarchy_group_id
} 


data "aws_connect_user_hierarchy_group" "canada" {
  instance_id = aws_connect_instance.saml_instance.id
  name        = "Canada"
}


output "canada_hierarchy_group_id" {
  value = data.aws_connect_user_hierarchy_group.canada.hierarchy_group_id
}


data "aws_connect_user_hierarchy_group" "vendor1" {
  instance_id = aws_connect_instance.saml_instance.id
  hierarchy_group_id = "1bf1466b-ab89-4b97-90d5-d2cb3ab43c9a"
  #name        = "vendor1"
}


output "vendor1_hierarchy_group_id" {
  value = data.aws_connect_user_hierarchy_group.vendor1.hierarchy_group_id
}


# Leaf group: teamA (under RogersBank → Canada → vendor1)
data "aws_connect_user_hierarchy_group" "teamA" {
  instance_id = aws_connect_instance.saml_instance.id
  hierarchy_group_id = "68580f0a-b369-49b1-86c7-a083826d04d6"
  #name             = "teamA"
}

output "teamA_hierarchy_group_id" {
  value = data.aws_connect_user_hierarchy_group.teamA.hierarchy_group_id
}

# Leaf group: teamB (under RogersBank → Canada → vendor1)
data "aws_connect_user_hierarchy_group" "teamB" {
  instance_id = aws_connect_instance.saml_instance.id
  hierarchy_group_id = "12e1df33-a05a-4ae1-ba0f-2221ad7e7221"
  #name             = "teamB"
}

output "teamB_hierarchy_group_id" {
  value = data.aws_connect_user_hierarchy_group.teamB.hierarchy_group_id
}

data "aws_connect_user_hierarchy_group" "vendor2" {
  instance_id = aws_connect_instance.saml_instance.id
  hierarchy_group_id = "cab18eef-d11a-44b0-98c3-40f59e1783d7"
  #name        = "vendor2"
}

output "vendor2_hierarchy_group_id" {
  value = data.aws_connect_user_hierarchy_group.vendor2.hierarchy_group_id
}

data "aws_connect_user_hierarchy_group" "vendor2_teamA" {
  instance_id = aws_connect_instance.saml_instance.id
  hierarchy_group_id = "1794c87d-ad7a-42f3-bead-19aa38ce38e8"
  #name        = "teamA"
}

output "vendor2_teamA_hierarchy_group_id" {
  value = data.aws_connect_user_hierarchy_group.vendor2_teamA.hierarchy_group_id
}

data "aws_connect_user_hierarchy_group" "vendor2_teamB" {
  instance_id        = aws_connect_instance.saml_instance.id
  hierarchy_group_id = "40130809-fa8b-4324-981a-0b6a1642c1bb"
}

output "vendor2_teamB_hierarchy_group_id" {
  value = data.aws_connect_user_hierarchy_group.vendor2_teamB.hierarchy_group_id
}


# # Resource when allowed_access_control_hierarchy_group_id is present
 resource "awscc_connect_security_profile" "security_profiles_with_hierarchy" {
   #for_each = {
   #  for k, v in local.security_profiles : k => v
   #  if try(v.allowed_access_control_hierarchy_group_id, "") != ""
   #}
    for_each = local.security_profiles_with_hierarchy

   instance_arn                             = aws_connect_instance.saml_instance.arn
   security_profile_name                    = "${each.key}"
   description                              = try(each.value.description, null) #"Deployed for rbconnect"
   allowed_access_control_hierarchy_group_id = each.value.allowed_access_control_hierarchy_group_id
   hierarchy_restricted_resources           = try(each.value.hierarchy_restricted_resources, null)
   allowed_access_control_tags              = try(each.value.allowed_access_control_tags, null)
   tag_restricted_resources                 = try(each.value.tag_restricted_resources, null)
   tags                                     = try(each.value.tags, null)
   permissions                              = try(each.value.permissions, null)
   provider                                 = awscc
  # Lifecycle guard-rails
  lifecycle {
    prevent_destroy = true

    # Ignore out-of-band permission edits to reduce plan noise/drift
    #ignore_changes = [
    #  permissions
    #]
  }
 }

# # Resource when allowed_access_control_hierarchy_group_id is not present
 resource "awscc_connect_security_profile" "security_profiles_without_hierarchy" {
   #for_each = {
   #  for k, v in local.security_profiles : k => v
   #  if try(v.allowed_access_control_hierarchy_group_id, "") == ""
   #}
  for_each = local.security_profiles_without_hierarchy

   instance_arn                             = aws_connect_instance.saml_instance.arn
   security_profile_name                    = "${each.key}"
   description                              = try(each.value.description, null)
   hierarchy_restricted_resources           = try(each.value.hierarchy_restricted_resources, null)
   allowed_access_control_tags              = try(each.value.allowed_access_control_tags, null)
   tag_restricted_resources                 = try(each.value.tag_restricted_resources, null)
   tags                                     = try(each.value.tags, null)
   permissions                              = try(each.value.permissions, null)
   provider                                 = awscc
   # Lifecycle guard-rails
  lifecycle {
    prevent_destroy = true

    # Ignore out-of-band permission edits to reduce plan noise/drift
    #ignore_changes = [
    #  permissions
    #]
  }
 }

/*
resource "awscc_connect_routing_profile" "awscc_provider_routing_profiles" {
  for_each = local.decode_routing_profiles

  instance_id               = aws_connect_instance.saml_instance.id
  name                      = each.value.name
  description               = each.value.description
  default_outbound_queue_id = lookup(local.connect_resources["queues"], each.value.outboundQueue, null)["id"]
  tags                      = each.value.tags

  # ----------------------------
  # Media Concurrencies (as-is)
  # ----------------------------
  dynamic "media_concurrencies" {
    for_each = each.value.media
    content {
      channel     = media_concurrencies.value.Channel
      concurrency = media_concurrencies.value.Concurrency
      # If you also carry CrossChannelBehavior in your JSON, you can add:
      # cross_channel_behavior = {
      #   behavior_type = media_concurrencies.value.CrossChannelBehavior.BehaviorType
      # }
    }
  }

  # ---------------------------------------
  # Auto-assignment Queue Configs (as-is)
  # ---------------------------------------
  dynamic "queue_configs" {
    for_each = each.value.queues
    content {
      queue_id = lookup(local.connect_resources["queues"], queue_configs.value.QueueName, null)["id"]
      channel  = queue_configs.value.Channel
      priority = queue_configs.value.Priority
      delay    = queue_configs.value.Delay
    }
  }

  # --------------------------------------------------------------------
  #  Manual-assignment Queue Configs (AWSCC-only, Worklist support)
  #    Expects an array in  input JSON at:
  #    "RoutingProfileManualAssignmentQueueConfig": [
  #      { "QueueName": "BackOffice_Task", "Channel": "TASK" }
  #    ]
  # --------------------------------------------------------------------
  routing_profile_manual_assignment_queue_configs = [
    for mac in lookup(each.value, "RoutingProfileManualAssignmentQueueConfig", []) : {
      QueueReference = {
        QueueId = lookup(local.connect_resources["queues"], mac.QueueName, null)["id"]
        Channel = mac.Channel  # Valid: TASK | CHAT | EMAIL (VOICE not supported)
      }
    }
  ]
}
*/
