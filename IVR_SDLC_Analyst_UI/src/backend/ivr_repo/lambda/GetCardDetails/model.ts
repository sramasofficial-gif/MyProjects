import { ConnectContactFlowResult, ConnectContactFlowEvent } from "aws-lambda";

export interface FinalResponse {
  statusCode: string,
  cardActive: string,
  reissuedReason: string,
  customerType: string,
  lastIssueDate: string,
  openDate: string,
  message: string
}

export type ReturnType = ConnectContactFlowResult | null;
export type EventType = ConnectContactFlowEvent;

export interface Carddetail {
  statusCode: string | null;
  errorMessage: string,
  cardDetails: {
    id: 0,
    cardDetails: [
      {
        personalEmbossInformation: string,
        cardActivated: boolean,
        numberOfPrimaryCards: 0,
        lastRequestDate: string,
        priorityPassNumber: string,
        identifiers: {
          accountId: string,
          customerId: string,
          cardLast4: string
        },
        datePinChanged: string,
        cardReceiptVerification: {
          date: string,
          status: string
        },
        cardRequestReason: string,
        priorityPassCard: string,
        tokenCounter: 0,
        numberOfAlternate1Cards: 0,
        withdrawalLimit: {
          value: string,
          currency: string
        },
        rfidInformation: {
          contactlessDisabledMasterCard: boolean,
          sequenceNumber: 0,
          currentCard: boolean,
          previousCard: boolean,
          cardType: string,
          customerId: string,
          previousCardType: string,
          previousSequenceNumber: string,
          cardSequenceNumber: string,
          contactlessCard: true
        },
        pinMailerStatus: string,
        chipCard: true,
        numberOfAlternate2Cards: 0,
        customerType: string,
        lastPinRequestDate: string,
        cardId: {
          primaryId: string,
          primaryMailerId: string
        },
        numberOfCardsLastRequested: 0,
        cardRequestStatus: string,
        expirationDate: string
      }
    ],
    message: {
      status: string,
      detail: string,
      title: string,
      errorCode: string,
      errors: [
        string
      ]
    },
    errorFound: true
  }
}