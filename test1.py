# from py2neo import Graph, NodeMatcher, Node, Relationship, RelationshipMatcher
#
# # graph = Graph("neo4j://10.176.22.62:7687", auth=("neo4j", "neo4j6008"))
# # matcher = NodeMatcher(graph)
#
# graph = Graph("neo4j://localhost:7687", auth=("neo4j", "1598273166wsy."))
# matcher = NodeMatcher(graph)
# rmatcher = RelationshipMatcher(graph)
#
# com1 = "aaa"
# com2 = 'bbb'
# type = 'test'
#
# node1 = matcher.match("Company").where(f"_.公司名称= '{ com1 }'").first()
# node2 = matcher.match("Company").where(f"_.公司名称= '{ com2 }'").first()
#
# query = f"MATCH (c1:Company)-[r:{type}]->(c2:Company) WHERE c1.`公司名称` = '{com1}' AND c2.`公司名称` = '{com2}' RETURN type(r) as relationship_type, r"
# result = graph.run(query)
#
# relationships = []
# for record in result:
#         relationship_type = record["relationship_type"]
#         relationship_properties = dict(record["r"])  # 将关系属性转换为字典
#         relationships.append({
#                 "type": relationship_type,
#                 "properties": relationship_properties
#         })
# print(relationships)

from py2neo import Graph, NodeMatcher, Node, Relationship, RelationshipMatcher
import io
import pandas as pd


graph = Graph("neo4j://localhost:7687", auth=("neo4j", "1598273166wsy."))
# file1_path = r"E:\work\finance_risk\test_add_node.xlsx"
# df = pd.read_excel(file1_path)
matcher = NodeMatcher(graph)

# df_unique = df.drop_duplicates()
# existing_nodes = []
# for index, row in df_unique.iterrows():
#         company_name = row['公司名称']
#         node = matcher.match("Company").where(f"_.公司名称='{company_name}'").first()
#
#         if not node:
#                 company_node = Node("Company", name=company_name, **row.to_dict())
#                 graph.create(company_node)
#         else:
#                 existing_nodes.append(row)
#         if existing_nodes:
#                 print("断点4")
#                 existing_df = pd.DataFrame(existing_nodes)
#                 output = io.BytesIO()
#                 print("断点6")
#                 print(type(existing_df))
#                 with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#                         existing_df.to_excel(writer, index=False, sheet_name='Sheet1')
#                 print("断点7")
#                 output.seek(0)
#                 print("断点1")

def QueryRelationship(node1, node2, relationship):
    query = ''
    if relationship:
        query = f"MATCH (c1:Company)-[r:{relationship}]->(c2:Company) WHERE c1.`公司名称` = '{node1}' AND c2.`公司名称` = '{node2}' RETURN type(r) as relationship_type, r"
    else:
        query = f"MATCH (c1:Company)-[r]->(c2:Company) WHERE c1.`公司名称` = '{node1}' AND c2.`公司名称` = '{node2}' RETURN type(r) as relationship_type, r"
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
            print(relationships)
            return True
    else:
            return False


com1 = "aaa"
com2 = 'ccc'
type = 'test'


print(QueryRelationship(com1, com2, 'test'))












