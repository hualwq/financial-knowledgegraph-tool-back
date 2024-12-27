import json

# Mapping dictionary for Chinese to English and its reverse for English to Chinese
chinese_to_english = {
    "公司名称": "company_name",
    "社会信用代码": "credit_number",
    "省份": "province",
    "公司类型": "company_type",
    "市": "city",
    "区县信息": "district_info",
    "主营业务": "main_business",
    "A股证券代码": "a_stock_code",
    "组织形式": "organization_form",
    "证券名称": "security_name",
    "股票简称": "stock_abbreviation",
    "证券代码": "security_code",
    "董事会秘书代码": "board_secretary_code",
    "经营范围": "business_scope",
    "注册地址": "registered_address",
    "法定代表人": "legal_representative",
    "公司曾用名": "former_company_name",
    "公司电话": "company_phone",
    "公司简介": "company_profile",
    "英文名称": "english_name",
    "B股证券代码": "b_stock_code",
    "实际控制人": "actual_controller",
}

# Create a reverse mapping for English to Chinese
english_to_chinese = {v: k for k, v in chinese_to_english.items()}

# Function to translate JSON keys using the given mapping
def translate_labels(data, to_english=True):
    if to_english:
        # Translate Chinese keys to English
        return {chinese_to_english.get(k, k): v for k, v in data.items()}
    else:
        # Translate English keys to Chinese
        return {english_to_chinese.get(k, k): v for k, v in data.items()}

# Example JSON data to be converted
json_data = {
    "公司名称": "某公司",
    "省份": "广东",
    "市": "深圳",
    "法定代表人": "张三"
}

# Choose the translation direction
translated_data_to_english = translate_labels(json_data, to_english=True)
translated_data_to_chinese = translate_labels(translated_data_to_english, to_english=False)

# Display the results
print("Original data:", json_data)
print("Translated to English:", translated_data_to_english)
print("Translated back to Chinese:", translated_data_to_chinese)
