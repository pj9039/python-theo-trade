import sys
import time
import datetime
import copy
import PyQt5.QtWidgets
import PyQt5.QAxContainer
import PyQt5.QtCore
from theo.framework import DictList, Log


class Kiwoom(PyQt5.QAxContainer.QAxWidget):
    '''
    It is the interface what control the Kiwoom API.

    Methods:
        configure(tran_request_limitation_evasion_type=None)

    Example:
    '''

    is_started = False
    tran_request_limitation_evasion_type = 1

    @staticmethod
    def configure(tran_request_limitation_evasion_type=None):
        if not Kiwoom.is_started:
            if tran_request_limitation_evasion_type is not None:
                if not isinstance(tran_request_limitation_evasion_type, int):
                    raise AssertionError('[theo.trade.Kiwoom] error: tran_request_limitation_evasion_type(type:{}) should be int.'.format(type(tran_request_limitation_evasion_type)))

                Kiwoom.tran_request_limitation_evasion_type = tran_request_limitation_evasion_type
        else:
            raise AssertionError('[theo.trade.Kiwoom] error: config should be configured before using.')
            # print('[theo.trade.Kiwoom] warning: config should be configured before using.')

    def print_config(self):
        self.log.print('info', '[theo.trade.Kiwoom] print configuration')
        self.log.print('info', '- Tran request limitation evasion type : {}'.format(
            'limitation list' if Kiwoom.tran_request_limitation_evasion_type == 1 else 'minimum seconds'))

    def __init__(self):
        if Kiwoom.is_started:
            raise AssertionError('[theo.trade.Kiwoom] error: Kiwoom should be used from only a point.')

        self.log = Log('Kiwoom')
        Kiwoom.is_started = True
        self.print_config()

        self.system_application = PyQt5.QtWidgets.QApplication(sys.argv)
        super().__init__()
        self.setControl('KHOPENAPI.KHOpenAPICtrl.1')

        self.tran_dictlist = DictList('request')
        self.market_dictlist = DictList('market')
        self.error_dictlist = DictList('code')
        self.set_tran()
        self.set_market()
        self.set_error()

        if Kiwoom.tran_request_limitation_evasion_type == 1:
            self.tran_request_limitations = [
                {'requested_times': list(), 'limit_second': 1, 'limit_count': 5},
                {'requested_times': list(), 'limit_second': 60, 'limit_count': 100},
                {'requested_times': list(), 'limit_second': 300, 'limit_count': 300},
                {'requested_times': list(), 'limit_second': 3600, 'limit_count': 1000}
            ]
        else:
            self.last_tran_request_time = datetime.datetime.now()

        self.OnReceiveTrData.connect(self._OnReceiveTrData)
        # self.OnReceiveRealData.connect(self._OnReceiveRealData)
        # self.OnReceiveMsg.connect(self._OnReceiveMsg)
        # self.OnReceiveChejanData.connect(self._OnReceiveChejanData)
        self.OnEventConnect.connect(self._OnEventConnect)

        self.CommConnect_event = PyQt5.QtCore.QEventLoop()
        self.CommRqData_event = PyQt5.QtCore.QEventLoop()

        self.tran_data = None
        self.is_tran_chain = False

        is_login = self.login()
        if not is_login:
            raise AssertionError('[theo.trade.Kiwoom] error: Kiwoom login is failed.')

    def login(self):
        if 0 == self.GetConnectState():
            self.CommConnect()

        if self.GetConnectState() == 1:
            self.log.print('info', 'Success to login (id:{})'.format(self.GetLoginInfo('USER_ID')))
            return True
        else:
            return False

    def get_accounts(self):
        accounts = self.GetLoginInfo('ACCNO').split(';')
        accounts.remove('')
        return accounts

    def get_markets(self):
        return self.market_dictlist.get_values('market')

    def get_codes(self, market):
        market = self.market_dictlist.get_datum(market)
        if market is not None:
            if 'codes' not in market:
                codes = self.GetCodeListByMarket(market['code']).split(';')
                codes.remove('')
                market['codes'] = codes

            return copy.copy(market['codes'])

        return list()

    def get_price_types(self, market, code):
        if code in self.get_codes(market):
            return ['month', 'week', 'day', 'min+30', 'min+1']

        return list()

    def get_item(self, market, code):
        if code in self.get_codes(market):
            data = self.get_tran_data('주식기본정보요청', [code])
            return data[0] if len(data) else None

        return None

    def get_prices(self, market, code, price_type, range=None):
        if price_type in self.get_price_types(market, code):
            start = '19700101' if range is None or 'start' not in range else datetime.datetime.strftime(range['start'], '%Y%m%d')
            end = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d') if range is None or 'end' not in range else datetime.datetime.strftime(range['end'], '%Y%m%d')

            if 'month' == price_type:
                return self.get_tran_data('주식월봉차트조회요청', [code, end, start, '0'], range)
            elif 'week' == price_type:
                return self.get_tran_data('주식주봉차트조회요청', [code, end, start, '0'], range)
            elif 'day' == price_type:
                return self.get_tran_data('주식일봉차트조회요청', [code, end, '0'], range)
            elif 'min' in price_type:
                return self.get_tran_data('주식분봉차트조회요청', [code, price_type.split('+')[1], '0'], range)

        return None

    def set_tran(self):
        """ 주식기본정보요청
        argument_id : 종목코드
        return_id : 종목코드, 종목명, 결산월, 액면가, 자본금, 상장주식, 신용비율, 연중최고, 연중최저, 시가총액,
                     시가총액비중, 외인소진률, 대용가, PER, EPS, ROE, PBR, EV, BPS, 매출액, 영업이익, 당기순이익,
                     250최고, 250최저, 시가, 고가, 저가, 상한가, 하한가, 기준가, 예상체결가, 예상체결수량
                     250최고가일, 250최고가대비율, 250최저가일, 250최저가대비율
                     현재가, 대비기호, 전일대비, 등락율, 거래량, 거래대비, 액면가단위
        """
        self.tran_dictlist.append(
            {
                'caller': 'CommRqData',
                'request': '주식기본정보요청',
                'code': 'opt10001',
                'screen': '1001',
                'data_type': 'single',
                'inputs': ['종목코드'],
                'outputs': [
                    ['종목코드', 'code', 'str'],
                    ['시가총액', 'market capitalization', 'float'],
                    ['250최고', '250 days high', 'float'],
                    ['250최저', '250 days low', 'float'],
                    ['PBR', 'pbr', 'float'],
                    ['PER', 'per', 'float'],
                    ['ROE', 'roe', 'float'],
                    ['EPS', 'eps', 'float'],
                    ['매출액', 'net sales', 'float'],
                    ['영업이익', 'operating profit', 'float'],
                    ['당기순이익', 'net profit', 'float']
                ]
            }
        )

        ''' 주식분봉차트조회요청
        argument_id : 종목코드, 틱범위 (1, 3, 5, 10, 15, 30, 45, 60(분)), 수정주가구분 (0, 1)
        return_id : 일자, 현재가, 시가, 고가, 저가, 거래량
                     수정비율, 대업종구분, 소업종구분, 종목정보, 수정주가이벤트, 전일종가
                     수정주가구분 (1(유상증자), 2(무상증자), 4(배당락), 8(액면분할), 16(액면병합), 32(기업합병),
                                   64(감자), 256(권리락))
        '''
        self.tran_dictlist.append(
            {
                'caller': 'CommRqData',
                'request': '주식분봉차트조회요청',
                'code': 'opt10080',
                'screen': '1501',
                'data_type': 'multi',
                'inputs': ['종목코드', '틱범위', '수정주가구분'],
                'outputs': [
                    ['체결시간', 'datetime', 'datetime'],
                    ['시가', 'open', 'float'],
                    ['현재가', 'close', 'float'],
                    ['고가', 'high', 'float'],
                    ['저가', 'low', 'float'],
                    ['거래량', 'volume', 'float']
                ]
            }
        )

        ''' 주식일봉차트조회요청
        argument_id : 종목코드, 기준일자 (YYYYMMDD), 수정주가구분 (0, 1)
        return_id : 일자, 현재가, 시가, 고가, 저가, 거래량
                     종목코드, 거래대금, 수정비율, 대업종구분, 소업종구분, 종목정보, 수정주가이벤트, 전일종가
                     수정주가구분 (1(유상증자), 2(무상증자), 4(배당락), 8(액면분할), 16(액면병합), 32(기업합병),
                                   64(감자), 256(권리락))
        '''
        self.tran_dictlist.append(
            {
                'caller': 'CommRqData',
                'request': '주식일봉차트조회요청',
                'code': 'opt10081',
                'screen': '1502',
                'data_type': 'multi',
                'inputs': ['종목코드', '기준일자', '수정주가구분'],
                'outputs': [
                    ['일자', 'datetime', 'datetime'],
                    ['시가', 'open', 'float'],
                    ['현재가', 'close', 'float'],
                    ['고가', 'high', 'float'],
                    ['저가', 'low', 'float'],
                    ['거래량', 'volume', 'float']
                ]
            }
        )

        ''' 주식주봉차트조회요청
        argument_id : 종목코드, 기준일자 (YYYYMMDD), 끝일자 (YYYYMMDD), 수정주가구분 (0, 1)
        return_id : 일자, 현재가, 시가, 고가, 저가, 거래량
                     거래대금, 수정비율, 대업종구분, 소업종구분, 종목정보, 수정주가이벤트, 전일종가
                     수정주가구분 (1(유상증자), 2(무상증자), 4(배당락), 8(액면분할), 16(액면병합), 32(기업합병),
                                   64(감자), 256(권리락))
        '''
        self.tran_dictlist.append(
            {
                'caller': 'CommRqData',
                'request': '주식주봉차트조회요청',
                'code': 'opt10082',
                'screen': '1503',
                'data_type': 'multi',
                'inputs': ['종목코드', '기준일자', '끝일자', '수정주가구분'],
                'outputs': [
                    ['일자', 'datetime', 'datetime'],
                    ['시가', 'open', 'float'],
                    ['현재가', 'close', 'float'],
                    ['고가', 'high', 'float'],
                    ['저가', 'low', 'float'],
                    ['거래량', 'volume', 'float']
                ]
            }
        )

        ''' 주식월봉차트조회요청
        argument_id : 종목코드, 기준일자 (YYYYMMDD), 끝일자 (YYYYMMDD), 수정주가구분 (0, 1)
        return_id : 일자, 현재가, 시가, 고가, 저가, 거래량
                     거래대금, 수정비율, 대업종구분, 소업종구분, 종목정보, 수정주가이벤트, 전일종가
                     수정주가구분 (1(유상증자), 2(무상증자), 4(배당락), 8(액면분할), 16(액면병합), 32(기업합병),
                                   64(감자), 256(권리락))
        '''
        self.tran_dictlist.append(
            {
                'caller': 'CommRqData',
                'request': '주식월봉차트조회요청',
                'code': 'opt10083',
                'screen': '1504',
                'data_type': 'multi',
                'inputs': ['종목코드', '기준일자', '끝일자', '수정주가구분'],
                'outputs': [
                    ['일자', 'datetime', 'datetime'],
                    ['시가', 'open', 'float'],
                    ['현재가', 'close', 'float'],
                    ['고가', 'high', 'float'],
                    ['저가', 'low', 'float'],
                    ['거래량', 'volume', 'float']
                ]
            }
        )

    def set_market(self):
        self.market_dictlist.extend_data([
            {'market': 'kospi', 'code': 0},
            {'market': 'kosdaq', 'code': 10},
            # {'market': 'ELW', 'code': 3},
            # {'market': '뮤추얼펀드', 'code': 4},
            # {'market': '신주인수권', 'code': 5},
            # {'market': '리츠', 'code': 6},
            # {'market': 'ETF', 'code': 8},
            # {'market': '하이일드펀드', 'code': 9},
            # {'market': 'K-OTC', 'code': 30},
            # {'market': '코넥스(KONEX)', 'code': 50},
        ])

    def set_error(self):
        self.error_dictlist.extend_data([
            {'code': 0, 'error': 'OP_ERR_NONE', 'description': '정상처리'},
            {'code': -10, 'error': 'OP_ERR_FAIL', 'description': '실패'},
            {'code': -100, 'error': 'OP_ERR_LOGIN', 'description': '사용자정보교환실패'},
            {'code': -101, 'error': 'OP_ERR_CONNECT', 'description': '서버접속실패'},
            {'code': -102, 'error': 'OP_ERR_VERSION', 'description': '버전처리실패'},
            {'code': -103, 'error': 'OP_ERR_FIREWALL', 'description': '개인방화벽실패'},
            {'code': -104, 'error': 'OP_ERR_MEMORY', 'description': '메모리보호실패'},
            {'code': -105, 'error': 'OP_ERR_INPUT', 'description': '함수입력값오류'},
            {'code': -106, 'error': 'OP_ERR_SOCKET_CLOSED', 'description': '통신연결종료'},
            {'code': -200, 'error': 'OP_ERR_SISE_OVERFLOW', 'description': '시세조회과부하'},
            {'code': -201, 'error': 'OP_ERR_RQ_STRUCT_FAIL', 'description': '전문작성초기화실패'},
            {'code': -202, 'error': 'OP_ERR_RQ_STRING_FAIL', 'description': '전문작성입력값오류'},
            {'code': -203, 'error': 'OP_ERR_NO_DATA', 'description': '데이터없음'},
            {'code': -204, 'error': 'OP_ERR_OVER_MAX_DATA', 'description': '조회가능한종목수초과'},
            {'code': -205, 'error': 'OP_ERR_DATA_RCV_FAIL', 'description': '데이터수신실패'},
            {'code': -206, 'error': 'OP_ERR_OVER_MAX_FID', 'description': '조회가능한FID수초과'},
            {'code': -207, 'error': 'OP_ERR_REAL_CANCEL', 'description': '실시간해제오류'},
            {'code': -300, 'error': 'OP_ERR_ORD_WRONG_INPUT', 'description': '입력값오류'},
            {'code': -301, 'error': 'OP_ERR_ORD_WRONG_ACCTNO', 'description': '계좌비밀번호없음'},
            {'code': -302, 'error': 'OP_ERR_OTHER_ACC_USE', 'description': '타인계좌사용오류'},
            {'code': -303, 'error': 'OP_ERR_MIS_2BILL_EXC', 'description': '주문가격이20억원을초과'},
            {'code': -304, 'error': 'OP_ERR_MIS_5BILL_EXC', 'description': '주문가격이50억원을초과'},
            {'code': -305, 'error': 'OP_ERR_MIS_1PER_EXC', 'description': '주문수량이총발행주수의1%초과오류'},
            {'code': -306, 'error': 'OP_ERR_MIS_3PER_EXC', 'description': '주문수량이총발행주수의5%초과오류'},
            {'code': -307, 'error': 'OP_ERR_SEND_FAIL', 'description': '주문전송실패'},
            {'code': -308, 'error': 'OP_ERR_ORD_OVERFLOW', 'description': '주문전송과부하'},
            {'code': -309, 'error': 'OP_ERR_MIS_300CNT_EXC', 'description': '주문수량300계약초과'},
            {'code': -310, 'error': 'OP_ERR_MIS_500CNT_EXC', 'description': '주문수량500계약초과'},
            {'code': -340, 'error': 'OP_ERR_WRONG_ACCTINFO', 'description': '계좌정보없음'},
            {'code': -500, 'error': 'OP_ERR_ORD_SYMCODE_EMPTY', 'description': '종목코드없음'},
            {'code': -310, 'error': 'OP_ERR_MIS_500CNT_EXC', 'description': '주문수량500계약초과 아래'},
            {'code': -311, 'error': 'OP_ERR_ORD_OVERFLOW', 'description': '주문전송제한 과부하'},
            {'code': -340, 'error': 'OP_ERR_ORD_WRONG_ACCTINFO', 'description': '계좌정보없음'}
        ])

    def get_tran_data(self, request, arguments, range=None):
        tran = self.tran_dictlist.get_datum(request)

        inputs = list()
        for input_id in tran['inputs']:
            inputs.append({'id': input_id})

        for index, input_value in enumerate(arguments):
            inputs[index]['value'] = input_value

        self.SetInputValues(inputs)

        data = list()
        result, is_tran_chain, tran_data = self.CommRqData(tran['request'], tran['code'], 0, tran['screen'])
        request_data_count = 1

        if result == 0:
            if Kiwoom.remove_over_range(tran_data, range):
                is_tran_chain = False

            data.extend(copy.copy(tran_data))

            while is_tran_chain:
                self.SetInputValues(inputs)

                result, is_tran_chain, tran_data = self.CommRqData(request, tran['code'], 2, tran['screen'])
                request_data_count = request_data_count + 1
                if 0 == (request_data_count % 5):
                    self.log.print('info', 'Request data is working in chain(count:{})'.format(request_data_count))

                if result == 0:
                    if Kiwoom.remove_over_range(tran_data, range):
                        is_tran_chain = False

                    data.extend(copy.copy(tran_data))
                else:
                    is_tran_chain = False

        return data

    @staticmethod
    def remove_over_range(prices, range):
        if range is not None:
            start = range['start'] if 'start' in range.keys() else None
            end = range['end'] if 'end' in range.keys() else None

            remove_prices = list()
            for price in prices:
                if start is not None and price['datetime'] < start:
                    remove_prices.append(price)
                elif end is not None and price['datetime'] > end:
                    remove_prices.append(price)

            if len(remove_prices):
                for price in remove_prices:
                    prices.remove(price)

                return True

        return False

    ''' 1. CommConnect > 5. OnEventConnect
    original form : LONG CommConnect()
    description : 로그인 윈도우를 실행한다.
    return : 0 (성공), - (실패)
    etc : 로그인이 성공하거나 실패하는 경우 OnEventConnect 이벤트가 발생하고
          이벤트의 인자 값으로 로그인 성공 여부를 알 수 있다.
    '''
    def CommConnect(self):
        result = self.dynamicCall('CommConnect()')
        if 0 == result:
            self.log.print('debug', 'CommConnect() needs to wait OnEventConnect()')
            self.CommConnect_event.exec_()

        return result

    ''' 3. CommRqData > 1. OnReceiveTrData
    original form : LONG CommRqData(BSTR sRQName, BSTR sTrCode, long nPrevNext, BSTR sScreenNo)
    description : Tran 을 서버로 송신한다.
    arguments : sRQName (사용자구분 명), sTrCode (Tran 명), nPrevNext (0:조회, 2:연속), sScreenNo (4자리의 화면번호)
    return : 0 (성공), - (실패)
    '''
    def CommRqData(self, sRQName, sTrCode, nPrevNext, sScreenNo):
        self.is_tran_chain = False
        self.tran_data = list()

        if 1 == Kiwoom.tran_request_limitation_evasion_type:
            self.evade_request_tran_limitation_by_limitation_list()
        else:
            self.evade_request_tran_limitation_by_minimum_seconds()

        result = self.dynamicCall(
            'CommRqData(QString, QString, int, QString)', [sRQName, sTrCode, nPrevNext, sScreenNo])

        if 0 == result:
            self.log.print('debug', 'CommRqData() needs to wait OnReceiveTrData()')
            self.CommRqData_event.exec_()

        return result, self.is_tran_chain, self.tran_data

    def evade_request_tran_limitation_by_limitation_list(self):
        for tran_request_limitation in self.tran_request_limitations:
            current_time = datetime.datetime.now()

            over_time_count = 0
            for requested_time in tran_request_limitation['requested_times']:
                if (current_time - requested_time).total_seconds() > tran_request_limitation['limit_second']:
                    over_time_count = over_time_count + 1

            while over_time_count:
                tran_request_limitation['requested_times'].pop(0)
                over_time_count = over_time_count - 1

            if len(tran_request_limitation['requested_times']) == tran_request_limitation['limit_count']:
                wait_time = tran_request_limitation['limit_second'] - (current_time - tran_request_limitation['requested_times'][0]).total_seconds()

                if wait_time >= 5:
                    self.log.print('info', 'wait gap time(sec:{}) for limit count({}) in sec({})'.format(wait_time, tran_request_limitation['limit_count'], tran_request_limitation['limit_second']))

                time.sleep(wait_time)
                tran_request_limitation['requested_times'].pop(0)

            tran_request_limitation['requested_times'].append(current_time)

    def evade_request_tran_limitation_by_minimum_seconds(self):
        gap = datetime.datetime.now() - self.last_tran_request_time

        if gap.total_seconds() < 3.6:  # 3600 secconds / 1000 requests
            wait_time = 3.6 - gap.total_seconds()
            # self.log.print('debug', 'wait gap time(sec:{}) for minimum seconds'.format(wait_time))
            time.sleep(wait_time)

        self.last_request_time = datetime.datetime.now()

    ''' 4. GetLoginInfo
    original form : BSTR GetLoginInfo(BSTR sTag)
    description : 로그인한 사용자 정보를 반환한다.
    arguments : sTag (사용자 정보 구분 TAG 값)
    return : TAG 값에 따른 데이터 반환
    etc : sTag 에 들어 갈 수 있는 값
          ACCOUNT_CNT : 전체 계좌 개수를 반환한다.
          ACCNO : 전체 계좌를 반환한다. 계좌별 구분은 ‘;’ 이다.
          USER_ID : 사용자 ID를 반환한다.
          USER_NAME : 사용자명을 반환한다.
          KEY_BSECGB : 키보드보안 해지여부. 0 (정상), 1 (해지)
          FIREW_SECGB: 방화벽 설정 여부. 0 (미설정), 1 (설정), 2 (해지) 
    '''
    def GetLoginInfo(self, sTag):
        return self.dynamicCall('GetLoginInfo(QString)', [sTag]).strip()

    ''' 7. SetInputValue
    original form : void SetInputValue(BSTR sID, BSTR sValue)
    description : Tran 입력 값을 서버통신 전에 입력한다.
    arguments : sID (아이템명),  sValue (입력 값) 
    '''
    def SetInputValue(self, sID, sValue):
        self.dynamicCall('SetInputValue(QString, QString)', [sID, sValue])

    def SetInputValues(self, inputs):
        for input in inputs:
            self.SetInputValue(input['id'], input['value'])

    ''' 11. GetRepeatCnt
    original form : LONG GetRepeatCnt(LPCTSTR sTrCode, LPCTSTR sRecordName)
    description : 레코드 반복횟수를 반환한다.
    arguments : sTrCode (Tran 명), sRecordName (레코드 명)
    return : 레코드의 반복횟수
    '''
    def GetRepeatCnt(self, sTrCode, sRecordName):
        return self.dynamicCall('GetRepeatCnt(QString, QString)', [sTrCode, sRecordName])

    ''' 14. GetCodeListByMarket
    original form : BSTR GetCodeListByMarket(LPCTSTR sMarket)
    description : 시장구분에 따른 종목코드를 반환한다.
    arguments : sMarket (시장구분)
    return : 종목코드 리스트, 종목간 구분은 ’;’ 이다.
    '''
    def GetCodeListByMarket(self, sMarket):
        return self.dynamicCall('GetCodeListByMarket(QString)', [sMarket]).strip()

    ''' 15. GetConnectState
    original form : LONG GetConnectState()
    description : 현재접속상태를 반환한다.
    arguments : 없음
    return : 1 (연결완료), 0 (미연결)
    '''
    def GetConnectState(self):
        return self.dynamicCall('GetConnectState()')

    ''' 24. GetCommData
    original form : BSTR GetCommData(LPCTSTR strTrCode, LPCTSTR strRecordName, long nIndex, LPCTSTR strItemName)
    description : 수신 데이터를 반환한다.
    arguments : strTrCode (Tran 코드), strRecordName(레코드명), nIndex(복수데이터 인덱스), strItemName(아이템명)
    return : 수신 데이터
    '''
    def GetCommData(self, strTrCode, strRecordName, nIndex, strItemName):
        return self.dynamicCall(
            'GetCommData(QString, QString, int, QString)', [strTrCode, strRecordName, nIndex, strItemName]).strip()

    ''' 1. OnReceiveTrData < 3. CommRqData
    original form : void OnReceiveTrData(LPCTSTR sScrNo, LPCTSTR sRQName, LPCTSTR sTrCode, LPCTSTR sRecordName,
                    LPCTSTR sPreNext, LONG nDataLength, LPCTSTR sErrorCode, LPCTSTR sMessage, LPCTSTR sSplmMsg)
    description : 서버통신 후 데이터를 받은 시점을 알려준다.
    arguments : sScrNo (화면번호), sRQName (사용자구분 명), sTrCode (Tran 명),
                sRecordName (Record 명), sPreNext (연속조회 유무)
    etc : sRQName, sTrCode 는 CommRqData 의 입력값과 매핑되는 이름이다.
    '''
    def _OnReceiveTrData(self, sScrNo, sRQName, sTrCode, sRecordName, sPreNext, none_used_1, none_used_2, none_used_3, none_used_4):
        self.log.print('debug', 'OnReceiveTrData(sScrNo:{}/sRQName:{}/sTrCode:{}/sRecordName:{}/sPreNext:{})'.format(sScrNo, sRQName, sTrCode, sRecordName, sPreNext))

        tran = self.tran_dictlist.get_datum(sRQName)
        if tran is None:
            self.log.print('critical', 'OnReceiveTrData(sScrNo:{}/sRQName:{}/sTrCode:{}/sRecordName:{}/sPreNext:{}) is not valid.'.format(sScrNo, sRQName, sTrCode, sRecordName, sPreNext))
            raise AssertionError('OnReceiveTrData(sScrNo:{}/sRQName:{}/sTrCode:{}/sRecordName:{}/sPreNext:{}) is not valid.'.format(sScrNo, sRQName, sTrCode, sRecordName, sPreNext))

        if tran['caller'] == 'CommRqData':
            if sPreNext == '2':
                self.is_tran_chain = True

            data_count = 0
            if tran['data_type'] == 'single':
                data_count = 1
            elif tran['data_type'] == 'multi':
                data_count = self.GetRepeatCnt(sTrCode, sRecordName)

            for index in range(data_count):
                datum = dict()

                for output in tran['outputs']:
                    value = self.GetCommData(sTrCode, sRecordName, index, output[0])

                    if len(value) == 0 and (output[2] == 'float' or output[2] == 'int'):
                        value = '0'

                    if output[2] == 'datetime':
                        if output[0] == '일자':
                            datum[output[1]] = datetime.datetime.strptime(value, '%Y%m%d')

                        elif output[0] == '체결시간':
                            datum[output[1]] = datetime.datetime.strptime(value[:12], '%Y%m%d%H%M')

                        else:
                            self.log.print('critical', 'value({}) is not valid of output({})'.format(value, output))
                            raise AssertionError('value({}) is not valid of output({})'.format(value, output))

                    elif output[2] == 'str':
                        datum[output[1]] = value

                    elif output[2] == 'float':
                        if value[0] == '-' or value[0] == '+':
                            value = value[1:]

                        datum[output[1]] = float(value)

                    elif output[2] == 'int':
                        if value[0] == '-' or value[1] == '+':
                            value = value[1:]

                        datum[output[1]] = int(value)

                    else:
                        self.log.print('critical', 'value({}) is not valid of output({})'.format(value, output))
                        raise AssertionError('value({}) is not valid of output({})'.format(value, output))

                self.tran_data.append(datum)

            self.CommRqData_event.exit()

    ''' 5. OnEventConnect < 1. CommConnect
    original form : void OnEventConnect(LONG nErrCode)
    description : 서버 접속 관련 이벤트
    arguments : nErrCode (에러 코드)
    etc : nErrCode 가 0이면 로그인 성공, 음수면 실패 음수인 경우는 에러 코드 참조
    '''
    def _OnEventConnect(self, nErrCode):
        self.log.print('debug', 'OnEventConnect({})'.format(self.error_dictlist.get_datum(nErrCode)['error']))
        self.CommConnect_event.exit()
