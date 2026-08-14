/*resource "aws_sns_topic" "cloudwatch_alarm_alerts" {
  name = "rogers-rbconnect-pci-CloudWatchAlarmAlerts"

  tags = {
    applicationname = "RB-PCI-RBCONNECT"
  }
}

resource "aws_sns_topic_subscription" "email_subscription_1" {
  topic_arn = aws_sns_topic.cloudwatch_alarm_alerts.arn
  protocol  = "email"
  endpoint  = "Chinmai.Kodam@rci.rogers.com"
}

resource "aws_sns_topic_subscription" "email_subscription_2" {
  topic_arn = aws_sns_topic.cloudwatch_alarm_alerts.arn
  protocol  = "email"
  endpoint  = "lokesh.kothapally@rci.rogers.com"
}
*/


module "sns_topic_cloudwatch_alerts" {
  source                   = "./modules/tfe.rogers.com/aws/sns"  # Adjust the path as needed
  sns-topic-name           = "rogers-rbconnect-pci-CloudWatchAlarmAlerts"
  sns-topic-name-prefix    = ""
  sns-topic-display-name   = "CloudWatch Alarm Alerts"
  kms-master-key-id        = null
  sns-policy-file          = null
  tracing-config           = null

  # Add any required tags here or pass them via locals
  environment           = var.tags.environment
  project-id            = var.tags.project-id
  application-owner     = var.tags.application-owner
  #data-classification   = var.data_classification
  #application-id        = var.application-id
  application-role      = var.tags.application-role
  application-name      = var.tags.application-name
  applicationname       = var.tags.applicationname
  PII                   = var.tags.PII
  compliance            = var.tags.compliance
  SCOA                  = var.tags.SCOA
  TFE                   = "YES"
  businessunit          = var.tags.businessunit
  costcenter            = var.tags.costcenter
}


module "sns_subscription_chinmai" {
  source                      = "./modules/tfe.rogers.com/aws/sns-subscription"  # Adjust the path
  sns-topic-arn               = module.sns_topic_cloudwatch_alerts.sns-topic-arn
  sns-subscription-protocol   = "email"
  sns-subscription-endpoint   = "Chinmai.Kodam@rci.rogers.com"
}

module "sns_subscription_lokesh" {
  source                      = "./modules/tfe.rogers.com/aws/sns-subscription"
  sns-topic-arn               = module.sns_topic_cloudwatch_alerts.sns-topic-arn
  sns-subscription-protocol   = "email"
  sns-subscription-endpoint   = "lokesh.kothapally@rci.rogers.com"
}

