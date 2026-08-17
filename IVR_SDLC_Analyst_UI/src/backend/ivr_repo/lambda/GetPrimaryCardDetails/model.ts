import { ConnectContactFlowResult, ConnectContactFlowEvent } from "aws-lambda"


export type EventType = ConnectContactFlowEvent
export type ReturnType = ConnectContactFlowResult | null

export interface CardInfodata {
  statusCode: string
  errorMessage: string
  cardDetails: CardDetails
}

export interface CardDetails {
  id: number
  cardDetails: CardDetail[]
  message: Message
  errorFound: boolean
}

export interface CardDetail {
  personalEmbossInformation: string
  cardActivated: boolean
  numberOfPrimaryCards: number
  lastRequestDate: string
  priorityPassNumber: string
  identifiers: Identifiers
  datePinChanged: string
  cardReceiptVerification: CardReceiptVerification
  cardRequestReason: string
  priorityPassCard: string
  tokenCounter: number
  numberOfAlternate1Cards: number
  withdrawalLimit: WithdrawalLimit
  rfidInformation: RfidInformation
  pinMailerStatus: string
  chipCard: boolean
  numberOfAlternate2Cards: number
  customerType: string
  lastPinRequestDate: string
  cardId: CardId
  numberOfCardsLastRequested: number
  cardRequestStatus: string
  expirationDate: string
}

export interface Identifiers {
  accountId: string
  customerId: string
  cardLast4: string
}

export interface CardReceiptVerification {
  date: string
  status: string
}

export interface WithdrawalLimit {
  value: string
  currency: string
}

export interface RfidInformation {
  contactlessDisabledMasterCard: boolean
  sequenceNumber: number
  currentCard: boolean
  previousCard: boolean
  cardType: string
  customerId: string
  previousCardType: string
  previousSequenceNumber: string
  cardSequenceNumber: string
  contactlessCard: boolean
}

export interface CardId {
  primaryId: string
  primaryMailerId: string
}

export interface Message {
  status: string
  detail: string
  title: string
  errorCode: string
  errors: string[]
}
// End of cardInfodata

// primary details interface

export interface PrimaryCarddata {
  message: string
  statusCode: number
  accountCardDetails: AccountCardDetails
}

export interface AccountCardDetails {
  accountInformation: AccountInformation
  accountStatus: AccountStatus
  activateStatus: ActivateStatus
  cardInfoResponse: CardInfoResponse
  customerInfo: CustomerInfo
  errorFound: boolean
}

export interface AccountInformation {
  id: number
  lastBillingDate: string
  cashLimit: CashLimit
  totalDisputes: TotalDisputes
  type: string
  statementBalance: StatementBalance
  numberCardsReissue: string
  lateCharges: LateCharges
  billingDay: string
  previousStatementDate: string
  creditLimit: CreditLimit
  outstandingDisputes: OutstandingDisputes
  product: Product
  paymentsHistory: PaymentsHistory
  identifiers: Identifiers
  currentBalance: CurrentBalance
  lastActivityInformation: LastActivityInformation
  lastPurchase: LastPurchase
  paymentDue: PaymentDue
  numberCardsOut: string
  openedDate: string
  paymentDueDate: string
  currencyInformation: CurrencyInformation
  meta: Meta
  codeInformation: CodeInformation
  purchasesSinceLastCycle: PurchasesSinceLastCycle
  multiAccount: string
  lastPayment: LastPayment
  featureToggles: FeatureToggles
  status: Status2[]
  collAgencyCode: string
  collectionAgencyAssignedDate: string
  message: Message
  errorFound: boolean
}

export interface CashLimit {
  currency: string
  value: string
}

export interface TotalDisputes {
  totalAmount: TotalAmount
  count: string
}

export interface TotalAmount {
  currency: string
  value: string
}

export interface StatementBalance {
  currency: string
  value: string
}

export interface LateCharges {
  currency: string
  value: string
}

export interface CreditLimit {
  currency: string
  value: string
}

export interface OutstandingDisputes {
  totalAmount: TotalAmount2
  count: string
}

export interface TotalAmount2 {
  currency: string
  value: string
}

export interface Product {
  productCode: string
  providerId: string
  clientProductCode: string
}

export interface PaymentsHistory {
  totalNumberOfPayments: string
  totalPaymentsAmount: TotalPaymentsAmount
}

export interface TotalPaymentsAmount {
  currency: string
  value: string
}

export interface Identifiers {
  accountId: string
  customerId: string
  cardLast4: string
}

export interface CurrentBalance {
  currency: string
  value: string
}

export interface LastActivityInformation {
  lastLatePaymentFeeDate: string
}

export interface LastPurchase {
  date: string
  amount: Amount
}

export interface Amount {
  value: string
  currency: string
}

export interface PaymentDue {
  outstandingStatementedAmount: OutstandingStatementedAmount
  outstandingAmount: OutstandingAmount
  statementedAmount: StatementedAmount
}

export interface OutstandingStatementedAmount {
  currency: string
  value: string
}

export interface OutstandingAmount {
  currency: string
  value: string
}

