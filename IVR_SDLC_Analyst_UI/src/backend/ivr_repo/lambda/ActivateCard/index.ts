import {
    RequestError,
    handleError
} from '@ccrlayer/common';

import { EventType } from "./model"

import { activateCard } from "./activate-card"

export async function handler(event: EventType) {
    let response: any
    try {
        const { accountId, customerId, action } = event.Details.Parameters
        if (!action || !accountId || !customerId) {
            throw new RequestError('accountId and customerId are required!', 406)
        }
        response = await activateCard(accountId, customerId)

    } catch (err: any) {        
        response = handleError(err)
    }
    return response;
}
