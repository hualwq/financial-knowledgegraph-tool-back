import time
from celery import Celery
from py2neo import Graph, NodeMatcher, Node, Relationship, RelationshipMatcher
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd
import requests
from io import BytesIO
import io
import os
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
from django.core.cache import cache
from time import sleep
from datetime import datetime
from django.views.decorators.http import require_GET

# graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))
# matcher = NodeMatcher(graph)

graph = Graph("neo4j://localhost:7687", auth=("neo4j", "1598273166wsy."))
matcher = NodeMatcher(graph)
rmatcher = RelationshipMatcher(graph)

SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.5/chat'
SPARKAI_APP_ID = '7bb8f7d8'
SPARKAI_API_SECRET = 'Zjc5MmM3N2NlMjllODRkNWRmYTY5NmIy'
SPARKAI_API_KEY = '6d6b00f19b4c602fbbabec2a4fa0c76f'
#星火认知大模型Spark Max的domain值，其他版本大模型domain值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
SPARKAI_DOMAIN = 'generalv3.5'

spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )


chinese_to_english = {
    "公司中文名称": "company_name",
    "统一社会信用代码": "credit_number",
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


english_to_chinese = {v: k for k, v in chinese_to_english.items()}

# Function to translate JSON keys using the given mapping
def translate_labels(data, to_english=True):
    if to_english:
        # Translate Chinese keys to English
        return {chinese_to_english.get(k, k): v for k, v in data.items()}
    else:
        # Translate English keys to Chinese
        return {english_to_chinese.get(k, k): v for k, v in data.items()}

def create_company(data):
    graph.run("""
        CREATE (c:Company {
            `公司中文名称`: $company_name,
            `统一社会信用代码`: $credit_number,
            `省份`: $province,
            `公司类型`: $company_type,
            `市`: $city,
            `区县信息`: $district_info,
            `主营业务`: $main_business,
            `A股证券代码`: $a_stock_code,
            `组织形式`: $organization_form,
            `证券名称`: $security_name,
            `股票简称`: $stock_abbreviation,
            `证券代码`: $security_code,
            `董事会秘书代码`: $board_secretary_code,
            `经营范围`: $business_scope,
            `注册地址`: $registered_address,
            `法定代表人`: $legal_representative,
            `公司曾用名`: $former_company_name,
            `公司电话`: $company_phone,
            `公司简介`: $company_profile,
            `英文名称`: $english_name,
            `B股证券代码`: $b_stock_code,
            `实际控制人`: $actual_controller
        })
    """, **data)

def Querynodes(data):
    label = data[0]['label']
    value = data[0]['value']
    if label == "company_name":
        node = matcher.match("Company").where(f"_.公司中文名称= '{ value }'").first()
        if node:
            return node
        else:
            query = f"match (n:Company) where n.`曾用名` contains '{value}' return n"
            result = graph.run(query).data()
            return result
    elif label == "credit_number":
        return matcher.match("Company").where(f"_.统一社会信用代码= '{value}'").first()
    elif label == "english_name":
        return matcher.match("Company").where(f"_.英文名称= '{value}'").first()
    elif label == "legal_representative":
        return matcher.match("Company").where(f"_.法定代表人= '{value}'").first()
    elif label == "security_code":
        return matcher.match("Company").where(f"_.证券代码= '{value}'").first()
    elif label == "stock_abbreviation":
        return matcher.match("Company").where(f"_.股票简称= '{value}'").first()

def QueryRelationship(node1, node2, relationship):
    query = ''
    if relationship:
        query = f"MATCH (c1:Company)-[r:{relationship}]->(c2:Company) WHERE c1.`统一社会信用代码` = '{node1}' AND c2.`统一社会信用代码` = '{node2}' RETURN type(r) as relationship_type, r"
    else:
        query = f"MATCH (c1:Company)-[r]->(c2:Company) WHERE c1.`统一社会信用代码` = '{node1}' AND c2.`统一社会信用代码` = '{node2}' RETURN type(r) as relationship_type, r"
    result = graph.run(query).data()
    relationship = str(result[0]['r'])
    return relationship.__str__().encode("utf-8").decode("unicode_escape")

def QueryRelationship_byname(node1, node2, relationship):
    query = ''
    if relationship:
        query = f"MATCH (c1:Company)-[r:{relationship}]->(c2:Company) WHERE c1.`公司中文名称` = '{node1}' AND c2.`公司中文名称` = '{node2}' RETURN type(r) as relationship_type, r"
    else:
        query = f"MATCH (c1:Company)-[r]->(c2:Company) WHERE c1.`公司中文名称` = '{node1}' AND c2.`公司中文名称` = '{node2}' RETURN type(r) as relationship_type, r"
    result = graph.run(query)
    relationships = []
    for record in result:
        relationship_type = record["relationship_type"]
        relationship_properties = dict(record["r"])  # 将关系属性转换为字典
        relationships.append({
            "type": relationship_type,
            "properties": relationship_properties
        })
    if relationships:
        return True
    else:
        return False

def QueryRelationship_withnonode(relation_name):
    query = f"MATCH ()-[r:{relation_name}]->()  RETURN type(r) as relationship_type, r LIMIT 1"
    result = graph.run(query).data()
    relationship = str(result[0]['r'])
    # relationships = []
    # for record in result:
    #     relationship_type = record["relationship_type"]
    #     relationship_properties = dict(record["r"])  # 将关系属性转换为字典
    #     relationships.append({
    #         "type": relationship_type,
    #         "properties": relationship_properties
    #     })
    return relationship.__str__().encode("utf-8").decode("unicode_escape")

def query_node(request):
    if request.method == 'POST':
        dat = json.loads(request.body)
        node = Querynodes(dat)
        if node:
            data = dict(node)
            data = translate_labels(data, to_english=True)
            return JsonResponse(data)
        else:
            return JsonResponse({'status': 'error', 'message': 'no such node'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def print_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(type(data))
        print(data)
        return JsonResponse({'status': 'success', 'message': 'Node added'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def add_node(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        credit_number = data["credit_number"]
        node = matcher.match("Company").where(f"_.统一社会信用代码= '{ credit_number }'").first()
        if not node:
            create_company(data)
        else:
            JsonResponse({'status': 'error', 'message': 'Node existed'})
        return JsonResponse({'status': 'success', 'message': 'Node added'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def delete_node(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        credit_number = data['1']['value']
        print(data)
        node = matcher.match("Company").where(f"_.统一社会信用代码= '{ credit_number }'").first()
        if node:
            graph.delete(node)
            return JsonResponse({'status': 'success', 'message': 'delete successful'})
        else:
            return JsonResponse({'status': 'error', 'message': 'no such node, please try again'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def add_node_excel(request):
    if request.method == 'POST' and request.FILES:
        excel_file = request.FILES['file']
        try:
            df = pd.read_excel(excel_file, keep_default_na=False)
            df_unique = df.drop_duplicates()
            total_rows = len(df_unique)
            existing_nodes = []
            for index, row in df_unique.iterrows():
                company_name = row['公司中文名称']
                node = matcher.match("Company").where(f"_.公司中文名称='{company_name}'").first()
                if not node:
                    company_node = Node("Company", name=company_name, **row.to_dict())
                    graph.create(company_node)
                else:
                    existing_nodes.append(row)
                progress = int((index + 1) / total_rows * 100)  # 计算百分比进度
                cache.set('task_progress', progress)
            if existing_nodes:
                existing_df = pd.DataFrame(existing_nodes)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    existing_df.to_excel(writer, index=False, sheet_name='Sheet1')
                output.seek(0)
                response = HttpResponse(output,
                                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="existing_nodes.xlsx"'
                # 将附加信息添加到响应头中
                response['status'] = 'success'
                response['message'] = 'Some nodes were not added'
                return response
            else:
                return JsonResponse({'status': 'success', 'message': 'All nodes added successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def add_relationship_excel(request):
    if request.method == "POST":
        relationship_name = request.POST.get("relationship_name")
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'status': 'error', 'message':'文件错误'})
        else:
            try:
                # 读取 Excel 文件
                df = pd.read_excel(file)
                total_rows = len(df)
                # 获取列名
                columns = df.columns
                # 遍历每行，添加关系到 Neo4j
                failed_data = []
                id = 0
                for index, row in df.iterrows():
                    id += 1
                    company1 = row[columns[0]]  # 第一列，"公司1"
                    company2 = row[columns[1]]  # 第二列，"公司2"
                    # 获取关系属性列
                    relationship_properties = {
                        col: row[col] for col in columns[2:]  # 从第三列开始是关系属性
                    }

                    # 创建节点和关系
                    node1 = matcher.match("Company").where(f"_.公司中文名称= '{ company1 }'").first()
                    node2 = matcher.match("Company").where(f"_.公司中文名称= '{ company2 }'").first()
                    if node2 and node1:
                        if not QueryRelationship_byname(company1, company2, relationship_name):
                            relationship = Relationship(node1, relationship_name, node2, **relationship_properties)
                            graph.create(relationship)
                    else:
                        failed_data.append({
                            "公司1": company1,
                            "公司2": company2,
                            **relationship_properties})
                progress = int((id / total_rows) * 100)
                cache.set('task_progress', progress)  # 更新缓存中的进度
                if failed_data:
                    failed_df = pd.DataFrame(failed_data)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                        failed_df.to_excel(writer, index=False, sheet_name="Sheet")
                    output.seek(0)

                    response = HttpResponse(
                        output,
                        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    response["Content-Disposition"] = 'attachment; filename="未成功添加的关系.xlsx"'
                    response['status'] = "success"
                    response["message"] = "某些关系未成功添加，可能因为节点不在知识图谱中！"
                    return response
                else:
                    return JsonResponse({'status': 'success', 'message':'All relationships added successfully'})

            except Exception as e:
                print("Error processing request:", e)
                return JsonResponse({"error": "Failed to process file"}, status=400)
    return JsonResponse({'status': 'error', 'message': 'try again'})


def query_relationship(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        relation_name = data['relation_name']
        if data['company1'] and data['company2']:
            label1 = data['company1'][0]['label']
            value1 = data['company1'][0]['value']
            label2 = data['company2'][0]['label']
            value2 = data['company2'][0]['value']
            node1 = None
            node2 = None
            if label1 == 'company_name':
                node1 = matcher.match("Company").where(f"_.公司中文名称= '{value1}'").first()
            elif label1 == 'credit_number':
                node1 = matcher.match("Company").where(f"_.统一社会信用代码= '{value1}'").first()
            if label2 == 'company_name':
                node2 = matcher.match("Company").where(f"_.公司中文名称= '{value2}'").first()
            elif label2 == 'credit_number':
                node2 = matcher.match("Company").where(f"_.统一社会信用代码= '{value2}'").first()
            if not node1 or not node2 and not relation_name:
                return JsonResponse({'status': 'error', 'message': 'company not existed'})
            elif node1 and node2:
                com1 = dict(node1)
                com2 = dict(node2)
                relation_data = QueryRelationship(com1['统一社会信用代码'], com2['统一社会信用代码'], relation_name)
                if not relation_data:
                    return JsonResponse({'status': 'error', 'message': 'no relationship exixt'})
                else:
                    return JsonResponse({'status': 'success', 'relationships': relation_data})
        elif relation_name:
            relation_data = QueryRelationship_withnonode(relation_name)
            return JsonResponse({'status': 'success', 'relationships': relation_data})
        else:
            return JsonResponse({'status': 'success', 'message': 'please try again'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def query_node_excel(request):
    if request.method == 'POST' and request.FILES:
        excel_file = request.FILES['file']
        try:
            # 读取 Excel 文件
            df = pd.read_excel(excel_file, keep_default_na=False)

            if df.columns[0] != "公司中文名称":
                return JsonResponse({'status': 'error', 'message': 'Invalid file format'}, status=400)

            # 添加新列 "公司是否在知识图谱中"
            df["公司是否在知识图谱中"] = [
                "是" if matcher.match("Company").where(f"_.公司中文名称= '{company}'").first() else "否"
                for company in df["公司中文名称"]
            ]

            # 将结果保存到 Excel 文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Company Status")
            output.seek(0)

            # 返回 Excel 文件到前端
            response = HttpResponse(
                output,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = 'attachment; filename="公司查询结果.xlsx"'
            response["status"] = "success"
            response["message"] = "查询成功"
            return response

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def compare_name(request):
    if request.method == 'POST' and request.FILES:
        excel_file = request.FILES['file']
        df = pd.read_excel(excel_file, sheet_name="Sheet1", keep_default_na=False)
        company1 = df.iloc[:, 0]
        company2 = df.iloc[:, 1]
        results = []
        for com1, com2 in zip(company1, company2):
            messages = [ChatMessage(
                role='user',
                content=f'{com1}和{com2}是否是同一家公司，请用一个字“是”或者”否“来回答'
            )]
            handler = ChunkPrintHandler()
            a = spark.generate([messages], callbacks=[handler])
            results.append(a.generations[0][0].text)
        if len(results) == len(df):
            df['对比结果'] = results
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)  # 重置指针到文件开始位置

        # 创建 HttpResponse，将 Excel 文件作为附件返回
        response = HttpResponse(
            excel_buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=对比结果.xlsx'
        response["status"] = "success"
        response["message"] = "查询成功"
        return response
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def test(request):
    if request.method == 'GET':
        progress = 50
        return JsonResponse({"progress": progress})

@require_GET
def getprogress(request):
    progress = cache.get('task_progress', 0)
    return JsonResponse({'progress': progress})

def fuzzymatch(request):
    if request.method == 'POST':
        name = json.loads(request.body)
        query = f'match (n:Company) where n.`公司中文名称` contains "{name}" or n.`曾用名` contains "{name}" return n'
        result = graph.run(query).data()
        rows = [item['n'] for item in result]
        df = pd.DataFrame(rows)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=companies.xlsx'

        # 创建一个 BytesIO 对象作为缓冲区
        output = BytesIO()

        # 使用 pandas 将 DataFrame 写入 Excel 格式
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Companies')

        # 移动指针到缓冲区的开始位置
        output.seek(0)

        # 创建 HttpResponse 对象，并设置为 Excel 文件
        response = HttpResponse(output.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=companies.xlsx'
        response['status'] = 'success'
        return response
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def generatequery(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        company_name = data.get('companyName')
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        start_date = start_date_obj.strftime("%Y-%m-%d")
        end_date = end_date_obj.strftime("%Y-%m-%d")
        date_name = data.get('date_name')
        step = data.get('step')
        tiaojian = "{`公司中文名称`:'" + company_name + "'}"
        query = f"MATCH path = (startNode {tiaojian} )-[rels*1..{step}]-(relatedNodes) WHERE ALL(r IN rels WHERE date(r.{date_name}) >= date('{start_date}') and date(r.date) <= date('{end_date}')) RETURN nodes(path), relationships(path)"
        result = graph.run(query).data()
        output = BytesIO()
        output.write(str(result).encode('utf-8'))  # 将结果写入字节流，注意这里用 str(result)
        # 将指针回到流的开始位置
        output.seek(0)
        # 使用 FileResponse 发送字节流数据
        response = FileResponse(output, as_attachment=True, filename='output.txt')
        return response
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


