export interface StatementedAmount {
  currency: string
  value: string
}

export interface CurrencyInformation {
  code: string
  name: string
}

export interface Meta {
  lastMaintenanceDate: string
  interestRate: string
  totalCashAdvanceAmount: TotalCashAdvanceAmount
  accountAttributes: AccountAttribute[]
  totalPurchaseAmount: TotalPurchaseAmount
  expirationDate: string
  status: Status[]
}

export interface TotalCashAdvanceAmount {
  currency: string
  value: string
}

export interface AccountAttribute {
  attributeId: string
  description: string
  value: string
}

export interface TotalPurchaseAmount {
  currency: string
  value: string
}

export interface Status {
  description: string
  reasonCode: string
  statusCode: string
  reason: string
  code: string
}

export interface CodeInformation {
  officerCode: string
}

export interface PurchasesSinceLastCycle {
  currency: string
  value: string
}

export interface LastPayment {
  date: string
  amount: Amount2
}

export interface Amount2 {
  value: string
  currency: string
}

export interface FeatureToggles {
  alerts: string
  autoPay: string
  overdraftProtection: string
  familyCard: string
}

export interface Status2 {
  description: string
  reasonCode: string
  statusCode: string
  reason: string
  code: string
}

export interface Message {
  status: string
  detail: string
  title: string
  errorCode: string
  errors: string[]
}

export interface AccountStatus {
  id: number
  miscellaneousBillingDispute: string
  identifiers: Identifiers2
  status: Status3[]
  message: Message2
  errorFound: boolean
}

export interface Identifiers2 {
  accountId: string
  customerId: string
  cardLast4: string
}

export interface Status3 {
  description: string
  reasonCode: string
  statusCode: string
  reason: string
  code: string
}

export interface Message2 {
  status: string
  detail: string
  title: string
  errorCode: string
  errors: string[]
}

export interface ActivateStatus {
  confirmationNumber: string
  lastRequestDate: string
  referenceNumber: string
  status: string
  message: Message3
}

export interface Message3 {
  status: string
  detail: string
  title: string
  errorCode: string
  errors: string[]
}

export interface CardInfoResponse {
  id: number
  cardDetails: CardDetail[]
  message: Message4
  errorFound: boolean
}

export interface CardDetail {
  personalEmbossInformation: string
  cardActivated: boolean
  numberOfPrimaryCards: number
  lastRequestDate: string
  priorityPassNumber: string
  identifiers: Identifiers3
  datePinChanged: string
  cardReceiptVerification: CardReceiptVerification
  cardRequestReason: string
  priorityPassCard: string
  tokenCounter: number
  numberOfAlternate1Cards: number
  withdrawalLimit: WithdrawalLimit
  rfidInformation: RfidInformation
  pinMailerStatus: string
  chipCard: boolean
  numberOfAlternate2Cards: number
  customerType: string
  lastPinRequestDate: string
  cardId: CardId
  numberOfCardsLastRequested: number
  cardRequestStatus: string
  expirationDate: string
}

export interface Identifiers3 {
  accountId: string
  customerId: string
  cardLast4: string
}

export interface CardReceiptVerification {
  date: string
  status: string
}

export interface WithdrawalLimit {
  value: string
  currency: string
}

export interface RfidInformation {
  contactlessDisabledMasterCard: boolean
  sequenceNumber: number
  currentCard: boolean
  previousCard: boolean
  cardType: string
  customerId: string
  previousCardType: string
  previousSequenceNumber: string
  cardSequenceNumber: string
  contactlessCard: boolean
}

export interface CardId {
  primaryId: string
  primaryMailerId: string
}

export interface Message4 {
  status: string
  detail: string
  title: string
  errorCode: string
  errors: string[]
}

export interface CustomerInfo {
  id: number
  identifiers: Identifiers4
  customerList: CustomerList[]
  message: Message5
  errorFound: boolean
}

export interface Identifiers4 {
  accountId: string
  customerId: string
  cardLast4: string
}

export interface CustomerList {
  specialMailingIndicator: string
  phones: Phone[]
  dateOfBirth: string
  language: string
  customerDeceased: string
  transferInfo: TransferInfo
  accountId: string
  customerType: string
  emailAddress: string
  emailAddressLastMaintained: string
  ssnLast4: string
  name: Name
  bankID: string
  verificationId: string
  customerId: string
  customerRelationship: string
  cardNumber: string
  cardLast4: string
  timesAcctTransferred: string
  correspondenceAddressIds: CorrespondenceAddressIds
  contactlessDevice: string
  timeZone: string
  customerDeleted: string
}

export interface Phone {
  phoneType: string
  dateLastMaintained: string
  consentToCall: string
  type: string
  value: string
}

export interface TransferInfo {
  transferFromCardNumber: string
  transferToCardNumber: string
}

export interface Name {
  last: string
  nameOnCard: string
  first: string
}

export interface CorrespondenceAddressIds {
  generalCorrespondence: string
  statement: string
  card: string
  pinMailer: string
}

export interface Message5 {
  status: string
  detail: string
  title: string
  errorCode: string
  errors: string[]
}
