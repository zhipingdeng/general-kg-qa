"""Import OwnThink KG triples into Neo4j with optional tag filtering."""
import asyncio
import csv
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.database.neo4j_client import Neo4jClient
from app.data.parser import OwnThinkParser
from app.data.importer import GraphImporter


OWNTHINK_PATH = "/mnt/e/hermes_code_workspace/dataset/通用百科数据集/OwnThink_KG/ownthink_v2.csv"


async def main():
    parser_args = argparse.ArgumentParser(description="Import OwnThink KG into Neo4j")
    parser_args.add_argument("--tags", type=str, default="",
                             help="Comma-separated tags to filter (e.g. '历史,历史事件,历史人物')")
    parser_args.add_argument("--limit", type=int, default=100000,
                             help="Max triples to import")
    parser_args.add_argument("--sample", type=int, default=0,
                             help="If >0, randomly sample this many entities and import ALL their triples")
    args = parser_args.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    settings = get_settings()
    client = Neo4jClient(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    await client.connect()

    csv_parser = OwnThinkParser()
    importer = GraphImporter(client)

    # Phase 1: If tags specified, first pass to find matching entity names
    matching_entities = set()
    if tags:
        print(f"Filtering by tags: {tags}")
        with open(OWNTHINK_PATH, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) < 3:
                    continue
                entity, attr, value = row[0].strip(), row[1].strip(), row[2].strip()
                if attr == "标签" and value in tags:
                    matching_entities.add(entity)

        print(f"Found {len(matching_entities)} entities matching tags")

        if not matching_entities:
            print("No matching entities found. Exiting.")
            await client.close()
            return

    # Phase 2: Parse all triples, filter by matching entities if tags specified
    triples = []
    with open(OWNTHINK_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 3:
                continue
            line = ",".join(row)
            t = csv_parser.parse_line(line)
            if not t:
                continue

            # Filter: only import triples for matching entities
            if tags and t.entity not in matching_entities:
                continue

            triples.append(t)
            if len(triples) >= args.limit:
                break

    print(f"Parsed {len(triples)} triples for {len(matching_entities) if tags else 'all'} entities")

    # Phase 3: Import
    imported = await importer.import_triples(triples, source="ownthink")
    print(f"Imported {imported} records.")

    result = await client.execute("MATCH (n:Entity {source: 'ownthink'}) RETURN count(n) AS cnt")
    print(f"Neo4j entity count: {result[0]['cnt']}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
