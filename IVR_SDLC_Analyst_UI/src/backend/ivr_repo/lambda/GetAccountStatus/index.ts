import {
    RequestError,
    xpGet,
    handleError
} from "@ccrlayer/common"

import {
    EventType,
    FinalResponse,
    ApiResponse
} from "./model"

import { HttpStatusCode } from "axios"

import { 
    STATUSCHECKLIST, 
    SF_CODE, 
    REASONS, 
    CODES 
} from "./constants"

const {
    ENDPOINT,
    CHANNEL,
    X_PLAT_APIGATEWAY_URL
} = process.env

export const handler = async (event: EventType): Promise<FinalResponse> => {
    let response: FinalResponse = { statusCode: HttpStatusCode.InternalServerError }
    try {
        if (!ENDPOINT || !CHANNEL || !X_PLAT_APIGATEWAY_URL) {
            throw new RequestError("Invalid env setup", HttpStatusCode.NotAcceptable)
        }
        const accountId: string = event.Details.Parameters.accountId
        if (!accountId) {
            throw new RequestError("Invalid env input", HttpStatusCode.NotAcceptable)
        }
        const endpoint: string = X_PLAT_APIGATEWAY_URL + ENDPOINT.replace("{accountId}", accountId)
        const apiRes = await xpGet(endpoint)
        if (apiRes.status != HttpStatusCode.Ok) {
            throw new RequestError(apiRes.data.message, apiRes.status)
        }
        const data: ApiResponse = apiRes.data
        const accountInformation: any = data?.accountInformation
        const statusList: any = accountInformation.meta.status       

        const isCodePresent = statusList.some((item: { code: string, reason: string }) =>
            (item.reason === REASONS.TWENTY_ONE && item.code === CODES.CW) ||
            (item.reason === REASONS.TWENTY_ONE && item.code === CODES.TW) ||
            (item.reason === REASONS.OTHER && item.code === CODES.WA) ||
            (STATUSCHECKLIST.includes(item.code))            
        );

        const sfCodeFlag: boolean = statusList.some((item: { code: string }) =>
            (item.code === SF_CODE)
        );

        response = {
            creditAllowed: !isCodePresent,
            accountStatus: sfCodeFlag ? SF_CODE : '',
            codeFlag: sfCodeFlag,
            agencyCode: accountInformation.collAgencyCode ?? '',
            statusCode: apiRes.status,
            clientProductCode: accountInformation.product.clientProductCode ?? '',
            openedDate: accountInformation.openedDate
        }
    } catch (err) {
        console.error(err)
        const errRes = handleError(err)
        response.statusCode = errRes.statusCode
        response.message = errRes.message
    }
    return response
}
