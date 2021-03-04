import json
import math

"""
    处理异常的装饰器类
"""


class DecorateExcept:
    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        try:
            function_result = self.function(*args, **kwargs)
        except FileNotFoundError as result:  # filename文件 没找到
            print("Error: file is not found %s" % result)
        except AttributeError as result:
            print("Error: %s" % result)
        except Exception as result:
            print("unkown Error: %s" % result)
        else:
            return function_result


"""
    合约模型类
"""


class PositionModel:
    @classmethod
    def position_key(cls):
        return "pos"

    @classmethod
    def entryprice_key(cls):
        return "entryprice"

    @classmethod
    def target_position_key(cls):
        return "target_pos"

    def __init__(self, position_dictionary):
        if PositionModel.position_key() in position_dictionary.keys():
            self.lots = position_dictionary[PositionModel.position_key()]
        else:
            self.lots = None

        if PositionModel.entryprice_key() in position_dictionary.keys():
            self.entry_price = position_dictionary[PositionModel.entryprice_key()]
        else:
            self.entry_price = None

        if PositionModel.target_position_key() in position_dictionary.keys():
            self.target_position = position_dictionary[PositionModel.target_position_key()]
        else:
            self.target_position = None

    def model_to_dictionary(self):
        empty_dictionary = {}

        if self.lots is not None:
            empty_dictionary[PositionModel.position_key()] = self.lots

        if self.entry_price is not None:
            empty_dictionary[PositionModel.entryprice_key()] = self.entry_price

        if self.target_position is not None:
            empty_dictionary[PositionModel.target_position_key()] = self.target_position

        return empty_dictionary


class ContractModel:
    def __init__(self, contract_name, position_model):
        self.name = contract_name
        self.__position_model = position_model

    @property
    def position_model(self):
        return self.__position_model

    @position_model.setter
    def position_model(self, position_model):
        self.__position_model = position_model

    @position_model.getter
    def position_model(self):
        return self.__position_model

    @classmethod
    def dictionary_to_models(cls, data_dictionary):
        contract_models = []
        for contract_name, position_dictionary in data_dictionary.items():
            contract_model = ContractModel(contract_name=contract_name, position_model=PositionModel(position_dictionary=position_dictionary))
            contract_models.append(contract_model)
        return contract_models

    @classmethod
    def models_to_dictionary(cls, *models):
        empty_dictionary = {}
        for model in models:
            empty_dictionary[model.name] = model.position_model.model_to_dictionary()
        return empty_dictionary


"""
    持仓json文件操作类
"""


