from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

env_path = 'knowledgegraph/neo4j_creds.env'
load_dotenv(dotenv_path=env_path)


# 1. Connect to your Neo4j instance.
neo4j_uri = os.getenv("NEO4J_URI")
# print(neo4j_uri)
neo4j_user = os.getenv("NEO4J_USERNAME")
# print(neo4j_user)
neo4j_password = os.getenv("NEO4J_PASSWORD")
# print(neo4j_password)

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def clear_graph():
    """Delete all nodes and relationships to avoid duplication errors."""
    clear_query = "MATCH (n) DETACH DELETE n"
    run_cypher_query(clear_query)

def create_sample_data():
    """Create sample nodes and relationships for a healthcare knowledge graph."""
    create_query = """
// Create Sectors
CREATE (automotive:Sector {name: 'Automotive'})
CREATE (mobile:Sector {name: 'Mobile Phones'})
CREATE (software:Sector {name: 'Software'})

// Create Companies in Automotive Sector with nationality as country
CREATE (ola:Company {name: 'Ola', nationality: 'India'})
CREATE (honda:Company {name: 'Honda', nationality: 'Japan'})
CREATE (tesla:Company {name: 'Tesla', nationality: 'USA'})
CREATE (bmw:Company {name: 'BMW', nationality: 'Germany'})
CREATE (automotive)-[:HAS_COMPANY]->(ola)
CREATE (automotive)-[:HAS_COMPANY]->(honda)
CREATE (automotive)-[:HAS_COMPANY]->(tesla)
CREATE (automotive)-[:HAS_COMPANY]->(bmw)

// Create Companies in Mobile Phones Sector with nationality as country
CREATE (nokia:Company {name: 'Nokia', nationality: 'Finland'})
CREATE (samsung:Company {name: 'Samsung', nationality: 'South Korea'})
CREATE (apple:Company {name: 'Apple', nationality: 'USA'})
CREATE (mobile)-[:HAS_COMPANY]->(nokia)
CREATE (mobile)-[:HAS_COMPANY]->(samsung)
CREATE (mobile)-[:HAS_COMPANY]->(apple)

// Create Companies in Software Sector with nationality as country
CREATE (microsoft:Company {name: 'Microsoft', nationality: 'USA'})
CREATE (ey:Company {name: 'EY', nationality: 'UK'})
CREATE (infosys:Company {name: 'Infosys', nationality: 'India'})
CREATE (software)-[:HAS_COMPANY]->(microsoft)
CREATE (software)-[:HAS_COMPANY]->(ey)
CREATE (software)-[:HAS_COMPANY]->(infosys)

// Create Raw Materials Entities
CREATE (lithium:RawMaterials {name: 'Lithium'})
CREATE (aluminum:RawMaterials {name: 'Aluminum'})
CREATE (copper:RawMaterials {name: 'Copper'})
CREATE (silicon:RawMaterials {name: 'Silicon/Chips'})

// Create Policy Entities
CREATE (trumpTariff:Policy {name: 'Trump Tariff'})
CREATE (steelTariff:Policy {name: 'Steel Tariff'})

// Create Regulation Entities
CREATE (pollutionNorms:Regulation {name: 'Pollution Norms'})
CREATE (safetyStandards:Regulation {name: 'Safety Standards for Vehicles'})

// Create Company Entities for Suppliers with nationality as country
CREATE (hindalco:Company {name: 'Hindalco', nationality: 'India'})
CREATE (albemarle:Company {name: 'Albemarle', nationality: 'USA'})
CREATE (freeportMcMoRan:Company {name: 'Freeport-McMoRan', nationality: 'USA'})
CREATE (intel:Company {name: 'Intel', nationality: 'USA'})
CREATE (rioTinto:Company {name: 'Rio Tinto', nationality: 'Australia'})


// Create Agency Entities
CREATE (departmentOfCommerce:Agency {name: 'Department of Commerce'})
CREATE (epa:Agency {name: 'Environmental Protection Agency (EPA)'})
CREATE (nhtsa:Agency {name: 'National Highway Traffic Safety Administration (NHTSA)'})

// Create Country Entities
CREATE (usa:Country {name: 'USA'})
CREATE (australia:Country {name: 'Australia'})
CREATE (canada:Country {name: 'Canada'})
CREATE (china:Country {name: 'China'})
CREATE (chile:Country {name: 'Chile'})
CREATE (ukraine:Country {name: 'Ukraine'})
CREATE (taiwan:Country {name: 'Taiwan'})
CREATE (japan:Country {name: 'Japan'})

// Create Mines
CREATE (lithiumMine:Mine {name: 'Lithium Mine'})
CREATE (aluminumMine:Mine {name: 'Aluminum Mine'})
CREATE (copperMine:Mine {name: 'Copper Mine'})
CREATE (siliconMine:Mine {name: 'Silicon Mine'})

// Create Relationships for Automotive Sector
CREATE (ola)-[:IMPACTED_BY]->(aluminum)
CREATE (ola)-[:IMPACTED_BY]->(lithium)
CREATE (ola)-[:IMPACTED_BY]->(trumpTariff)
CREATE (ola)-[:IMPACTED_BY]->(pollutionNorms)
CREATE (ola)-[:IMPACTED_BY]->(safetyStandards)

CREATE (honda)-[:IMPACTED_BY]->(aluminum)
CREATE (honda)-[:IMPACTED_BY]->(trumpTariff)
CREATE (honda)-[:IMPACTED_BY]->(pollutionNorms)
CREATE (honda)-[:IMPACTED_BY]->(safetyStandards)

CREATE (tesla)-[:IMPACTED_BY]->(silicon)
CREATE (tesla)-[:IMPACTED_BY]->(aluminum)
CREATE (tesla)-[:IMPACTED_BY]->(steelTariff)
CREATE (tesla)-[:IMPACTED_BY]->(pollutionNorms)
CREATE (tesla)-[:IMPACTED_BY]->(safetyStandards)

CREATE (bmw)-[:IMPACTED_BY]->(aluminum)
CREATE (bmw)-[:IMPACTED_BY]->(trumpTariff)
CREATE (bmw)-[:IMPACTED_BY]->(pollutionNorms)
CREATE (bmw)-[:IMPACTED_BY]->(safetyStandards)

// Create Relationships for Mobile Phones Sector
CREATE (nokia)-[:IMPACTED_BY]->(lithium)
CREATE (nokia)-[:IMPACTED_BY]->(aluminum)
CREATE (nokia)-[:IMPACTED_BY]->(trumpTariff)
CREATE (nokia)-[:IMPACTED_BY]->(pollutionNorms)

CREATE (samsung)-[:IMPACTED_BY]->(copper)
CREATE (samsung)-[:IMPACTED_BY]->(lithium)
CREATE (samsung)-[:IMPACTED_BY]->(aluminum)
CREATE (samsung)-[:IMPACTED_BY]->(silicon)
CREATE (samsung)-[:IMPACTED_BY]->(trumpTariff)
CREATE (samsung)-[:IMPACTED_BY]->(pollutionNorms)

CREATE (apple)-[:IMPACTED_BY]->(copper)
CREATE (apple)-[:IMPACTED_BY]->(lithium)
CREATE (apple)-[:IMPACTED_BY]->(aluminum)
CREATE (apple)-[:IMPACTED_BY]->(silicon)
CREATE (apple)-[:IMPACTED_BY]->(pollutionNorms)
CREATE (apple)-[:IMPACTED_BY]->(steelTariff)

// Create Relationships for Software Sector
CREATE (microsoft)-[:IMPACTED_BY]->(silicon)
CREATE (microsoft)-[:IMPACTED_BY]->(copper)

CREATE (ey)-[:IMPACTED_BY]->(silicon)

CREATE (infosys)-[:IMPACTED_BY]->(silicon)
CREATE (infosys)-[:IMPACTED_BY]->(copper)

// Make Relationship Supplies
CREATE (hindalco)-[:SUPPLIES]->(aluminum)
CREATE (albemarle)-[:SUPPLIES]->(lithium)
CREATE (freeportMcMoRan)-[:SUPPLIES]->(copper)
CREATE (intel)-[:SUPPLIES]->(silicon)
CREATE (rioTinto)-[:SUPPLIES]->(aluminum)
CREATE (rioTinto)-[:SUPPLIES]->(lithium)

// Link Agencies to Policies
CREATE (departmentOfCommerce)-[:ENFORCES]->(trumpTariff)
CREATE (departmentOfCommerce)-[:ENFORCES]->(steelTariff)
CREATE (epa)-[:ENFORCES]->(pollutionNorms) // EPA enforces pollution norms
CREATE (nhtsa)-[:ENFORCES]->(safetyStandards) // NHTSA enforces safety standards


// Create Relationships for Companies sourcing from Countries
CREATE (hindalco)-[:SOURCES_FROM]->(usa)
CREATE (hindalco)-[:SOURCES_FROM]->(canada)
CREATE (hindalco)-[:SOURCES_FROM]->(australia)

CREATE (albemarle)-[:SOURCES_FROM]->(australia)
CREATE (albemarle)-[:SOURCES_FROM]->(chile)

CREATE (freeportMcMoRan)-[:SOURCES_FROM]->(usa)
CREATE (freeportMcMoRan)-[:SOURCES_FROM]->(chile)

CREATE (rioTinto)-[:SOURCES_FROM]->(usa)
CREATE (rioTinto)-[:SOURCES_FROM]->(australia)

CREATE (intel)-[:SOURCES_FROM]->(usa)
CREATE (intel)-[:SOURCES_FROM]->(taiwan)

// Create Relationships for Countries possessing Mines
CREATE (usa)-[:POSSESSED_BY]->(aluminumMine)
CREATE (canada)-[:POSSESSED_BY]->(aluminumMine)
CREATE (australia)-[:POSSESSED_BY]->(aluminumMine)

CREATE (australia)-[:POSSESSED_BY]->(lithiumMine)
CREATE (chile)-[:POSSESSED_BY]->(lithiumMine)
CREATE (usa)-[:POSSESSED_BY]->(lithiumMine)

CREATE (canada)-[:POSSESSED_BY]->(copperMine)
CREATE (usa)-[:POSSESSED_BY]->(copperMine)
CREATE (chile)-[:POSSESSED_BY]->(copperMine)

// Create Relationships for Countries possessing Silicon Mine
CREATE (usa)-[:POSSESSED_BY]->(siliconMine)
CREATE (china)-[:POSSESSED_BY]->(siliconMine)
CREATE (taiwan)-[:POSSESSED_BY]->(siliconMine)
CREATE (japan)-[:POSSESSED_BY]->(siliconMine)  
"""
    run_cypher_query(create_query)

def run_cypher_query(query: str):
    """Execute a Cypher query and return the results."""
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

# 3. Main execution: Clear graph, create sample data, then generate and execute the query.
if __name__ == "__main__":
    try:
        clear_graph()
        create_sample_data()
        
        # cypher_query = "MATCH (p:Patient {name: 'John Doe'}) RETURN p"
        # print("Cypher Query:")
        # print(cypher_query, "\n")
    #     query = """
    # CREATE (companyA:Company {name: 'Company A', industry: 'Pharmaceuticals'})
    # CREATE (companyB:Company {name: 'Company B', industry: 'Pharmaceuticals'})
    # """
        # results = run_cypher_query(query)
    #     for query in queries:
    #         results = run_cypher_query(query)
    #         print("Query Results:")
    #         print(results)
    except Exception as e:
        print("An error occurred:", e)