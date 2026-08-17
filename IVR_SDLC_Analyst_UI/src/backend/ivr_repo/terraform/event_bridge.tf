/*
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "invoke-roger-lambda-every-day"
  description         = "Triggers the ExportCnxReportFromS3 Lambda every day"
  schedule_expression = "cron(30 23 * * ? *)"
}
 
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "rogers-lambda"
  arn       = "arn:aws:lambda:ca-central-1:489551464761:function:rogers-rbconnect-dev-ExportCnxReportFromS3-function"
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = "rogers-rbconnect-dev-ExportCnxReportFromS3-function"
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}



module "invoke_export_lambda_schedule" {
  source = "./modules/eventbridge" # Adjust to match actual module path

  create                 = true
  create_event_rules     = true
  create_event_targets   = true
  create_scheduler_group = false
  create_schedules       = false
  create_event_bus       = false
  create_connection      = false
  create_api_destination = false
  create_archives        = false

  # Only needed if using a custom event bus, which you're not
  event_bus_name = "default"

  # Event Rule Definition
 rules = {
    invoke_roger_lambda_every_day = {
      name                = "invoke-roger-lambda-every-day"
      name_prefix         = null
      description         = "Triggers the ExportCnxReportFromS3 Lambda every day"
      schedule_expression = "cron(30 23 * * ? *)"
      event_pattern       = null
      role_arn            = null
      state               = "ENABLED"
    }
  }

  # Event Target Definition
  targets = {
    rogers_lambda = {
      name        = "rogers-lambda"
      rule_name   = "invoke-roger-lambda-every-day"
      arn         = "arn:aws:lambda:ca-central-1:489551464761:function:rogers-rbconnect-dev-ExportCnxReportFromS3-function"
      target_id   = "rogers-lambda"
      role_arn    = null
      input       = null
      input_path  = null
    }
  }

  lambda_permissions = [
    {
      function_name = "rogers-rbconnect-dev-ExportCnxReportFromS3-function"
      source_arn    = "arn:aws:events:ca-central-1:${data.aws_caller_identity.current.account_id}:rule/invoke-roger-lambda-every-day"
      statement_id  = "AllowExecutionFromEventBridge"
    }
  ]

  # Optional metadata
  project-id         = var.project-id
  application-owner  = var.application-owner
  application-role   = var.application-role
  application-name   = var.application-name
  PII                = var.PII
  compliance         = var.compliance
  SCOA               = var.SCOA
  TFE                = var.TFE
  businessunit       = var.businessunit
}

*/

#########################################################################################################
###########              eventbridge module call                                      ##################
#########################################################################################################

module "rbconnect_eventbridge" {
  source = "./modules/tfe.rogers.com/aws/eventbridge"  

  # Event Bus
  #create_event_bus = var.create_event_bus
  #event_bus_name   = var.event_bus_name

  # Rules
  create_event_rules = var.create_event_rules
  rules              = var.rules

  # Targets
  create_event_targets = var.create_event_targets
  targets              = var.targets
  
  # Pipes
  create_pipes         = var.create_pipes
  pipes                = var.pipes
  

  # Required Tags (you already use local.common_tags inside the module)
  TFE                 = var.tags.TFE
  environment         = var.tags.environment
  application-id      = var.tags.application-id
  application-owner   = var.tags.application-owner
  application-role    = var.tags.application-role
  SCOA                = var.tags.SCOA
  project-id          = var.tags.project-id
  PII                 = var.tags.PII
  compliance          = var.tags.compliance
  businessunit        = var.tags.businessunit
  application-name    = var.tags.application-name
  data-classification = var.tags.data-classification
  costcenter          = var.tags.costcenter
}

