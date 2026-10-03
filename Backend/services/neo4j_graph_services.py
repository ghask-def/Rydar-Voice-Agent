# ### File: services/neo4j_graph.py
# from neo4j import GraphDatabase
# import os

# driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Extract relations from email, including dynamic semantic relations
def extract_neo4j_relations(session, user_id, user_email, relations):
    for rel in relations:
        rel_type = rel["type"].upper()
        target = rel["target"]

        # Clean up relation name if necessary
        if " " in rel_type:
            rel_type = rel_type.replace(" ", "_")

        session.run(
            f"""
            MERGE (u:Person {{email: $user_email, user_id: $user_id}})
            MERGE (e:Entity {{name: $target, user_id: $user_id}})
            MERGE (u)-[r:{rel_type}]->(e)
            """,
            user_email=user_email,
            user_id=user_id,
            target=target
        )
