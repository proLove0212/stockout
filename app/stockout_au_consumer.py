# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
from typing import Dict
import functools

import const
from logging import Logger
import logger
from mq import MQ, MQMsgData
import auapi


def _stockout(msg_data: MQMsgData, log: Logger):
    set_list = []
    item_ids = msg_data.item_ids
    for item_id in item_ids:
        set_data = auapi.AuUpdateStockData(item_code=item_id, stock_count=0)
        set_list.append(set_data)

    with auapi.AuAPI(log=log) as api:
        try:
            result = api.stock.update(update_items=set_list)
        except Exception:
            log.exception('Failed to update stock')
            raise
    log.info('Update stock data=%s', set_list)
    log.info('No update stock data=%s', result)


def _relist_on_message(msg: Dict, log: Logger) -> bool:
    log.info('Message data=%s', logger.var_dump(msg))
    try:
        msg_data = MQMsgData(**msg)
    except Exception:
        raise Exception('Receive message parse error')
    log.info('Get queue message data=%s', msg_data)

    _stockout(msg_data=msg_data, log=log)
    return True


def _consumer(log: Logger):
    try:
        with MQ(**const.MQ_CONNECT,
                queue=const.MQ_AU_QUEUE,
                routing_key=const.MQ_AU_ROUTING_KEY) as queue:
            queue.open()
            callback = functools.partial(_relist_on_message, log=log)
            queue.receive_message(callback)

    except Exception:
        log.exception('Failed to MQ connect')
        raise


def main():
    parser = argparse.ArgumentParser(description='stockout_au_consumer')
    parser.add_argument('--task_no',
                        required=True,
                        type=int,
                        help='input process No type integer')

    arg_parser = parser.parse_args()

    # ログ
    log = logger.get_logger(task_name='stockout-au-consumer',
                            sub_name='main',
                            name_datetime=datetime.now(),
                            task_no=arg_parser.task_no,
                            **const.LOG_SETTING)
    log.info('Start task')
    log.info('Input args task_no=%s', arg_parser.task_no)

    _consumer(log=log)
    log.info('End task')


if __name__ == '__main__':
    main()