#####################################################################################################
##                       Event Pipe                                                               ##
#####################################################################################################
/*
module "eventpipe_ae_cnx" {
  source = "./modules/tfe.rogers.com/aws/eventpipe"

  name               = "rb-pci-dev-eventpipe-rbconnect-ae-cnx"
  role_arn           = "arn:aws:iam::207567788052:role/pci-ccr-eventbridgepipe-Role"
  kinesis_stream_arn = "arn:aws:kinesis:ca-central-1:207567788052:stream/rb-pci-dev-kds-rbconnect-agentevents"
  event_bus_arn      = "arn:aws:events:ca-central-1:207567788052:event-bus/default"

  batch_size                 = 5
  kinesis_starting_position = "LATEST"
  enable_filter              = true

  filter_pattern = jsonencode({
    data = {
      CurrentAgentSnapshot = {
        Configuration = {
          Username = [{
            suffix = "@rci.rogers.com"
          }]
        }
      }
    }
  })

  input_template = <<EOT
{
  "data": <$.data>
}
EOT

  detail_type  = ""
  event_source = "rb-pci-dev-eventpipe-rbconnect-ae-cnx"
}


module "eventpipe_ctr_voicemail" {
  source = "./modules/tfe.rogers.com/aws/eventpipe"

  name               = "rb-pci-dev-eventpipe-rbconnect-ctr-voicemail"
  role_arn           = "arn:aws:iam::207567788052:role/pci-ccr-eventbridgepipe-Role"
  kinesis_stream_arn = "arn:aws:kinesis:ca-central-1:207567788052:stream/rb-pci-dev-kds-rbconnect-ctr"
  event_bus_arn      = "arn:aws:events:ca-central-1:207567788052:event-bus/default"

  batch_size                 = 5
  kinesis_starting_position = "LATEST"
  enable_filter              = true

  filter_pattern = jsonencode({
    data = {
      Attributes = {
        voicemail = ["true"]
      },
      Channel = ["VOICE"]
    }
  })

  input_template = <<EOT
{
  "data": <$.data>
}
EOT

  detail_type  = ""
  event_source = "rb-pci-dev-eventpipe-rbconnect-ctr-voicemail"
}


module "eventpipe_ctr_calls" {
  source = "./modules/tfe.rogers.com/aws/eventpipe"

  name               = "rb-pci-dev-eventpipe-rbconnect-ctr-calls"
  role_arn           = "arn:aws:iam::207567788052:role/pci-ccr-eventbridgepipe-Role"
  kinesis_stream_arn = "arn:aws:kinesis:ca-central-1:207567788052:stream/rb-pci-dev-kds-rbconnect-ctr"
  event_bus_arn      = "arn:aws:events:ca-central-1:207567788052:event-bus/default"

  batch_size                 = 5
  kinesis_starting_position = "LATEST"
  enable_filter              = true

 filter_pattern = jsonencode({
  data = {
    Attributes = {
      voicemail = [null]
    },
    Channel = ["VOICE"]
  }
})

  input_template = <<EOT
{
  "data": <$.data>
}
EOT

  detail_type  = ""
  event_source = "rb-pci-dev-eventpipe-rbconnect-ctr-calls"
}


module "eventpipe_ctr_calls_new" {
  source = "./modules/tfe.rogers.com/aws/eventpipe"

  name               = "rb-pci-dev-eventpipe-rbconnect-ae-rogers"
  role_arn           = "arn:aws:iam::207567788052:role/pci-ccr-eventbridgepipe-Role"
  kinesis_stream_arn = "arn:aws:kinesis:ca-central-1:207567788052:stream/rb-pci-dev-kds-rbconnect-ctr"
  event_bus_arn      = "arn:aws:events:ca-central-1:207567788052:event-bus/default"

  batch_size                 = 5
  kinesis_starting_position = "LATEST"
  enable_filter              = true

 filter_pattern = jsonencode({
  data = {
    Attributes = {
      voicemail = [null]
    },
    Channel = ["VOICE"]
  }
})

  input_template = <<EOT
{
  "data": <$.data>
}
EOT

  detail_type  = ""
  event_source = "rb-pci-dev-eventpipe-rbconnect-ctr-calls"
}
*/