class PositionJsonOperator:
    """
     操作 json文件 的 类
     ps: 使用时, 需要导入 json、math库
    """

    @classmethod
    def __read_type(cls):
        return "r"

    @classmethod
    def __write_type(cls):
        return "w"

    @classmethod
    def __utf_8_encoding(cls):
        return "utf-8"



    # ------------------ public part ------------------
    @classmethod
    def tqz_load_jsonfile(cls, jsonfile=None):
        if jsonfile is None:
            exception = Exception("Error: filename is None")
            raise exception
        else:
            return cls.__writeReadFile_except_operation(jsonfile=jsonfile, operation_type=cls.__read_type())

    @classmethod
    def tqz_write_jsonfile(cls, content=None, target_jsonfile=None):
        if target_jsonfile is None:
            exception = Exception("Error: filename is None")
            raise exception
        else:
            cls.__writeReadFile_except_operation(jsonfile=target_jsonfile, content=content, operation_type=cls.__write_type())

    @classmethod
    def tqz_sum_position_all_jsonfile(cls, *jsonfile_list, target_jsonfile):
        """
        加总多个 json文件的 持仓, 并写入新的目标json文件中
        :param jsonfile_list: 字符串数组
        :param target_jsonfile: 要存入的 json文件名
        """
        jsonfile_content_list = []
        [jsonfile_content_list.append(cls.tqz_load_jsonfile(jsonfile)) for jsonfile in jsonfile_list]

        content_dic = cls.__sum_position_all_keyValueNotFound_except_operation(dic_list=jsonfile_content_list)

        cls.tqz_write_jsonfile(content=content_dic, target_jsonfile=target_jsonfile)

    @classmethod
    def tqz_multi_position_all(cls, *jsonfile_list, multi):
        """
        按倍数调整 多个json文件的 持仓
        :param jsonfile_list: 需要调整持仓的 json文件数组
        :param multi: 倍数
        """
        [cls.__multi_position(source_jsonfile=jsonfile, multi=multi) for jsonfile in jsonfile_list]

    @classmethod
    def tqz_empty_position_all(cls, *jsonfile_list):
        """
        清空 多个json文件的 持仓
        :param jsonfile_list: 需要清空的 json文件数组
        """
        cls.tqz_multi_position_all(*jsonfile_list, multi=0)

    # ------------------ private part ------------------
    @classmethod
    def __multi_position(cls, source_jsonfile, multi):
        source_content = cls.tqz_load_jsonfile(jsonfile=source_jsonfile)

        source_content = cls.__multi_position_keyValueNotFound_except_operation(source_content=source_content, multi=multi)

        cls.tqz_write_jsonfile(content=source_content, target_jsonfile=source_jsonfile)

    @classmethod
    def __empty_position(cls, source_jsonfile):
        cls.__multi_position(source_jsonfile=source_jsonfile, multi=0)

    # ------------------ except operation part ------------------
    @classmethod
    @DecorateExcept
    def __writeReadFile_except_operation(cls, jsonfile=None, content=None, operation_type="r"):
        if cls.__read_type() is operation_type:
            with open(jsonfile, operation_type, encoding=cls.__utf_8_encoding()) as fp:
                return json.load(fp=fp)
        elif cls.__write_type() is operation_type:
            with open(jsonfile, operation_type, encoding=cls.__utf_8_encoding()) as fp:
                json.dump(content, fp=fp, ensure_ascii=False, indent=4)  # 参数indent: json文件按格式写入, 距行首空4格;

    @classmethod
    # @DecorateExcept
    def __sum_position_all_keyValueNotFound_except_operation(cls, dic_list=None):

        new_json_contract_models = []
        new_json_contract_names = []

        temp_dic_list = []
        for single_json_content in dic_list:
            temp_dic = {}
            for key, value in single_json_content.items():
                vt_symbol = key.split(".")[0] + "." + key.split(".")[1]
                temp_dic[vt_symbol] = value
            temp_dic_list.append(temp_dic)
        dic_list = temp_dic_list

        all_json_contract_models = []
        if dic_list is not None:
            [all_json_contract_models.append(ContractModel.dictionary_to_models(data_dictionary=dic)) for dic in dic_list]

        for contract_models in all_json_contract_models:
            for contract_model in contract_models:
                if contract_model.name not in new_json_contract_names:
                    new_json_contract_models.append(ContractModel(contract_name=contract_model.name, position_model=contract_model.position_model))
                    new_json_contract_names.append(contract_model.name)
                else:
                    find_contract_model = cls.__find_contract_model(*new_json_contract_models, model_name=contract_model.name)
                    find_contract_model.position_model.lots += contract_model.position_model.lots

        return ContractModel.models_to_dictionary(*new_json_contract_models)

    @classmethod
    def __find_contract_model(cls, *contract_models, model_name):
        for contract_model in contract_models:
            if contract_model.name == model_name:
                return contract_model
        return None


    @classmethod
    @DecorateExcept
    def __multi_position_keyValueNotFound_except_operation(cls, source_content=None, multi=1):

        all_json_contract_models = []
        if source_content is not None:
            [all_json_contract_models.append(ContractModel(contract_name=contract_name, position_model=PositionModel(position_dictionary=position_dictionary))) for contract_name, position_dictionary in source_content.items()]

        for contract_model in all_json_contract_models:
            before_multi_lots = contract_model.position_model.lots

            # multi_lots: 按倍数调整完后的仓位
            if before_multi_lots > 0:
                multi_lots = math.floor(contract_model.position_model.lots * multi)
            else:
                multi_lots = math.floor(-1 * contract_model.position_model.lots * multi) * -1

            # 按倍数调整完, 确保持仓至少保留1手;
            if (before_multi_lots > 0) and (multi_lots is 0):  # 原先持有多单, 仓位调整完后为 0;
                multi_lots = 1
            elif (before_multi_lots < 0) and (multi_lots is 0):  # 原先持有空单, 仓位调整完后为 0;
                multi_lots = -1

            contract_model.position_model.lots = multi_lots

        return ContractModel.models_to_dictionary(*all_json_contract_models)


def __main_engine():
    list = [
        "symbol_2.json",
        "symbol_3.json",
        "symbol_4.json",
        "symbol_5.json"
    ]

    target_jsonfile = "test.json"

    PositionJsonOperator.tqz_sum_position_all_jsonfile(*list, target_jsonfile=target_jsonfile)

    # PositionJsonOperator.tqz_multi_position_all(target_jsonfile, multi=0.5)
    # PositionJsonOperator.tqz_empty_position_all(target_jsonfile)


if __name__ == '__main__':
    __main_engine()
