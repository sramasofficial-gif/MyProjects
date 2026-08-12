module "ses_domain" {
  source = "./modules/tfe.rogers.com/aws/ses"   # update path to your module

  enabled            = true
  enable_domain      = true
  enable_verification = false
  enable_mail_from   = false
  enable_spf_domain  = false
  enable_mx          = false
  enable_policy      = true
  enable_template    = false   # optional
  enable_filter      = false   # optional

  domain             = "rci.rogers.com"
  mail_from_domain   = "mail.rci.rogers.com"

  #zone_id            = "Z123456789ABCDEFG"   # your Route53 hosted zone ID

  txt_type           = "TXT"
  cname_type         = "CNAME"
  mx_type            = "MX"

  iam_policy_identifiers = "arn:aws:iam::207567788052:role/service-role/AmazonConnectEmailSESAccessRole"

  template_subject   = "Welcome!"
  template_html      = "<h1>Hello</h1>"
  text               = "Hello"

  filter_cidr        = "0.0.0.0/0"
  filter_policy      = "Allow"

  # VPC endpoint (optional)
  vpc_id             = null
  subnet_ids         = []
  security_group_ids = []
  vpc_endpoint_id    = null

  environment       = var.tags.environment
  project-id        = var.tags.project-id
  application-owner = var.tags.application-owner
  application-role  = var.tags.application-role
  application-name  = var.tags.application-name
  applicationname   = var.tags.applicationname
  PII               = var.tags.PII
  compliance        = var.tags.compliance
  SCOA              = var.tags.SCOA
  businessunit      = var.tags.businessunit
  costcenter        = var.tags.costcenter
  TFE               = "YES"
}
